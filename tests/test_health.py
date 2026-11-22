"""Unit tests for Truthful Operational Health Monitoring (Phase 2.1)."""

import pytest
import pandas as pd
from neuralshield.utils.health import (
    evaluate_system_health,
    STATUS_OPERATIONAL,
    STATUS_DEGRADED,
    STATUS_ERROR,
    STATUS_NO_DATA,
)


def test_evaluate_system_health_structure():
    health = evaluate_system_health()
    assert "overall_status" in health
    assert "overall_label" in health
    assert "badge_class" in health
    assert "components" in health
    assert isinstance(health["components"], dict)
    
    expected_components = [
        "dataset_loader",
        "data_validator",
        "cleaning_engine",
        "feature_engineering",
        "eda_engine",
        "visualization_engine",
        "export_engine",
    ]
    for comp in expected_components:
        assert comp in health["components"]
        assert "status" in health["components"][comp]
        assert "details" in health["components"][comp]


def test_evaluate_system_health_execution():
    test_df = pd.DataFrame({
        "Flow Duration": [1000.0, 2000.0, 3000.0, 4000.0],
        "Total Fwd Packets": [10.0, 20.0, 15.0, 25.0],
        "Total Backward Packets": [5.0, 10.0, 8.0, 12.0],
        "Flow Bytes/s": [500.0, 1000.0, 750.0, 1200.0],
        "Flow Packets/s": [15.0, 30.0, 23.0, 37.0],
        "SYN Flag Count": [1, 0, 1, 0],
        "ACK Flag Count": [0, 1, 0, 1],
        "Label": ["BENIGN", "BENIGN", "DDoS", "PortScan"],
    })
    health = evaluate_system_health(test_df)
    
    # Validator, cleaning, features, eda, viz, export must all pass
    assert health["components"]["data_validator"]["status"] == STATUS_OPERATIONAL
    assert health["components"]["cleaning_engine"]["status"] == STATUS_OPERATIONAL
    assert health["components"]["feature_engineering"]["status"] == STATUS_OPERATIONAL
    assert health["components"]["eda_engine"]["status"] == STATUS_OPERATIONAL
    assert health["components"]["visualization_engine"]["status"] == STATUS_OPERATIONAL
    assert health["components"]["export_engine"]["status"] == STATUS_OPERATIONAL
    assert health["error_count"] == 0


def test_evaluate_system_health_status_derivation():
    health = evaluate_system_health()
    # In sandbox environment without full 3.1 GB raw files extracted,
    # status should truthfully be DEGRADED (sample fixture) or OPERATIONAL, never ERROR
    assert health["overall_status"] in (STATUS_OPERATIONAL, STATUS_DEGRADED)
    assert health["badge_class"] in ("badge-emerald", "badge-amber")
