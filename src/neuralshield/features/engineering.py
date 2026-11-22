"""Domain-specific network flow feature engineering, semantic feature grouping, and ML feature preparation."""

from typing import List, Tuple, Optional, Dict, Any
import pandas as pd
import numpy as np
from config.settings import TARGET_LEAKAGE_COLUMNS
from config.logging_config import get_logger

logger = get_logger("features.engineering")


# 5 Core Semantic Groups for CIC-IDS2017
SEMANTIC_FEATURE_GROUPS = {
    "traffic_volume": {
        "name": "Network Traffic Volume",
        "description": "Forward and backward packet counts, byte volumes, and directional symmetry ratios.",
        "features": [
            "total_fwd_packets",
            "total_backward_packets",
            "total_length_of_fwd_packets",
            "total_length_of_bwd_packets",
            "packet_symmetry_ratio",
            "byte_symmetry_ratio",
        ],
    },
    "flow_timing": {
        "name": "Network Flow Timing & Inter-Arrival Dynamics",
        "description": "Flow duration, inter-arrival time (IAT) metrics, active/idle time windows, and log duration transforms.",
        "features": [
            "flow_duration",
            "log_flow_duration",
            "flow_iat_mean",
            "flow_iat_std",
            "flow_iat_max",
            "flow_iat_min",
            "fwd_iat_total",
            "bwd_iat_total",
        ],
    },
    "tcp_behavior": {
        "name": "TCP Connection Behavior & Flags",
        "description": "Connection handshake state flags (SYN, ACK, FIN, RST, PSH, URG), flag ratios, and scan density.",
        "features": [
            "fin_flag_count",
            "syn_flag_count",
            "rst_flag_count",
            "psh_flag_count",
            "ack_flag_count",
            "urg_flag_count",
            "syn_packet_density",
            "syn_to_ack_ratio",
        ],
    },
    "traffic_rates": {
        "name": "Traffic Rates & Throughput Dynamics",
        "description": "Rates of packet and byte transmission per second, average packet size, and directional throughput.",
        "features": [
            "flow_bytes_per_sec",
            "flow_packets_per_sec",
            "fwd_packets_per_sec",
            "bwd_packets_per_sec",
            "average_packet_size",
        ],
    },
    "packet_characteristics": {
        "name": "Packet Length & Statistical Variations",
        "description": "Statistical distributions of packet payload lengths across forward and backward channels.",
        "features": [
            "min_packet_length",
            "max_packet_length",
            "packet_length_mean",
            "packet_length_std",
            "packet_length_variance",
            "packet_length_spread",
        ],
    },
}


def create_network_domain_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derives domain-specific cybersecurity and network telemetry features:
    
    1. Volume Group:
       - packet_symmetry_ratio: Ratio of forward packets to backward packets
       - byte_symmetry_ratio: Ratio of forward bytes to backward bytes
       - total_volume_bytes: Aggregate forward and backward byte load
       
    2. Timing Group:
       - log_flow_duration: Natural log(1 + duration) to stabilize heavy-tailed microsecond metrics
       
    3. TCP Behavior Group:
       - syn_packet_density: Proportion of forward packets accompanied by SYN flags
       - syn_to_ack_ratio: Ratio of SYN to ACK flags (elevated during SYN port scans)
       
    4. Rate Group:
       - fwd_to_bwd_rate_ratio: Ratio of forward transmission rate to backward rate
       
    5. Packet Characteristics Group:
       - packet_length_spread: Difference between maximum and minimum observed packet lengths
    """
    df_feat = df.copy()
    cols = df_feat.columns

    # Helper function to find matching column case-insensitively
    def find_col(patterns: List[str]) -> Optional[str]:
        for pat in patterns:
            for c in cols:
                c_clean = c.lower().replace(" ", "_").replace("-", "_").replace("/", "_")
                if pat in c_clean:
                    return c
        return None

    # 1. Volume Features
    fwd_pkts = find_col(["total_fwd_packets", "total_fwd_packet"])
    bwd_pkts = find_col(["total_backward_packets", "total_bwd_packets"])
    fwd_bytes = find_col(["total_length_of_fwd_packets", "fwd_pkt_len_tot"])
    bwd_bytes = find_col(["total_length_of_bwd_packets", "bwd_pkt_len_tot"])

    if fwd_pkts and bwd_pkts:
        denom = np.maximum(df_feat[bwd_pkts].astype(float), 1.0)
        df_feat["packet_symmetry_ratio"] = (df_feat[fwd_pkts].astype(float) / denom).astype(np.float32)

    if fwd_bytes and bwd_bytes:
        denom_b = np.maximum(df_feat[bwd_bytes].astype(float), 1.0)
        df_feat["byte_symmetry_ratio"] = (df_feat[fwd_bytes].astype(float) / denom_b).astype(np.float32)
        df_feat["total_volume_bytes"] = (df_feat[fwd_bytes].astype(float) + df_feat[bwd_bytes].astype(float)).astype(np.float32)

    # 2. Timing Features
    dur_col = find_col(["flow_duration"])
    if dur_col:
        df_feat["log_flow_duration"] = np.log1p(
            np.clip(df_feat[dur_col].astype(float), 0, None)
        ).astype(np.float32)

    # 3. TCP Behavior Features
    syn_col = find_col(["syn_flag_count"])
    ack_col = find_col(["ack_flag_count"])

    if syn_col and fwd_pkts:
        denom_p = np.maximum(df_feat[fwd_pkts].astype(float), 1.0)
        df_feat["syn_packet_density"] = (df_feat[syn_col].astype(float) / denom_p).astype(np.float32)

    if syn_col and ack_col:
        denom_a = np.maximum(df_feat[ack_col].astype(float), 1.0)
        df_feat["syn_to_ack_ratio"] = (df_feat[syn_col].astype(float) / denom_a).astype(np.float32)

    # 4. Packet Characteristics Features
    max_len = find_col(["max_packet_length", "packet_length_max"])
    min_len = find_col(["min_packet_length", "packet_length_min"])
    if max_len and min_len:
        df_feat["packet_length_spread"] = (
            df_feat[max_len].astype(float) - df_feat[min_len].astype(float)
        ).astype(np.float32)

    return df_feat


def get_feature_catalog(df: pd.DataFrame) -> Dict[str, Any]:
    """Generates an inventory and documentation catalog of features mapped to the 5 semantic groups."""
    cols = [c.lower() for c in df.columns]
    catalog = {}

    for group_key, group_meta in SEMANTIC_FEATURE_GROUPS.items():
        present_in_group = []
        for feat in group_meta["features"]:
            if any(feat in c for c in cols):
                present_in_group.append(feat)

        catalog[group_key] = {
            "group_name": group_meta["name"],
            "description": group_meta["description"],
            "expected_features_count": len(group_meta["features"]),
            "present_features_count": len(present_in_group),
            "present_features": present_in_group,
        }

    return catalog


def remove_target_leakage_features(
    df: pd.DataFrame,
    leakage_cols: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, List[str]]:
    """Removes columns known to introduce target leakage (e.g. IPs, Timestamps, IDs).
    
    Returns:
        (filtered_df, list_of_removed_columns)
    """
    to_exclude = leakage_cols or TARGET_LEAKAGE_COLUMNS
    removed = []
    
    for col in df.columns:
        col_clean = col.strip().lower()
        for leak in to_exclude:
            if col_clean == leak.strip().lower():
                removed.append(col)
                break
                
    if removed:
        logger.info(f"Filtered target-leakage features: {removed}")
        return df.drop(columns=removed, errors="ignore"), removed
    return df, []
