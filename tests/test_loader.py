"""Unit tests for dataset loading, CSV discovery, downcasting and sampling."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from neuralshield.data.discovery import discover_csv_files, inspect_dataset_inventory
from neuralshield.data.loader import DatasetLoader, downcast_numeric_dtypes, sample_dataframe
from neuralshield.utils.file_utils import safe_read_csv, get_file_size_mb
from neuralshield.utils.validators import validate_dataframe_not_empty, ValidationError


def test_discover_csv_files(tmp_path: Path):
    """Verifies that discover_csv_files correctly discovers all CSV files."""
    file1 = tmp_path / "test1.csv"
    file2 = tmp_path / "test2.csv"
    file1.write_text("a,b\n1,2")
    file2.write_text("x,y\n3,4")
    
    discovered = discover_csv_files(tmp_path)
    assert len(discovered) == 2
    assert file1 in discovered
    assert file2 in discovered


def test_discover_empty_directory(tmp_path: Path):
    """Verifies behavior on an empty directory."""
    discovered = discover_csv_files(tmp_path)
    assert discovered == []


def test_inspect_dataset_inventory_incomplete(tmp_path: Path):
    """Verifies that inventory flags missing official benchmark files."""
    file1 = tmp_path / "Monday-WorkingHours.pcap_ISCX.csv"
    file1.write_text("Destination Port,Label\n80,BENIGN")
    
    inv = inspect_dataset_inventory(tmp_path)
    assert inv["total_files_found"] == 1
    assert inv["expected_present_count"] == 1
    assert inv["is_complete_benchmark"] is False


def test_dataset_loader_single_file(tmp_path: Path):
    """Verifies DatasetLoader loads a CSV properly."""
    f = tmp_path / "sample.csv"
    f.write_text("col_a,col_b\n10,20\n30,40")
    
    loader = DatasetLoader()
    df = loader.load_single_file(f)
    assert len(df) == 2
    assert list(df.columns) == ["col_a", "col_b"]


def test_dataset_loader_selective_columns(tmp_path: Path):
    """Verifies selective column loading with usecols."""
    f = tmp_path / "sample.csv"
    f.write_text("col_a,col_b,col_c\n1,2,3\n4,5,6")
    
    loader = DatasetLoader()
    df = loader.load_single_file(f, usecols=["col_a", "col_c"])
    assert list(df.columns) == ["col_a", "col_c"]


def test_dataset_loader_invalid_file():
    """Verifies that loading a non-existent file raises FileNotFoundError."""
    loader = DatasetLoader()
    with pytest.raises(FileNotFoundError):
        loader.load_single_file("non_existent_file.csv")


def test_validate_dataframe_not_empty_raises(empty_df):
    """Verifies ValidationError is raised when dataframe is empty."""
    with pytest.raises(ValidationError):
        validate_dataframe_not_empty(empty_df)


def test_downcast_numeric_dtypes():
    """Verifies numeric downcasting reduces memory without data loss."""
    df = pd.DataFrame({
        "flt_col": np.array([1.5, 2.5, 3.5], dtype=np.float64),
        "int_col": np.array([10, 20, 30], dtype=np.int64),
    })
    df_opt, metrics = downcast_numeric_dtypes(df)
    assert df_opt["flt_col"].dtype == np.float32
    assert df_opt["int_col"].dtype in [np.int8, np.int16, np.int32]
    assert metrics["reduction_percentage"] > 0


def test_sample_dataframe():
    """Verifies deterministic random sampling and stratified sampling."""
    df = pd.DataFrame({
        "feature": range(100),
        "label": ["A"] * 80 + ["B"] * 20,
    })
    # Fixed count sample
    sample_50 = sample_dataframe(df, n=50, random_state=42)
    assert len(sample_50) == 50

    # Stratified sample
    strat_sample = sample_dataframe(df, n=20, random_state=42, stratify_col="label")
    assert len(strat_sample) > 0
