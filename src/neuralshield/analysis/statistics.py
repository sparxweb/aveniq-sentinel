"""Statistical summary computations and feature descriptive metrics."""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from config.logging_config import get_logger

logger = get_logger("analysis.statistics")


def compute_descriptive_statistics(
    df: pd.DataFrame,
    features: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Computes extended summary statistics for numeric features:
    mean, std, min, 25%, median, 75%, max, skewness, kurtosis, and zero-variance flag.
    """
    numeric_df = df.select_dtypes(include=[np.number])
    if features:
        cols = [c for c in features if c in numeric_df.columns]
        numeric_df = numeric_df[cols]
        
    if numeric_df.empty:
        return pd.DataFrame()
        
    desc = numeric_df.describe().T
    desc["variance"] = numeric_df.var()
    desc["skewness"] = numeric_df.skew()
    desc["kurtosis"] = numeric_df.kurtosis()
    desc["missing_count"] = numeric_df.isna().sum()
    desc["zero_variance"] = desc["variance"] == 0.0
    
    return desc.round(4)


def identify_constant_features(df: pd.DataFrame) -> List[str]:
    """Finds features that have zero variance or only a single unique value."""
    constant_cols = []
    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].nunique(dropna=False) <= 1 or df[col].var() == 0:
            constant_cols.append(col)
    return constant_cols
