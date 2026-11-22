"""Statistical comparison of network behaviors between benign and attack traffic."""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from config.logging_config import get_logger

logger = get_logger("analysis.comparisons")

DEFAULT_COMPARISON_METRICS = [
    "flow_duration",
    "total_fwd_packets",
    "total_backward_packets",
    "flow_bytes_per_sec",
    "flow_packets_per_sec",
    "packet_length_mean",
]


def compare_benign_vs_attack(
    df: pd.DataFrame,
    target_col: str = "label",
    metrics: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Computes comprehensive statistical comparisons between benign and attack traffic:
    - Median and IQR for heavy-tailed telemetry
    - Mean and Standard Deviation
    - Attack-to-Benign median divergence ratio
    - TCP flag breakdown across classes
    """
    if df.empty:
        return {"error": "DataFrame is empty"}

    found_target = None
    for c in df.columns:
        if c.strip().lower() == target_col.strip().lower():
            found_target = c
            break

    if not found_target:
        return {"error": f"Target column '{target_col}' not found"}

    # Separate benign and attack records
    is_benign = df[found_target].astype(str).str.lower().str.contains("benign")
    benign_df = df[is_benign]
    attack_df = df[~is_benign]

    comparison_results: Dict[str, Any] = {
        "benign_sample_count": len(benign_df),
        "attack_sample_count": len(attack_df),
        "feature_comparisons": {},
        "tcp_flag_comparisons": {},
        "empirical_findings": [],
    }

    if len(benign_df) == 0 or len(attack_df) == 0:
        comparison_results["warning"] = "Dataset contains only one class. Comparative analysis unavailable."
        return comparison_results

    # Select numerical metrics to compare
    cols_to_compare = []
    candidates = metrics or DEFAULT_COMPARISON_METRICS
    for cand in candidates:
        for c in df.select_dtypes(include=[np.number]).columns:
            if cand in c.lower() and c not in cols_to_compare:
                cols_to_compare.append(c)

    # 1. Metric Comparisons
    for col in cols_to_compare:
        b_series = benign_df[col].dropna()
        a_series = attack_df[col].dropna()

        if len(b_series) == 0 or len(a_series) == 0:
            continue

        b_med = float(b_series.median())
        a_med = float(a_series.median())
        b_mean = float(b_series.mean())
        a_mean = float(a_series.mean())
        b_iqr = float(b_series.quantile(0.75) - b_series.quantile(0.25))
        a_iqr = float(a_series.quantile(0.75) - a_series.quantile(0.25))

        ratio = round(a_med / max(b_med, 1e-6), 2) if b_med > 0 else (100.0 if a_med > 0 else 1.0)

        comparison_results["feature_comparisons"][col] = {
            "benign_mean": round(b_mean, 2),
            "attack_mean": round(a_mean, 2),
            "benign_median": round(b_med, 2),
            "attack_median": round(a_med, 2),
            "benign_iqr": round(b_iqr, 2),
            "attack_iqr": round(a_iqr, 2),
            "attack_to_benign_median_ratio": ratio,
        }

    # 2. TCP Flag Comparisons
    flag_cols = [c for c in df.columns if "flag" in c.lower()]
    for f_col in flag_cols:
        if pd.api.types.is_numeric_dtype(df[f_col]):
            b_pct = round(float((benign_df[f_col] > 0).mean()) * 100.0, 2)
            a_pct = round(float((attack_df[f_col] > 0).mean()) * 100.0, 2)
            comparison_results["tcp_flag_comparisons"][f_col] = {
                "benign_percentage_active": b_pct,
                "attack_percentage_active": a_pct,
                "percentage_point_difference": round(a_pct - b_pct, 2),
            }

    # 3. Derive Empirical Findings
    findings = []
    syn_flag = next((c for c in flag_cols if "syn" in c.lower()), None)
    if syn_flag and syn_flag in comparison_results["tcp_flag_comparisons"]:
        diff = comparison_results["tcp_flag_comparisons"][syn_flag]["percentage_point_difference"]
        if abs(diff) >= 5.0:
            findings.append(
                f"SYN Flag activation diverges by {abs(diff)}% between attack ({comparison_results['tcp_flag_comparisons'][syn_flag]['attack_percentage_active']}%) "
                f"and benign traffic ({comparison_results['tcp_flag_comparisons'][syn_flag]['benign_percentage_active']}%), "
                "characteristic of reconnaissance port scanning and SYN flooding."
            )

    dur_match = next((c for c in cols_to_compare if "duration" in c.lower()), None)
    if dur_match and dur_match in comparison_results["feature_comparisons"]:
        a_med_dur = comparison_results["feature_comparisons"][dur_match]["attack_median"]
        b_med_dur = comparison_results["feature_comparisons"][dur_match]["benign_median"]
        if a_med_dur < b_med_dur:
            findings.append(
                f"Attack traffic exhibits substantially shorter median flow duration ({a_med_dur:,} us vs {b_med_dur:,} us), "
                "consistent with high-velocity automated attack scripts that do not establish sustained session exchanges."
            )

    comparison_results["empirical_findings"] = findings
    return comparison_results
