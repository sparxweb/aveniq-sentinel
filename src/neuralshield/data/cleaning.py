"""Data cleaning, normalization, duplicate handling and infinity sanitation."""

from typing import Dict, Any, Tuple, List, Optional
import pandas as pd
import numpy as np
from config.settings import ATTACK_TAXONOMY, REDUNDANT_COLUMNS
from config.logging_config import get_logger

logger = get_logger("data.cleaning")


def normalize_column_names(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Strips whitespace, replaces special characters, and converts column headers to snake_case.
    
    Returns:
        (renamed_dataframe, mapping_of_original_to_normalized)
    """
    column_mapping = {}
    new_columns = []
    
    for col in df.columns:
        clean_name = str(col).strip()
        # Canonical normalization: lower, replace spaces and slashes with underscores
        norm = (
            clean_name.lower()
            .replace(" /s", "_per_sec")
            .replace("/s", "_per_sec")
            .replace(" ", "_")
            .replace("-", "_")
            .replace("/", "_")
        )
        # Avoid double underscores
        while "__" in norm:
            norm = norm.replace("__", "_")
        column_mapping[col] = norm
        new_columns.append(norm)
        
    df_clean = df.copy()
    df_clean.columns = new_columns
    return df_clean, column_mapping


def identify_and_drop_redundant_columns(
    df: pd.DataFrame,
    verify_equality: bool = True
) -> Tuple[pd.DataFrame, List[str]]:
    """Identifies duplicate or redundant columns (such as Fwd Header Length.1)
    and removes them after optionally verifying value equivalence.
    
    Returns:
        (cleaned_dataframe, list_of_dropped_columns)
    """
    dropped = []
    df_clean = df.copy()
    cols = list(df_clean.columns)
    
    # 1. Check known redundant column names
    for col in cols:
        col_lower = col.strip().lower()
        if col in REDUNDANT_COLUMNS or col_lower in [c.lower() for c in REDUNDANT_COLUMNS]:
            dropped.append(col)
            
    # 2. Check for pandas auto-renamed duplicates (e.g. col.1)
    for col in cols:
        if col.endswith(".1") or col.endswith("_1"):
            base_col = col[:-2]
            if base_col in cols and col not in dropped:
                if verify_equality:
                    # Check if values actually match
                    series1 = df_clean[base_col]
                    series2 = df_clean[col]
                    if series1.equals(series2):
                        dropped.append(col)
                else:
                    dropped.append(col)
                    
    if dropped:
        logger.info(f"Removing verified redundant columns: {dropped}")
        df_clean = df_clean.drop(columns=dropped, errors="ignore")
        
    return df_clean, dropped


def sanitize_infinite_and_nan(
    df: pd.DataFrame,
    replace_strategy: str = "nan",
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """Detects positive and negative infinity values (frequent in Flow Bytes/s and Flow Packets/s),
    counts occurrences, and converts them to NaN or median imputed values.
    
    Returns:
        (sanitized_df, stats_dict)
    """
    df_clean = df.copy()
    stats = {"pos_inf_count": 0, "neg_inf_count": 0, "nan_initial_count": 0}
    
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        return df_clean, stats
        
    num_vals = df_clean[numeric_cols].to_numpy()
    pos_inf_mask = np.isneginf(num_vals) == False
    pos_inf_mask = np.isposinf(num_vals)
    neg_inf_mask = np.isneginf(num_vals)
    
    stats["pos_inf_count"] = int(np.sum(pos_inf_mask))
    stats["neg_inf_count"] = int(np.sum(neg_inf_mask))
    stats["nan_initial_count"] = int(df_clean.isna().sum().sum())
    
    # Replace infinite values with NaN
    df_clean[numeric_cols] = df_clean[numeric_cols].replace([np.inf, -np.inf], np.nan)
    
    if replace_strategy == "median":
        medians = df_clean[numeric_cols].median()
        df_clean[numeric_cols] = df_clean[numeric_cols].fillna(medians)
    elif replace_strategy == "drop":
        df_clean = df_clean.dropna(subset=numeric_cols)
        
    return df_clean, stats


def handle_duplicates(
    df: pd.DataFrame,
    subset: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, int]:
    """Identifies and drops exact duplicate records to prevent data leakage.
    
    Returns:
        (deduplicated_df, duplicates_removed_count)
    """
    initial_count = len(df)
    df_dedup = df.drop_duplicates(subset=subset)
    removed = initial_count - len(df_dedup)
    
    if removed > 0:
        logger.info(f"Dropped {removed:,} duplicate records ({removed/initial_count*100:.2f}%)")
    return df_dedup, removed


def normalize_labels(
    df: pd.DataFrame,
    target_col: str = "label",
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Standardizes target labels according to ATTACK_TAXONOMY, tracking remappings.
    
    Returns:
        (normalized_df, label_audit_report)
    """
    if target_col not in df.columns:
        # Try resolving case-insensitively
        found = None
        for c in df.columns:
            if c.strip().lower() == target_col.strip().lower():
                found = c
                break
        if not found:
            logger.warning(f"Target column '{target_col}' not found. Skipping label normalization.")
            return df, {}
        target_col = found
        
    df_clean = df.copy()
    raw_series = df_clean[target_col].astype(str).str.strip()
    raw_counts = raw_series.value_counts().to_dict()
    
    normalized_series = raw_series.map(lambda x: ATTACK_TAXONOMY.get(x, x))
    df_clean[target_col] = normalized_series
    
    norm_counts = df_clean[target_col].value_counts().to_dict()
    
    audit = {
        "target_column": target_col,
        "unique_raw_labels": len(raw_counts),
        "unique_normalized_labels": len(norm_counts),
        "raw_distribution": raw_counts,
        "normalized_distribution": norm_counts,
        "is_binary": len(norm_counts) <= 2,
    }
    return df_clean, audit
