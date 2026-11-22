"""Data validation routines and integrity checks."""

from typing import List, Tuple, Optional
import pandas as pd
import numpy as np


class ValidationError(ValueError):
    """Custom exception raised when data validation fails."""
    pass


def validate_dataframe_not_empty(df: pd.DataFrame, context: str = "Dataset") -> None:
    """Verifies that a dataframe contains at least one row and column."""
    if df is None:
        raise ValidationError(f"{context} is None.")
    if df.empty:
        raise ValidationError(f"{context} is empty (0 rows or 0 columns).")
    if len(df.columns) == 0:
        raise ValidationError(f"{context} has no columns.")


def validate_target_column_present(df: pd.DataFrame, target_col: str = "label") -> str:
    """Finds or validates the target label column case-insensitively.
    
    Returns:
        Actual column name present in DataFrame.
    Raises:
        ValidationError: If target column cannot be resolved.
    """
    validate_dataframe_not_empty(df, "Target validation")
    target_lower = target_col.strip().lower()
    for col in df.columns:
        if str(col).strip().lower() == target_lower:
            return col
    raise ValidationError(
        f"Target column '{target_col}' not found in DataFrame columns: {list(df.columns[:10])}..."
    )


def validate_numeric_features(df: pd.DataFrame, exclude_cols: Optional[List[str]] = None) -> List[str]:
    """Identifies and returns all numeric feature columns."""
    exclude = set(exclude_cols or [])
    numeric_cols = [
        col for col in df.columns
        if col not in exclude and pd.api.types.is_numeric_dtype(df[col])
    ]
    return numeric_cols


def validate_finite_values(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Tuple[bool, int]:
    """Checks whether the specified columns contain infinite values.
    
    Returns:
        (is_finite, infinite_value_count)
    """
    cols = columns if columns is not None else df.select_dtypes(include=[np.number]).columns
    if len(cols) == 0:
        return True, 0
    sub_df = df[cols]
    inf_mask = np.isinf(sub_df.to_numpy())
    inf_count = int(np.sum(inf_mask))
    return inf_count == 0, inf_count
