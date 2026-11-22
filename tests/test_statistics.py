"""Unit tests for statistical summaries, distributions, and correlations."""

import pytest
import pandas as pd
import numpy as np
from neuralshield.analysis.statistics import (
    compute_descriptive_statistics,
    identify_constant_features,
)
from neuralshield.analysis.distributions import analyze_class_balance
from neuralshield.analysis.correlations import (
    compute_correlation_matrix,
    find_high_correlation_pairs,
)


def test_compute_descriptive_statistics(clean_synthetic_df):
    """Verifies descriptive stats table includes variance, skewness, and zero-variance flag."""
    desc = compute_descriptive_statistics(clean_synthetic_df)
    assert not desc.empty
    assert "mean" in desc.columns
    assert "variance" in desc.columns
    assert "skewness" in desc.columns
    assert "zero_variance" in desc.columns


def test_identify_constant_features():
    """Verifies that features with zero variance are identified."""
    df = pd.DataFrame({
        "var_col": [1, 2, 3, 4],
        "const_col": [5, 5, 5, 5],
    })
    consts = identify_constant_features(df)
    assert "const_col" in consts
    assert "var_col" not in consts


def test_analyze_class_balance(clean_synthetic_df):
    """Verifies class imbalance analysis correctly flags distribution and ratios."""
    balance = analyze_class_balance(clean_synthetic_df, target_col="Label")
    assert "class_counts" in balance
    assert balance["majority_class"] == "BENIGN"
    assert "imbalance_ratio" in balance


def test_correlation_and_collinearity():
    """Verifies correlation matrix calculation and high correlation pair discovery."""
    df = pd.DataFrame({
        "feat_a": [1.0, 2.0, 3.0, 4.0, 5.0],
        "feat_b": [2.0, 4.0, 6.0, 8.0, 10.0],  # Perfectly correlated with feat_a
        "feat_c": [5.0, 1.0, 4.0, 2.0, 3.0],
    })
    corr = compute_correlation_matrix(df)
    assert corr.shape == (3, 3)
    
    pairs = find_high_correlation_pairs(corr, threshold=0.95)
    assert len(pairs) >= 1
    assert pairs[0]["feature_1"] in ["feat_a", "feat_b"]
    assert pairs[0]["feature_2"] in ["feat_a", "feat_b"]
    assert pairs[0]["abs_correlation"] >= 0.99
