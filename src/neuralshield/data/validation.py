"""Comprehensive dataset validation, numerical integrity auditing, and reporting engine."""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
import pandas as pd
import numpy as np
from neuralshield.utils.validators import validate_dataframe_not_empty
from neuralshield.utils.file_utils import ensure_directory
from neuralshield.data.discovery import inspect_dataset_inventory
from config.settings import DATA_QUALITY_REPORTS_DIR
from config.logging_config import get_logger

logger = get_logger("data.validation")

# Inherently non-negative network features
NON_NEGATIVE_FEATURE_PATTERNS = [
    "packet",
    "byte",
    "duration",
    "iat",
    "header",
    "window",
    "rate",
    "count",
    "length",
]


def inspect_numerical_anomalies(df: pd.DataFrame) -> Dict[str, Any]:
    """Inspects numeric columns for anomalies:
    - Negative values in features that must be non-negative.
    - Zero flow durations with positive packet counts (division-by-zero risk).
    - Constant / zero-variance columns.
    """
    anomalies: Dict[str, Any] = {
        "negative_value_violations": {},
        "zero_duration_flows_with_packets": 0,
        "constant_columns": [],
    }

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        col_lower = col.lower()
        # Check non-negative expectations (excluding window sizes which can sometimes be -1)
        if any(pat in col_lower for pat in NON_NEGATIVE_FEATURE_PATTERNS) and "win" not in col_lower:
            neg_count = int((df[col] < 0).sum())
            if neg_count > 0:
                anomalies["negative_value_violations"][col] = neg_count

        # Check zero-variance
        if df[col].nunique(dropna=False) <= 1:
            anomalies["constant_columns"].append(col)

    # Check zero-duration with positive packets
    duration_col = next((c for c in df.columns if "duration" in c.lower()), None)
    packets_col = next((c for c in df.columns if "packets" in c.lower() and "total" in c.lower()), None)
    if duration_col and packets_col and duration_col in numeric_cols and packets_col in numeric_cols:
        bad_flows = int(((df[duration_col] == 0) & (df[packets_col] > 0)).sum())
        anomalies["zero_duration_flows_with_packets"] = bad_flows

    return anomalies


def audit_dataframe_quality(
    df: pd.DataFrame,
    target_col: str = "label",
    context_name: str = "Dataset",
) -> Dict[str, Any]:
    """Generates an exhaustive quality and integrity audit of a dataframe.
    
    Returns:
        Structured dictionary containing dimensions, missing values, infinite values,
        duplicates, data types, memory consumption, class balance, and numerical anomalies.
    """
    validate_dataframe_not_empty(df, context_name)
    
    total_rows = len(df)
    total_cols = len(df.columns)
    
    # 1. Missing value statistics
    missing_by_col = df.isna().sum().to_dict()
    cols_with_missing = {k: int(v) for k, v in missing_by_col.items() if v > 0}
    total_missing = sum(cols_with_missing.values())
    rows_with_missing = int(df.isna().any(axis=1).sum())
    empty_columns = [k for k, v in missing_by_col.items() if v == total_rows]
    
    # 2. Infinite value statistics
    numeric_df = df.select_dtypes(include=[np.number])
    cols_with_infinite = {}
    pos_inf_count = 0
    neg_inf_count = 0
    if not numeric_df.empty:
        arr = numeric_df.to_numpy()
        pos_mask = np.isposinf(arr)
        neg_mask = np.isneginf(arr)
        pos_inf_count = int(np.sum(pos_mask))
        neg_inf_count = int(np.sum(neg_mask))
        
        for col in numeric_df.columns:
            inf_cnt = int(np.isinf(df[col]).sum())
            if inf_cnt > 0:
                cols_with_infinite[col] = inf_cnt
                
    total_infinite = pos_inf_count + neg_inf_count
                
    # 3. Duplicate statistics
    duplicate_count = int(df.duplicated().sum())
    duplicate_ratio = round((duplicate_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
    
    # 4. Duplicate column names and identical columns
    col_names = [str(c) for c in df.columns]
    duplicate_column_names = [c for c in set(col_names) if col_names.count(c) > 1]
    
    # 5. Memory usage
    memory_bytes = int(df.memory_usage(deep=True).sum())
    memory_mb = round(memory_bytes / (1024 * 1024), 2)
    
    # 6. Target / Class balance (both binary and multiclass)
    target_summary: Dict[str, Any] = {}
    found_target = None
    for c in df.columns:
        if c.strip().lower() == target_col.strip().lower():
            found_target = c
            break
            
    if found_target:
        class_counts = df[found_target].value_counts().to_dict()
        class_pcts = (df[found_target].value_counts(normalize=True) * 100).round(3).to_dict()
        
        # Binary breakdown: Benign vs Attack
        benign_cnt = sum(cnt for lbl, cnt in class_counts.items() if "benign" in str(lbl).lower())
        attack_cnt = total_rows - benign_cnt
        binary_counts = {"Benign": benign_cnt, "Attack": attack_cnt}
        binary_pcts = {
            "Benign": round((benign_cnt / max(1, total_rows)) * 100, 2),
            "Attack": round((attack_cnt / max(1, total_rows)) * 100, 2),
        }
        
        target_summary = {
            "target_column": found_target,
            "classes_detected": len(class_counts),
            "multiclass_distribution": {str(k): int(v) for k, v in class_counts.items()},
            "multiclass_percentages": {str(k): float(v) for k, v in class_pcts.items()},
            "binary_distribution": binary_counts,
            "binary_percentages": binary_pcts,
            "is_imbalanced": (max(class_pcts.values()) > 80.0) if class_pcts else False,
            "missing_labels": int(df[found_target].isna().sum()),
        }

    # 7. Numerical anomalies
    anomalies = inspect_numerical_anomalies(df)
        
    quality_score = _calculate_quality_score(
        missing_count=total_missing,
        infinite_count=total_infinite,
        duplicate_count=duplicate_count,
        total_rows=total_rows,
        anomalies_count=len(anomalies["negative_value_violations"]),
    )

    return {
        "context_name": context_name,
        "total_rows": total_rows,
        "total_columns": total_cols,
        "memory_mb": memory_mb,
        "total_missing_values": total_missing,
        "rows_with_missing": rows_with_missing,
        "columns_with_missing": cols_with_missing,
        "empty_columns": empty_columns,
        "total_infinite_values": total_infinite,
        "pos_inf_count": pos_inf_count,
        "neg_inf_count": neg_inf_count,
        "columns_with_infinite": cols_with_infinite,
        "duplicate_rows": duplicate_count,
        "duplicate_percentage": duplicate_ratio,
        "duplicate_column_names": duplicate_column_names,
        "dtypes": {str(k): str(v) for k, v in df.dtypes.to_dict().items()},
        "numeric_column_count": len(numeric_df.columns),
        "target_summary": target_summary,
        "numerical_anomalies": anomalies,
        "quality_score": quality_score,
    }


def _calculate_quality_score(
    missing_count: int,
    infinite_count: int,
    duplicate_count: int,
    total_rows: int,
    anomalies_count: int = 0,
) -> float:
    """Computes an algorithmic data quality index between 0.0 and 100.0."""
    if total_rows == 0:
        return 0.0
    # Penalty weightings
    missing_penalty = min(30.0, (missing_count / total_rows) * 100 * 2.0)
    inf_penalty = min(30.0, (infinite_count / total_rows) * 100 * 5.0)
    dup_penalty = min(30.0, (duplicate_count / total_rows) * 100 * 1.0)
    anomaly_penalty = min(10.0, anomalies_count * 2.0)
    
    score = 100.0 - (missing_penalty + inf_penalty + dup_penalty + anomaly_penalty)
    return round(max(0.0, score), 1)


def export_quality_report(
    report: Dict[str, Any],
    output_path: Union[str, Path],
    format: str = "json",
) -> Path:
    """Exports structured quality audit report to disk in JSON or CSV format."""
    p = Path(output_path)
    ensure_directory(p.parent)
    fmt = format.lower()

    if fmt == "json":
        if not p.suffix.endswith(".json"):
            p = p.with_suffix(".json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
    elif fmt == "csv":
        if not p.suffix.endswith(".csv"):
            p = p.with_suffix(".csv")
        # Flatten top-level metrics for tabular display
        flat_data = {
            "Metric": [
                "Dataset Context",
                "Total Rows",
                "Total Columns",
                "Memory (MB)",
                "Quality Score",
                "Missing Values",
                "Rows with Missing",
                "Infinite Values",
                "Duplicate Rows",
                "Duplicate Percentage",
            ],
            "Value": [
                report.get("context_name", "N/A"),
                report.get("total_rows", 0),
                report.get("total_columns", 0),
                report.get("memory_mb", 0.0),
                report.get("quality_score", 0.0),
                report.get("total_missing_values", 0),
                report.get("rows_with_missing", 0),
                report.get("total_infinite_values", 0),
                report.get("duplicate_rows", 0),
                report.get("duplicate_percentage", 0.0),
            ],
        }
        pd.DataFrame(flat_data).to_csv(p, index=False)
    else:
        raise ValueError(f"Unsupported report format: {format}")

    logger.info(f"Saved quality report ({fmt.upper()}): {p}")
    return p


def generate_all_data_quality_reports(
    df: pd.DataFrame,
    inventory_dict: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Union[str, Path]] = None,
    target_col: str = "label",
) -> Dict[str, Path]:
    """Generates and writes all 6 standardized data quality reports to disk:
    1. dataset_inventory.json
    2. data_quality_report.json
    3. missing_values.csv
    4. duplicate_analysis.json
    5. label_distribution.csv
    6. data_quality_summary.csv

    Args:
        df: Input DataFrame to audit and document.
        inventory_dict: Optional precomputed inventory dictionary.
        output_dir: Destination folder (defaults to DATA_QUALITY_REPORTS_DIR).
        target_col: Canonical target column name.

    Returns:
        Dictionary mapping report identifiers to generated Path objects.
    """
    out_path = Path(output_dir) if output_dir else DATA_QUALITY_REPORTS_DIR
    ensure_directory(out_path)

    # 1. Dataset Inventory JSON
    inv_path = out_path / "dataset_inventory.json"
    if inventory_dict is None:
        inventory_dict = inspect_dataset_inventory()
    with open(inv_path, "w", encoding="utf-8") as f:
        json.dump(inventory_dict, f, indent=2, default=str)

    # Compute audit
    audit = audit_dataframe_quality(df, target_col=target_col)

    # 2. Exhaustive Data Quality Report JSON
    quality_json_path = out_path / "data_quality_report.json"
    with open(quality_json_path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, default=str)

    # 3. Missing Values CSV
    missing_csv_path = out_path / "missing_values.csv"
    missing_series = df.isna().sum()
    total_len = max(1, len(df))
    missing_df = pd.DataFrame({
        "column_name": missing_series.index,
        "missing_count": missing_series.values,
        "missing_percentage": ((missing_series.values / total_len) * 100).round(4),
        "dtype": [str(df[col].dtype) for col in missing_series.index],
    }).sort_values(by="missing_count", ascending=False)
    missing_df.to_csv(missing_csv_path, index=False)

    # 4. Duplicate Analysis JSON
    dup_json_path = out_path / "duplicate_analysis.json"
    dup_count = audit.get("duplicate_rows", 0)
    dup_pct = audit.get("duplicate_percentage", 0.0)
    dup_cols = audit.get("duplicate_column_names", [])
    dup_report = {
        "total_records": len(df),
        "exact_duplicate_rows": dup_count,
        "duplicate_percentage": dup_pct,
        "duplicate_column_names": dup_cols,
        "impact_assessment": (
            "Exact duplicate network flow records artificially inflate evaluation metrics "
            "if randomly partitioned across train and test sets (data leakage). "
            "Deduplication is recommended prior to model training."
            if dup_count > 0
            else "No exact duplicate records detected."
        ),
        "deduplication_recommended": dup_count > 0,
    }
    with open(dup_json_path, "w", encoding="utf-8") as f:
        json.dump(dup_report, f, indent=2, default=str)

    # 5. Label Distribution CSV
    label_csv_path = out_path / "label_distribution.csv"
    tgt_info = audit.get("target_summary", {})
    multiclass_dist = tgt_info.get("multiclass_distribution", {})
    if multiclass_dist:
        records = []
        for label_name, count in multiclass_dist.items():
            pct = round((count / total_len) * 100, 4)
            cat = "Benign" if "benign" in str(label_name).lower() else "Attack"
            records.append({
                "attack_class": str(label_name),
                "count": count,
                "percentage": pct,
                "binary_category": cat,
            })
        label_df = pd.DataFrame(records).sort_values(by="count", ascending=False)
    else:
        label_df = pd.DataFrame(columns=["attack_class", "count", "percentage", "binary_category"])
    label_df.to_csv(label_csv_path, index=False)

    # 6. Data Quality Summary CSV
    summary_csv_path = out_path / "data_quality_summary.csv"
    anomalies = audit.get("numerical_anomalies", {})
    neg_viol_count = len(anomalies.get("negative_value_violations", {}))
    const_cols = len(anomalies.get("constant_columns", []))
    q_score = audit.get("quality_score", 100.0)

    summary_rows = [
        {"Metric": "Total Analyzed Rows", "Value": str(len(df)), "Status": "INFO"},
        {"Metric": "Total Columns", "Value": str(len(df.columns)), "Status": "INFO"},
        {"Metric": "Memory Footprint (MB)", "Value": str(audit.get("memory_mb", 0.0)), "Status": "INFO"},
        {
            "Metric": "Data Quality Score",
            "Value": f"{q_score}/100.0",
            "Status": "OPTIMAL" if q_score >= 90 else ("ACCEPTABLE" if q_score >= 70 else "CRITICAL"),
        },
        {
            "Metric": "Total Missing Cells",
            "Value": str(audit.get("total_missing_values", 0)),
            "Status": "OK" if audit.get("total_missing_values", 0) == 0 else "WARNING",
        },
        {
            "Metric": "Total Infinite Values",
            "Value": str(audit.get("total_infinite_values", 0)),
            "Status": "OK" if audit.get("total_infinite_values", 0) == 0 else "CRITICAL",
        },
        {
            "Metric": "Exact Duplicate Rows",
            "Value": f"{dup_count} ({dup_pct}%)",
            "Status": "OK" if dup_count == 0 else "WARNING",
        },
        {
            "Metric": "Negative Non-Negative Features",
            "Value": str(neg_viol_count),
            "Status": "OK" if neg_viol_count == 0 else "WARNING",
        },
        {
            "Metric": "Zero Variance (Constant) Columns",
            "Value": str(const_cols),
            "Status": "OK" if const_cols == 0 else "NOTICE",
        },
    ]
    pd.DataFrame(summary_rows).to_csv(summary_csv_path, index=False)

    logger.info(f"Generated all 6 data quality reports in {out_path}")
    return {
        "inventory": inv_path,
        "quality_report": quality_json_path,
        "missing_values": missing_csv_path,
        "duplicate_analysis": dup_json_path,
        "label_distribution": label_csv_path,
        "quality_summary": summary_csv_path,
    }

