"""Unit tests for benign vs attack behavioral comparisons."""

import pytest
import pandas as pd
import numpy as np
from neuralshield.analysis.comparisons import compare_benign_vs_attack


def test_compare_benign_vs_attack(clean_synthetic_df):
    """Verifies statistical comparisons between benign and attack flows."""
    comp = compare_benign_vs_attack(clean_synthetic_df, target_col="Label")
    assert "error" not in comp
    assert comp["benign_sample_count"] == 3
    assert comp["attack_sample_count"] == 2
    assert "feature_comparisons" in comp
    assert "tcp_flag_comparisons" in comp


def test_compare_benign_vs_attack_single_class():
    """Verifies graceful handling when dataset has only a single class."""
    df_single = pd.DataFrame({
        "Flow Duration": [100.0, 200.0],
        "Label": ["BENIGN", "BENIGN"],
    })
    comp = compare_benign_vs_attack(df_single, target_col="Label")
    assert "warning" in comp


def test_compare_benign_vs_attack_missing_label():
    """Verifies error reporting when target column does not exist."""
    df = pd.DataFrame({"Flow Duration": [100.0, 200.0]})
    comp = compare_benign_vs_attack(df, target_col="Target")
    assert "error" in comp
