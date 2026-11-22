"""Correlation analysis and collinearity detection."""

from typing import Tuple, List, Dict, Any
import pandas as pd
import numpy as np


def compute_correlation_matrix(
    df: pd.DataFrame,
    method: str = "pearson",
    max_features: int = 40,
) -> pd.DataFrame:
    """Computes correlation matrix for numeric features, limiting feature count for performance."""
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        return pd.DataFrame()
        
    # Drop constant features before calculating correlation
    valid_cols = [c for c in numeric_df.columns if numeric_df[c].nunique() > 1]
    if not valid_cols:
        return pd.DataFrame()
        
    if len(valid_cols) > max_features:
        # Prioritize features with higher overall variance
        variances = numeric_df[valid_cols].var().sort_values(ascending=False)
        selected_cols = variances.head(max_features).index.tolist()
    else:
        selected_cols = valid_cols
        
    return numeric_df[selected_cols].corr(method=method).round(4)


def find_high_correlation_pairs(
    corr_matrix: pd.DataFrame,
    threshold: float = 0.90,
) -> List[Dict[str, Any]]:
    """Identifies feature pairs with absolute correlation above threshold (multicollinearity risk)."""
    if corr_matrix.empty:
        return []
        
    pairs = []
    cols = corr_matrix.columns
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            col1 = cols[i]
            col2 = cols[j]
            val = corr_matrix.loc[col1, col2]
            if abs(val) >= threshold:
                pairs.append({
                    "feature_1": col1,
                    "feature_2": col2,
                    "correlation": round(float(val), 4),
                    "abs_correlation": round(abs(float(val)), 4),
                })
                
    pairs.sort(key=lambda x: x["abs_correlation"], reverse=True)
    return pairs
