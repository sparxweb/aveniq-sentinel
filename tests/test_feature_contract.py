"""Unit tests for ML Feature Contract and Leakage Prevention (Phase 3.1)."""

import pytest
import pandas as pd
import numpy as np

from neuralshield.ml.feature_contract import FeatureContract, CORE_ML_FEATURES


@pytest.fixture
def sample_feature_df():
    return pd.DataFrame({
        "Flow Duration": [1000.0, 2000.0, 3000.0],
        "Total Fwd Packets": [10.0, 20.0, 15.0],
        "Total Backward Packets": [5.0, 10.0, 8.0],
        "Flow Bytes/s": [500.0, 1000.0, 750.0],
        "Flow Packets/s": [15.0, 30.0, 23.0],
        "SYN Flag Count": [1, 0, 1],
        "ACK Flag Count": [0, 1, 0],
        "Label": ["BENIGN", "BENIGN", "DDoS"],
    })


def test_feature_contract_validation_clean(sample_feature_df):
    contract = FeatureContract()
    audit = contract.validate_dataframe(sample_feature_df)

    assert audit["has_leakage_hazard"] is False
    assert audit["detected_leakage_columns"] == []
    assert audit["is_valid_for_training"] is True
    assert audit["available_permitted_count"] > 0


def test_feature_contract_detects_leakage(sample_feature_df):
    contract = FeatureContract()
    dirty_df = sample_feature_df.copy()
    dirty_df["Source IP"] = ["192.168.1.1", "192.168.1.2", "10.0.0.1"]
    dirty_df["Timestamp"] = ["03/07/2017 09:00", "03/07/2017 09:01", "03/07/2017 09:02"]
    dirty_df["Flow ID"] = ["192.168.1.1-10.0.0.1-80", "192.168.1.2-10.0.0.1-80", "10.0.0.1-10.0.0.2-443"]

    audit = contract.validate_dataframe(dirty_df)

    assert audit["has_leakage_hazard"] is True
    assert "Source IP" in audit["detected_leakage_columns"]
    assert "Timestamp" in audit["detected_leakage_columns"]
    assert "Flow ID" in audit["detected_leakage_columns"]
    assert audit["is_valid_for_training"] is False


def test_prepare_feature_matrix_leakage_removal(sample_feature_df):
    contract = FeatureContract()
    dirty_df = sample_feature_df.copy()
    dirty_df["Source IP"] = ["192.168.1.1", "192.168.1.2", "10.0.0.1"]
    dirty_df["Timestamp"] = ["03/07/2017 09:00", "03/07/2017 09:01", "03/07/2017 09:02"]

    X, y = contract.prepare_feature_matrix(dirty_df, label_col="Label")

    # X must be strictly numeric
    assert X.select_dtypes(include=[np.number]).shape[1] == X.shape[1]
    # Forbidden columns must be stripped
    assert "Source IP" not in X.columns
    assert "Timestamp" not in X.columns
    assert "Label" not in X.columns
    # Types must be downcasted to float32
    assert X["Flow Duration"].dtype == np.float32
    # y must contain targets
    assert list(y) == ["BENIGN", "BENIGN", "DDoS"]


def test_prepare_feature_matrix_inf_and_nan(sample_feature_df):
    contract = FeatureContract()
    dirty_df = sample_feature_df.copy()
    dirty_df.loc[0, "Flow Bytes/s"] = np.inf
    dirty_df.loc[1, "Flow Packets/s"] = np.nan

    X, y = contract.prepare_feature_matrix(dirty_df, label_col="Label")

    # Infinities and NaNs must be sanitized
    assert not np.isinf(X["Flow Bytes/s"]).any()
    assert not X["Flow Packets/s"].isna().any()
