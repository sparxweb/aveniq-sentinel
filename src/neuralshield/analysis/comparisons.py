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
    target_col: Optional[str] = None,
    label_col: Optional[str] = None,
    metrics: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Computes comprehensive statistical comparisons between benign and attack traffic:
    - Median and IQR for heavy-tailed telemetry
    - Mean and Standard Deviation
    - Attack-to-Benign median divergence ratio (divergence_ratio / attack_to_benign_median_ratio)
    - TCP flag breakdown across classes
    - Robust handling of single-class, empty, missing, or null-laden DataFrames.

    Args:
        df: Input DataFrame containing network flow telemetry.
        target_col: Name of the label/target column (primary).
        label_col: Alias for target_col for API compatibility.
        metrics: Optional explicit list of feature names or substrings to compare.

    Returns:
        Structured dictionary containing statistical comparisons and empirical findings.
    """
    base_structure: Dict[str, Any] = {
        "benign_sample_count": 0,
        "attack_sample_count": 0,
        "feature_comparisons": {},
        "tcp_flag_comparisons": {},
        "empirical_findings": [],
    }

    if df is None or df.empty:
        base_structure["error"] = "DataFrame is empty or None."
        return base_structure

    # Resolve target column name from target_col or label_col (case-insensitive)
    effective_target = target_col or label_col or "label"

    found_target = None
    for c in df.columns:
        if c.strip().lower() == effective_target.strip().lower():
            found_target = c
            break

    # Fallback search if standard name was not exact match
    if not found_target:
        for candidate in ["label", "target", "class", "threat_category"]:
            for c in df.columns:
                if c.strip().lower() == candidate:
                    found_target = c
                    break
            if found_target:
                break

    if not found_target:
        base_structure["error"] = f"Target column '{effective_target}' not found in DataFrame."
        return base_structure

    # Drop null labels to ensure robust classification
    valid_df = df.dropna(subset=[found_target])
    if valid_df.empty:
        base_structure["error"] = f"Target column '{found_target}' contains only null values."
        return base_structure

    # Separate benign and attack records
    # Benign flows are identified if label string contains 'benign' (case-insensitive)
    target_series_str = valid_df[found_target].astype(str).str.strip().str.lower()
    is_benign = target_series_str.str.contains("benign")

    benign_df = valid_df[is_benign]
    attack_df = valid_df[~is_benign]

    base_structure["benign_sample_count"] = int(len(benign_df))
    base_structure["attack_sample_count"] = int(len(attack_df))

    if len(benign_df) == 0:
        base_structure["warning"] = "Dataset contains only attack traffic (no benign baseline). Comparative analysis unavailable."
        return base_structure

    if len(attack_df) == 0:
        base_structure["warning"] = "Dataset contains only benign traffic (no attack samples). Comparative analysis unavailable."
        return base_structure

    # Select numerical metrics to compare (excluding non-numeric columns and target column)
    cols_to_compare: List[str] = []
    candidates = metrics or DEFAULT_COMPARISON_METRICS
    numeric_cols = [c for c in valid_df.select_dtypes(include=[np.number]).columns if c != found_target]

    for cand in candidates:
        cand_norm = cand.lower().replace(" ", "_").strip()
        for c in numeric_cols:
            col_norm = c.lower().replace(" ", "_").strip()
            if (cand_norm in col_norm or col_norm in cand_norm) and c not in cols_to_compare:
                cols_to_compare.append(c)

    # Fallback: if candidate matching produced no columns, include available numeric columns (up to 15, excluding flags)
    if not cols_to_compare:
        cols_to_compare = [c for c in numeric_cols if "flag" not in c.lower()][:15]

    # 1. Metric Comparisons with Division-by-Zero Safety
    for col in cols_to_compare:
        # Strip NaNs and infinite values for calculation
        b_series = benign_df[col].replace([np.inf, -np.inf], np.nan).dropna()
        a_series = attack_df[col].replace([np.inf, -np.inf], np.nan).dropna()

        if len(b_series) == 0 or len(a_series) == 0:
            continue

        b_med = float(b_series.median())
        a_med = float(a_series.median())
        b_mean = float(b_series.mean())
        a_mean = float(a_series.mean())
        b_iqr = float(b_series.quantile(0.75) - b_series.quantile(0.25))
        a_iqr = float(a_series.quantile(0.75) - a_series.quantile(0.25))

        # Safe divergence ratio calculation
        if b_med > 0:
            ratio = round(float(a_med / b_med), 2)
        elif b_med == 0.0:
            ratio = 100.0 if a_med > 0 else 1.0
        else:
            ratio = round(float(a_med / max(abs(b_med), 1e-6)), 2)

        stat_record = {
            "benign_mean": round(b_mean, 2),
            "attack_mean": round(a_mean, 2),
            "benign_median": round(b_med, 2),
            "attack_median": round(a_med, 2),
            "benign_iqr": round(b_iqr, 2),
            "attack_iqr": round(a_iqr, 2),
            "attack_to_benign_median_ratio": ratio,
            "divergence_ratio": ratio,
        }
        base_structure["feature_comparisons"][col] = stat_record

    # 2. TCP Flag Comparisons
    flag_cols = [c for c in valid_df.columns if "flag" in c.lower() and c in numeric_cols]
    for f_col in flag_cols:
        b_flag_series = benign_df[f_col].replace([np.inf, -np.inf], np.nan).dropna()
        a_flag_series = attack_df[f_col].replace([np.inf, -np.inf], np.nan).dropna()

        if len(b_flag_series) == 0 or len(a_flag_series) == 0:
            continue

        b_pct = round(float((b_flag_series > 0).mean()) * 100.0, 2)
        a_pct = round(float((a_flag_series > 0).mean()) * 100.0, 2)
        base_structure["tcp_flag_comparisons"][f_col] = {
            "benign_percentage_active": b_pct,
            "attack_percentage_active": a_pct,
            "percentage_point_difference": round(a_pct - b_pct, 2),
        }

    # 3. Derive Empirical Findings
    findings: List[str] = []
    syn_flag = next((c for c in flag_cols if "syn" in c.lower()), None)
    if syn_flag and syn_flag in base_structure["tcp_flag_comparisons"]:
        diff = base_structure["tcp_flag_comparisons"][syn_flag]["percentage_point_difference"]
        if abs(diff) >= 5.0:
            findings.append(
                f"SYN Flag activation diverges by {abs(diff)}% between attack "
                f"({base_structure['tcp_flag_comparisons'][syn_flag]['attack_percentage_active']}%) "
                f"and benign traffic ({base_structure['tcp_flag_comparisons'][syn_flag]['benign_percentage_active']}%), "
                "characteristic of reconnaissance port scanning and SYN flooding."
            )

    dur_match = next((c for c in cols_to_compare if "duration" in c.lower()), None)
    if dur_match and dur_match in base_structure["feature_comparisons"]:
        a_med_dur = base_structure["feature_comparisons"][dur_match]["attack_median"]
        b_med_dur = base_structure["feature_comparisons"][dur_match]["benign_median"]
        if a_med_dur < b_med_dur:
            findings.append(
                f"Attack traffic exhibits substantially shorter median flow duration ({a_med_dur:,} us vs {b_med_dur:,} us), "
                "consistent with high-velocity automated attack scripts that do not establish sustained session exchanges."
            )

    base_structure["empirical_findings"] = findings
    return base_structure
