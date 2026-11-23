"""Unit tests for Chronological Temporal Splitting Architecture (Phase 3.1)."""

import pytest
import pandas as pd
import numpy as np

from neuralshield.ml.temporal import (
    TemporalSplitter,
    TemporalSplit,
    KNOWN_TRAINING_ATTACKS,
    UNSEEN_TEST_ATTACKS,
)


@pytest.fixture
def sample_daily_data():
    """Generates synthetic multi-day network flow datasets matching CIC-IDS2017 day profiles."""
    monday = pd.DataFrame({
        "Flow Duration": [100.0, 200.0, 150.0],
        "Total Fwd Packets": [10.0, 20.0, 15.0],
        "Label": ["BENIGN", "BENIGN", "BENIGN"],
    })
    tuesday = pd.DataFrame({
        "Flow Duration": [300.0, 400.0],
        "Total Fwd Packets": [30.0, 40.0],
        "Label": ["BENIGN", "FTP-Patator"],
    })
    wednesday = pd.DataFrame({
        "Flow Duration": [500.0, 600.0, 700.0],
        "Total Fwd Packets": [50.0, 60.0, 70.0],
        "Label": ["BENIGN", "DoS Hulk", "Heartbleed"],
    })
    thursday = pd.DataFrame({
        "Flow Duration": [800.0, 900.0],
        "Total Fwd Packets": [80.0, 90.0],
        "Label": ["BENIGN", "Web Attack  Brute Force"],
    })
    friday = pd.DataFrame({
        "Flow Duration": [1000.0, 1100.0],
        "Total Fwd Packets": [100.0, 110.0],
        "Label": ["PortScan", "DDoS"],
    })

    return {
        "Monday": monday,
        "Tuesday": tuesday,
        "Wednesday": wednesday,
        "Thursday": thursday,
        "Friday": friday,
    }


def test_temporal_split_by_day(sample_daily_data):
    splitter = TemporalSplitter(val_fraction_of_train=0.25)
    split = splitter.split_by_day(sample_daily_data, label_col="Label")

    assert isinstance(split, TemporalSplit)
    # Mon (3) + Tue (2) + Wed (3) = 8 flows total in train period
    assert len(split.train_df) + len(split.val_df) == 8
    # Thu (2) + Fri (2) = 4 flows in test period
    assert len(split.test_df) == 4

    # Verify that unseen attack classes are correctly identified
    assert "Web Attack  Brute Force" in split.unseen_test_classes
    assert "PortScan" in split.unseen_test_classes
    assert "DDoS" in split.unseen_test_classes
    # Known attacks must NOT be in unseen
    assert "FTP-Patator" not in split.unseen_test_classes
    assert "DoS Hulk" not in split.unseen_test_classes


def test_temporal_split_single_dataframe():
    df = pd.DataFrame({
        "Flow Duration": list(range(100)),
        "Total Fwd Packets": list(range(100)),
        "Label": ["BENIGN"] * 80 + ["DDoS"] * 20,
    })
    splitter = TemporalSplitter()
    split = splitter.split_single_dataframe_chronologically(
        df,
        train_ratio=0.60,
        val_ratio=0.20,
        test_ratio=0.20,
    )

    assert len(split.train_df) == 60
    assert len(split.val_df) == 20
    assert len(split.test_df) == 20
    # Chronological integrity: train should have indices 0..59, val 60..79, test 80..99
    assert split.train_df["Flow Duration"].iloc[0] == 0
    assert split.train_df["Flow Duration"].iloc[-1] == 59
    assert split.test_df["Flow Duration"].iloc[-1] == 99


def test_partition_known_vs_unseen_test(sample_daily_data):
    splitter = TemporalSplitter()
    split = splitter.split_by_day(sample_daily_data, label_col="Label")

    known_test, unseen_test = splitter.partition_known_vs_unseen_test(
        split.test_df,
        split.train_classes,
        label_col="Label",
    )

    # In Thu/Fri test set: BENIGN was present in Mon-Wed, so it is known
    assert all(known_test["Label"] == "BENIGN")
    # Web Attack, PortScan, DDoS were never in Mon-Wed, so they are unseen
    unseen_labels = set(unseen_test["Label"])
    assert "Web Attack  Brute Force" in unseen_labels
    assert "PortScan" in unseen_labels
    assert "DDoS" in unseen_labels


def test_temporal_split_missing_days():
    splitter = TemporalSplitter()
    # Missing train period data
    with pytest.raises(ValueError, match="No Monday-Wednesday data found"):
        splitter.split_by_day({"Thursday": pd.DataFrame({"Label": ["BENIGN"]})})
