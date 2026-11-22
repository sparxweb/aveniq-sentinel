"""Unit tests for pipeline edge cases, data sanitization anomalies, and leakage guards."""

import pytest
import pandas as pd
import numpy as np
from neuralshield.data.preprocessing import PreprocessingPipeline
from neuralshield.data.loader import downcast_numeric_dtypes, DatasetLoader
from neuralshield.utils.validators import ValidationError
from config.settings import TARGET_LEAKAGE_COLUMNS


def test_pipeline_empty_dataframe_raises():
    """Verifies that an empty DataFrame raises ValidationError rather than unhandled exception."""
    pipeline = PreprocessingPipeline()
    empty_df = pd.DataFrame()
    with pytest.raises(ValidationError):
        pipeline.fit_transform(empty_df, dataset_name="EmptyTest")


def test_pipeline_preserves_clean_features(clean_synthetic_df):
    """Verifies that running pipeline on already-clean data preserves validity."""
    pipeline = PreprocessingPipeline()
    result = pipeline.fit_transform(clean_synthetic_df, dataset_name="CleanTest")
    cleaned = result["cleaned_df"]
    assert len(cleaned) == len(clean_synthetic_df)
    assert result["audit_report"]["quality_audit"]["quality_score"] >= 95.0


def test_pipeline_strips_target_leakage_identifiers():
    """Verifies that sensitive network identifiers are removed from the pipeline output."""
    df_with_leakage = pd.DataFrame({
        "Flow ID": ["192.168.1.1-8.8.8.8-53-1234-17"],
        "Source IP": ["192.168.1.1"],
        "Destination IP": ["8.8.8.8"],
        "Timestamp": ["04/07/2017 08:50:00"],
        "flow_duration": [1200.0],
        "total_fwd_packets": [10],
        "label": ["Benign"],
    })
    pipeline = PreprocessingPipeline()
    res = pipeline.fit_transform(df_with_leakage, dataset_name="LeakageTest")
    cleaned = res["cleaned_df"]

    for col in TARGET_LEAKAGE_COLUMNS:
        assert col not in cleaned.columns, f"Leaked column {col} was found in cleaned dataset!"


def test_downcast_numeric_dtypes_lossless():
    """Verifies that numeric downcasting preserves precision within acceptable bounds."""
    original_df = pd.DataFrame({
        "integer_vals": [10, 100, 1000, 50000],
        "float_vals": [1.5, 2.75, 100.125, 9999.0625],
    })
    downcasted_df, stats = downcast_numeric_dtypes(original_df)

    # Dtypes are reduced
    assert downcasted_df["integer_vals"].dtype in [np.int16, np.int32]
    assert downcasted_df["float_vals"].dtype == np.float32

    # Numerical values match exactly
    np.testing.assert_array_equal(original_df["integer_vals"].values, downcasted_df["integer_vals"].values)
    np.testing.assert_allclose(original_df["float_vals"].values, downcasted_df["float_vals"].values, rtol=1e-5)
    assert stats["reduction_percentage"] > 0.0


def test_dataset_loader_missing_file_raises():
    """Verifies that DatasetLoader raises FileNotFoundError on missing files."""
    loader = DatasetLoader()
    with pytest.raises(FileNotFoundError):
        loader.load_single_file("non_existent_capture_file.csv")
