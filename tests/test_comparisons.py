"""Unit and regression tests for benign vs attack behavioral comparisons."""

import pytest
import pandas as pd
import numpy as np
from neuralshield.analysis.comparisons import compare_benign_vs_attack


def test_compare_benign_vs_attack(clean_synthetic_df):
    """Verifies statistical comparisons between benign and attack flows using target_col."""
    comp = compare_benign_vs_attack(clean_synthetic_df, target_col="Label")
    assert "error" not in comp
    assert comp["benign_sample_count"] == 3
    assert comp["attack_sample_count"] == 2
    assert "feature_comparisons" in comp
    assert "tcp_flag_comparisons" in comp
    # Verify both ratio keys exist for contract compatibility
    for feat, stats in comp["feature_comparisons"].items():
        assert "attack_to_benign_median_ratio" in stats
        assert "divergence_ratio" in stats
        assert stats["attack_to_benign_median_ratio"] == stats["divergence_ratio"]


def test_compare_benign_vs_attack_label_col_kwarg(clean_synthetic_df):
    """Regression test: verifies calling with label_col kwarg succeeds without error."""
    comp = compare_benign_vs_attack(clean_synthetic_df, label_col="Label")
    assert "error" not in comp
    assert comp["benign_sample_count"] == 3
    assert comp["attack_sample_count"] == 2
    assert len(comp["feature_comparisons"]) > 0


def test_compare_benign_vs_attack_empty_dataframe():
    """Verifies graceful handling when an empty DataFrame is passed."""
    comp = compare_benign_vs_attack(pd.DataFrame(), target_col="Label")
    assert "error" in comp
    assert comp["benign_sample_count"] == 0
    assert comp["attack_sample_count"] == 0
    assert comp["feature_comparisons"] == {}


def test_compare_benign_vs_attack_none_dataframe():
    """Verifies graceful handling when None is passed."""
    comp = compare_benign_vs_attack(None, target_col="Label")
    assert "error" in comp
    assert comp["benign_sample_count"] == 0


def test_compare_benign_vs_attack_single_class_benign():
    """Verifies warning when dataset contains only benign traffic."""
    df_single = pd.DataFrame({
        "Flow Duration": [100.0, 200.0, 300.0],
        "Label": ["BENIGN", "BENIGN", "BENIGN"],
    })
    comp = compare_benign_vs_attack(df_single, target_col="Label")
    assert "warning" in comp
    assert comp["benign_sample_count"] == 3
    assert comp["attack_sample_count"] == 0


def test_compare_benign_vs_attack_single_class_attack():
    """Verifies warning when dataset contains only attack traffic."""
    df_single = pd.DataFrame({
        "Flow Duration": [100.0, 200.0, 300.0],
        "Label": ["DDoS", "PortScan", "Bot"],
    })
    comp = compare_benign_vs_attack(df_single, target_col="Label")
    assert "warning" in comp
    assert comp["benign_sample_count"] == 0
    assert comp["attack_sample_count"] == 3


def test_compare_benign_vs_attack_missing_label():
    """Verifies error reporting when target column does not exist."""
    df = pd.DataFrame({"Flow Duration": [100.0, 200.0]})
    comp = compare_benign_vs_attack(df, target_col="NonExistentColumn")
    assert "error" in comp


def test_compare_benign_vs_attack_null_labels():
    """Verifies that null target labels are filtered out without crashing."""
    df = pd.DataFrame({
        "Flow Duration": [100.0, 200.0, 300.0, 400.0],
        "Label": ["BENIGN", None, "DDoS", np.nan],
    })
    comp = compare_benign_vs_attack(df, target_col="Label")
    assert "error" not in comp
    assert comp["benign_sample_count"] == 1
    assert comp["attack_sample_count"] == 1


def test_compare_benign_vs_attack_all_null_labels():
    """Verifies error reporting when target column contains only null values."""
    df = pd.DataFrame({
        "Flow Duration": [100.0, 200.0],
        "Label": [None, np.nan],
    })
    comp = compare_benign_vs_attack(df, target_col="Label")
    assert "error" in comp


def test_compare_benign_vs_attack_constant_and_zero_median():
    """Verifies division-by-zero protection when benign median is zero."""
    df = pd.DataFrame({
        "Flow Duration": [0.0, 0.0, 500.0, 600.0],
        "Label": ["BENIGN", "BENIGN", "DDoS", "DDoS"],
    })
    comp = compare_benign_vs_attack(df, target_col="Label")
    assert "error" not in comp
    stats = comp["feature_comparisons"].get("Flow Duration")
    assert stats is not None
    assert stats["benign_median"] == 0.0
    assert stats["attack_median"] == 550.0
    assert stats["divergence_ratio"] == 100.0


def test_compare_benign_vs_attack_infinite_values():
    """Verifies that infinite values in feature columns are sanitized during comparison."""
    df = pd.DataFrame({
        "Flow Duration": [np.inf, 100.0, -np.inf, 400.0],
        "Label": ["BENIGN", "BENIGN", "DDoS", "DDoS"],
    })
    comp = compare_benign_vs_attack(df, target_col="Label")
    assert "error" not in comp
    stats = comp["feature_comparisons"].get("Flow Duration")
    assert stats is not None
    assert np.isfinite(stats["benign_median"])
    assert np.isfinite(stats["attack_median"])
