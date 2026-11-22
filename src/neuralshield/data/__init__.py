"""Data engineering, discovery, schema validation, and preprocessing pipeline exports."""

from neuralshield.data.discovery import (
    discover_csv_files,
    inspect_dataset_inventory,
    STATUS_DIR_UNAVAILABLE,
    STATUS_DIR_EMPTY,
    STATUS_BENCHMARK_PARTIAL,
    STATUS_BENCHMARK_COMPLETE,
)
from neuralshield.data.schema import inspect_csv_schema, compare_schemas
from neuralshield.data.loader import DatasetLoader, downcast_numeric_dtypes, sample_dataframe
from neuralshield.data.cleaning import (
    normalize_column_names,
    identify_and_drop_redundant_columns,
    sanitize_infinite_and_nan,
    handle_duplicates,
    normalize_labels,
)
from neuralshield.data.validation import (
    audit_dataframe_quality,
    inspect_numerical_anomalies,
    export_quality_report,
)
from neuralshield.data.preprocessing import PreprocessingPipeline

__all__ = [
    "discover_csv_files",
    "inspect_dataset_inventory",
    "STATUS_DIR_UNAVAILABLE",
    "STATUS_DIR_EMPTY",
    "STATUS_BENCHMARK_PARTIAL",
    "STATUS_BENCHMARK_COMPLETE",
    "inspect_csv_schema",
    "compare_schemas",
    "DatasetLoader",
    "downcast_numeric_dtypes",
    "sample_dataframe",
    "normalize_column_names",
    "identify_and_drop_redundant_columns",
    "sanitize_infinite_and_nan",
    "handle_duplicates",
    "normalize_labels",
    "audit_dataframe_quality",
    "inspect_numerical_anomalies",
    "export_quality_report",
    "PreprocessingPipeline",
]
