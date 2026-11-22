"""Unit tests for Unified Data Source Manager (Phase 2.1)."""

import pytest
import pandas as pd
from pathlib import Path
from neuralshield.data.source_manager import (
    detect_data_source,
    load_active_dataset,
    SOURCE_OFFICIAL,
    SOURCE_USER,
    SOURCE_DEMO,
    SOURCE_NONE,
)
from config.settings import RAW_DATA_DIR, SAMPLE_DATA_DIR


def test_detect_data_source_none():
    res = detect_data_source(None)
    assert res["source_type"] == SOURCE_NONE
    assert res["is_real_telemetry"] is False
    assert res["flow_count"] == 0
    assert "No Dataset Available" in res["source_name"]


def test_detect_data_source_official_path():
    fake_raw = RAW_DATA_DIR / "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv"
    df = pd.DataFrame({"Flow Duration": [100, 200], "Label": ["BENIGN", "DDoS"]})
    res = detect_data_source(df, source_path=fake_raw)
    assert res["source_type"] == SOURCE_OFFICIAL
    assert res["is_real_telemetry"] is True
    assert res["flow_count"] == 2
    assert "Official" in res["source_name"]
    assert res["disclaimer"] is None


def test_detect_data_source_sample_path():
    sample_file = SAMPLE_DATA_DIR / "cic_ids2017_sample.csv"
    df = pd.DataFrame({"Flow Duration": [100, 200], "Label": ["BENIGN", "BENIGN"]})
    res = detect_data_source(df, source_path=sample_file)
    assert res["source_type"] == SOURCE_DEMO
    assert res["is_real_telemetry"] is False
    assert "DEMONSTRATION DATA" in res["disclaimer"]


def test_detect_data_source_user_upload():
    df = pd.DataFrame({"Flow Duration": [100, 200, 300], "Label": ["BENIGN", "Attack", "BENIGN"]})
    res = detect_data_source(df, source_name="Uploaded custom_capture.csv")
    assert res["source_type"] == SOURCE_USER
    assert res["is_real_telemetry"] is True
    assert res["badge_class"] == "badge-cyan"


def test_detect_data_source_override():
    res = detect_data_source(source_type_override=SOURCE_OFFICIAL)
    assert res["source_type"] == SOURCE_OFFICIAL
    assert res["is_real_telemetry"] is True
