"""Unit tests for cleaning, normalization, duplicate handling and infinity sanitation."""

import pytest
import numpy as np
import pandas as pd
from neuralshield.data.cleaning import (
    normalize_column_names,
    identify_and_drop_redundant_columns,
    sanitize_infinite_and_nan,
    handle_duplicates,
    normalize_labels,
)


def test_normalize_column_names(dirty_synthetic_df):
    """Verifies column headers are stripped of whitespace and converted to snake_case."""
    df_clean, mapping = normalize_column_names(dirty_synthetic_df)
    assert "destination_port" in df_clean.columns
    assert "flow_duration" in df_clean.columns
    assert "flow_bytes_per_sec" in df_clean.columns
    assert "label" in df_clean.columns
    assert not any(c.startswith(" ") or c.endswith(" ") for c in df_clean.columns)


def test_identify_and_drop_redundant_columns(dirty_synthetic_df):
    """Verifies that duplicate redundant columns like Fwd Header Length.1 are dropped."""
    df_clean, dropped = identify_and_drop_redundant_columns(dirty_synthetic_df, verify_equality=True)
    assert "Fwd Header Length.1" in dropped
    assert "Fwd Header Length.1" not in df_clean.columns
    assert "Fwd Header Length" in df_clean.columns


def test_sanitize_infinite_and_nan(dirty_synthetic_df):
    """Verifies infinite values are identified and replaced with NaN or median."""
    df_clean, stats = sanitize_infinite_and_nan(dirty_synthetic_df, replace_strategy="nan")
    assert stats["pos_inf_count"] >= 1
    assert stats["neg_inf_count"] >= 1
    # Check that no infs remain in the dataframe
    num_vals = df_clean.select_dtypes(include=[np.number]).to_numpy()
    assert not np.isinf(num_vals).any()


def test_handle_duplicates(dirty_synthetic_df):
    """Verifies exact duplicate rows are identified and removed."""
    initial_len = len(dirty_synthetic_df)
    df_dedup, removed = handle_duplicates(dirty_synthetic_df)
    assert removed == 2  # Rows index 0, 2, 3 are identical in the fixture
    assert len(df_dedup) == initial_len - removed


def test_normalize_labels(dirty_synthetic_df):
    """Verifies target labels are mapped according to attack taxonomy."""
    df_clean, mapping = normalize_column_names(dirty_synthetic_df)
    df_norm, audit = normalize_labels(df_clean, target_col="label")
    
    assert audit["unique_normalized_labels"] >= 2
    # "BENIGN" should be mapped to "Benign"
    assert "Benign" in df_norm["label"].values
    # "DoS Hulk" should be mapped to "DoS - Hulk"
    assert "DoS - Hulk" in df_norm["label"].values
