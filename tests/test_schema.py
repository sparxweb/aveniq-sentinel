"""Unit tests for schema inspection and cross-file consistency comparison."""

import pytest
import pandas as pd
from pathlib import Path
from neuralshield.data.schema import inspect_csv_schema, compare_schemas


def test_inspect_csv_schema(tmp_path: Path):
    """Verifies schema inspection correctly extracts columns and types."""
    f = tmp_path / "test_flow.csv"
    f.write_text(" Destination Port , Flow Duration,Label\n80,1000.0,BENIGN\n")
    
    sch = inspect_csv_schema(f)
    assert sch["raw_column_count"] == 3
    assert "destination_port" in sch["normalized_columns"]
    assert "flow_duration" in sch["normalized_columns"]
    assert "label" in sch["normalized_columns"]


def test_compare_schemas_consistent(tmp_path: Path):
    """Verifies 100% consistency when files share identical schemas."""
    f1 = tmp_path / "file1.csv"
    f2 = tmp_path / "file2.csv"
    f1.write_text("port,duration,label\n80,100,BENIGN\n")
    f2.write_text("port,duration,label\n443,200,DDoS\n")
    
    comp = compare_schemas([f1, f2])
    assert comp["total_files_compared"] == 2
    assert comp["consistency_score"] == 100.0
    assert len(comp["discrepancies"]) == 0
    assert set(comp["universal_columns"]) == {"port", "duration", "label"}


def test_compare_schemas_drift(tmp_path: Path):
    """Verifies discrepancy detection when files have divergent schemas."""
    f1 = tmp_path / "file1.csv"
    f2 = tmp_path / "file2.csv"
    f1.write_text("port,duration,label\n80,100,BENIGN\n")
    f2.write_text("port,duration,extra_col,label\n443,200,1,DDoS\n")
    
    comp = compare_schemas([f1, f2])
    assert comp["consistency_score"] < 100.0
    assert len(comp["discrepancies"]) >= 1
    assert comp["universal_columns_count"] == 3
