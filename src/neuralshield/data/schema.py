"""Cross-file schema validation, schema consistency scoring, and drift detection."""

from pathlib import Path
from typing import List, Dict, Any, Union, Set
import pandas as pd
from neuralshield.utils.file_utils import safe_read_csv
from neuralshield.data.cleaning import normalize_column_names
from config.logging_config import get_logger

logger = get_logger("data.schema")


def inspect_csv_schema(file_path: Union[str, Path], sample_rows: int = 5) -> Dict[str, Any]:
    """Inspects header and initial dtypes of a CSV file without loading entire file into memory."""
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"File not found: {p}")
        
    df_sample = safe_read_csv(p, nrows=sample_rows)
    raw_columns = list(df_sample.columns)
    df_norm, col_mapping = normalize_column_names(df_sample)
    
    return {
        "filename": p.name,
        "raw_column_count": len(raw_columns),
        "raw_columns": raw_columns,
        "normalized_columns": list(df_norm.columns),
        "column_mapping": col_mapping,
        "dtypes": {c: str(df_sample[c].dtype) for c in raw_columns},
    }


def compare_schemas(file_paths: List[Union[str, Path]], sample_rows: int = 5) -> Dict[str, Any]:
    """Compares column schemas across multiple CSV files to detect schema drift,
    missing columns, or naming inconsistencies.
    
    Returns:
        Structured dictionary with common features, file-specific features,
        and an overall schema consistency index (0.0 to 100.0%).
    """
    if not file_paths:
        return {
            "total_files_compared": 0,
            "consistency_score": 100.0,
            "universal_columns": [],
            "discrepancies": [],
            "file_schemas": {},
        }

    schemas: Dict[str, Dict[str, Any]] = {}
    normalized_sets: List[Set[str]] = []

    for fp in file_paths:
        p = Path(fp)
        try:
            sch = inspect_csv_schema(p, sample_rows=sample_rows)
            schemas[p.name] = sch
            normalized_sets.append(set(sch["normalized_columns"]))
        except Exception as e:
            logger.warning(f"Failed to inspect schema for {p.name}: {e}")
            schemas[p.name] = {"error": str(e), "normalized_columns": []}

    valid_sets = [s for s in normalized_sets if s]
    if not valid_sets:
        return {
            "total_files_compared": len(file_paths),
            "consistency_score": 0.0,
            "universal_columns": [],
            "discrepancies": ["No valid schemas could be read"],
            "file_schemas": schemas,
        }

    # Universal features present in all files
    universal_cols = sorted(list(set.intersection(*valid_sets)))
    # Union of all features across any file
    all_cols = sorted(list(set.union(*valid_sets)))

    discrepancies = []
    for fname, sch in schemas.items():
        if "error" in sch:
            continue
        f_cols = set(sch["normalized_columns"])
        missing_from_file = sorted(list(set(all_cols) - f_cols))
        if missing_from_file:
            discrepancies.append({
                "filename": fname,
                "missing_columns_count": len(missing_from_file),
                "missing_columns": missing_from_file[:10],
            })

    # Consistency score calculation
    if all_cols:
        consistency_score = round((len(universal_cols) / len(all_cols)) * 100.0, 2)
    else:
        consistency_score = 100.0

    return {
        "total_files_compared": len(file_paths),
        "total_unique_columns_observed": len(all_cols),
        "universal_columns_count": len(universal_cols),
        "universal_columns": universal_cols,
        "consistency_score": consistency_score,
        "discrepancies": discrepancies,
        "file_schemas": schemas,
    }
