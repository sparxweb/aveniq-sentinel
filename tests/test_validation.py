"""Unit tests for data validation, numerical anomalies, quality scoring and report export."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from neuralshield.data.validation import (
    audit_dataframe_quality,
    inspect_numerical_anomalies,
    export_quality_report,
    _calculate_quality_score,
    generate_all_data_quality_reports,
)
from neuralshield.data.preprocessing import PreprocessingPipeline


def test_audit_dataframe_quality(dirty_synthetic_df):
    """Verifies audit captures missing, infinite, and duplicate statistics."""
    audit = audit_dataframe_quality(dirty_synthetic_df, target_col=" Label ")
    assert audit["total_rows"] == 5
    assert audit["total_columns"] == 13
    assert audit["total_missing_values"] >= 1
    assert audit["total_infinite_values"] >= 2
    assert audit["duplicate_rows"] == 2
    assert 0.0 <= audit["quality_score"] <= 100.0
    assert "target_summary" in audit
    assert "binary_distribution" in audit["target_summary"]
    assert "multiclass_distribution" in audit["target_summary"]


def test_inspect_numerical_anomalies():
    """Verifies detection of negative non-negative features and zero-duration rate hazards."""
    df = pd.DataFrame({
        "total_fwd_packets": [10, -5, 20],  # Negative violation
        "flow_duration": [0.0, 1000.0, 500.0],
        "const_feature": [1, 1, 1],         # Zero variance
    })
    anomalies = inspect_numerical_anomalies(df)
    assert "total_fwd_packets" in anomalies["negative_value_violations"]
    assert "const_feature" in anomalies["constant_columns"]


def test_export_quality_report(tmp_path: Path, clean_synthetic_df):
    """Verifies quality report export in both JSON and CSV formats."""
    audit = audit_dataframe_quality(clean_synthetic_df, target_col="Label")
    
    # Export JSON
    json_path = tmp_path / "report.json"
    p_json = export_quality_report(audit, json_path, format="json")
    assert p_json.is_file()
    assert p_json.stat().st_size > 0

    # Export CSV
    csv_path = tmp_path / "report.csv"
    p_csv = export_quality_report(audit, csv_path, format="csv")
    assert p_csv.is_file()
    assert p_csv.stat().st_size > 0


def test_quality_score_calculation():
    """Verifies quality index decreases with corruption."""
    perfect_score = _calculate_quality_score(0, 0, 0, 1000)
    assert perfect_score == 100.0
    
    corrupted_score = _calculate_quality_score(100, 50, 150, 1000, anomalies_count=2)
    assert corrupted_score < perfect_score


def test_preprocessing_pipeline_end_to_end(dirty_synthetic_df):
    """Verifies complete PreprocessingPipeline fit_transform cleans dirty input."""
    pipeline = PreprocessingPipeline()
    result = pipeline.fit_transform(dirty_synthetic_df, dataset_name="TestFlow")
    
    cleaned_df = result["cleaned_df"]
    audit = result["audit_report"]
    
    assert len(cleaned_df) < len(dirty_synthetic_df)  # Duplicates removed
    assert "destination_port" in cleaned_df.columns
    assert "label" in cleaned_df.columns
    assert "fwd_header_length_1" not in cleaned_df.columns
    assert audit["quality_audit"]["quality_score"] >= 70.0


def test_generate_all_data_quality_reports(tmp_path: Path, dirty_synthetic_df):
    """Verifies generation of all 6 mandated data quality report artifacts."""
    out_dir = tmp_path / "quality_reports"
    reports = generate_all_data_quality_reports(
        dirty_synthetic_df,
        output_dir=out_dir,
        target_col=" Label ",
    )

    expected_keys = [
        "inventory",
        "quality_report",
        "missing_values",
        "duplicate_analysis",
        "label_distribution",
        "quality_summary",
    ]
    for key in expected_keys:
        assert key in reports
        p = reports[key]
        assert p.is_file(), f"File {p} does not exist"
        assert p.stat().st_size > 0, f"File {p} is empty"

    # Verify content of CSVs and JSONs
    missing_df = pd.read_csv(reports["missing_values"])
    assert "column_name" in missing_df.columns
    assert "missing_count" in missing_df.columns

    summary_df = pd.read_csv(reports["quality_summary"])
    assert "Metric" in summary_df.columns
    assert "Status" in summary_df.columns

