"""Distribution analysis for flow durations, packet sizes, and class balance."""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


def analyze_class_balance(df: pd.DataFrame, target_col: str = "label") -> Dict[str, Any]:
    """Calculates class frequencies, percentages, and minority-to-majority ratio."""
    found = None
    for c in df.columns:
        if c.strip().lower() == target_col.strip().lower():
            found = c
            break
            
    if not found or found not in df.columns:
        return {"error": f"Target column '{target_col}' not found"}
        
    counts = df[found].value_counts()
    percentages = (df[found].value_counts(normalize=True) * 100).round(3)
    
    majority_class = counts.index[0]
    minority_class = counts.index[-1]
    imbalance_ratio = round(counts.iloc[0] / max(1, counts.iloc[-1]), 2)
    
    return {
        "target_column": found,
        "total_samples": len(df),
        "class_counts": counts.to_dict(),
        "class_percentages": percentages.to_dict(),
        "majority_class": majority_class,
        "minority_class": minority_class,
        "imbalance_ratio": imbalance_ratio,
        "is_severely_imbalanced": imbalance_ratio > 10.0,
    }


def compute_feature_quantiles(
    df: pd.DataFrame,
    feature: str,
    quantiles: Optional[list] = None,
) -> Dict[str, float]:
    """Computes percentile breakdown for a specific feature."""
    if feature not in df.columns or not pd.api.types.is_numeric_dtype(df[feature]):
        return {}
        
    q_list = quantiles or [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
    q_vals = df[feature].quantile(q_list).to_dict()
    return {f"{int(k*100)}%": round(float(v), 4) for k, v in q_vals.items()}
