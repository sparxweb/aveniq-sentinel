"""Unit tests for feature engineering, semantic feature grouping, target leakage and risk engine."""

import pytest
import pandas as pd
import numpy as np
from neuralshield.features.engineering import (
    create_network_domain_features,
    remove_target_leakage_features,
    get_feature_catalog,
    SEMANTIC_FEATURE_GROUPS,
)
from neuralshield.intelligence.risk_engine import NetworkRiskEngine


def test_create_network_domain_features():
    """Verifies creation of packet symmetry, byte symmetry, and log duration features."""
    df = pd.DataFrame({
        "total_fwd_packets": [10, 20],
        "total_backward_packets": [5, 0],
        "total_length_of_fwd_packets": [1000.0, 2000.0],
        "total_length_of_bwd_packets": [500.0, 0.0],
        "flow_duration": [5000.0, 100.0],
        "syn_flag_count": [1, 0],
        "ack_flag_count": [1, 1],
        "max_packet_length": [1500.0, 1000.0],
        "min_packet_length": [50.0, 0.0],
    })
    feat_df = create_network_domain_features(df)
    assert "packet_symmetry_ratio" in feat_df.columns
    assert "byte_symmetry_ratio" in feat_df.columns
    assert "total_volume_bytes" in feat_df.columns
    assert "log_flow_duration" in feat_df.columns
    assert "syn_packet_density" in feat_df.columns
    assert "syn_to_ack_ratio" in feat_df.columns
    assert "packet_length_spread" in feat_df.columns


def test_get_feature_catalog(clean_synthetic_df):
    """Verifies feature catalog maps features to the 5 semantic groups."""
    catalog = get_feature_catalog(clean_synthetic_df)
    assert len(catalog) == 5
    assert "traffic_volume" in catalog
    assert "flow_timing" in catalog
    assert "tcp_behavior" in catalog
    assert "traffic_rates" in catalog
    assert "packet_characteristics" in catalog


def test_remove_target_leakage_features():
    """Verifies removal of columns that cause target leakage."""
    df = pd.DataFrame({
        "flow_id": ["id1", "id2"],
        "source_ip": ["192.168.1.1", "10.0.0.1"],
        "destination_ip": ["192.168.1.2", "10.0.0.2"],
        "timestamp": ["2017-07-07", "2017-07-07"],
        "destination_port": [80, 443],
        "label": ["Benign", "DDoS"],
    })
    cleaned, removed = remove_target_leakage_features(df)
    assert "flow_id" in removed
    assert "source_ip" in removed
    assert "destination_ip" in removed
    assert "timestamp" in removed
    assert "destination_port" in cleaned.columns
    assert "label" in cleaned.columns


def test_network_risk_engine_heuristics():
    """Verifies that heuristic risk scoring triggers expected risk levels."""
    # PortScan pattern: unanswered SYN with 0 backward packets
    port_scan_flow = pd.Series({
        "syn_flag_count": 1,
        "total_backward_packets": 0,
        "flow_packets_per_sec": 500,
        "flow_duration": 1000,
        "total_fwd_packets": 1,
    })
    res_ps = NetworkRiskEngine.calculate_flow_risk_score(port_scan_flow)
    assert res_ps["risk_score"] >= 35.0
    assert any("SYN" in ind for ind in res_ps["indicators"])
    
    # Normal Benign flow
    benign_flow = pd.Series({
        "syn_flag_count": 0,
        "total_backward_packets": 10,
        "flow_packets_per_sec": 50,
        "flow_duration": 50000,
        "total_fwd_packets": 10,
    })
    res_b = NetworkRiskEngine.calculate_flow_risk_score(benign_flow)
    assert res_b["risk_level"] == "Low"
