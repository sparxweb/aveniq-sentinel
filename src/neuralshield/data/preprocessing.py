"""End-to-end preprocessing pipeline with full audit logging and artifact export."""

from pathlib import Path
from typing import Dict, Any, Optional, Union
import pandas as pd
from config.settings import ProcessingConfig, PROCESSED_DATA_DIR, DATA_QUALITY_REPORTS_DIR
from neuralshield.data.cleaning import (
    normalize_column_names,
    identify_and_drop_redundant_columns,
    sanitize_infinite_and_nan,
    handle_duplicates,
    normalize_labels,
)
from neuralshield.features.engineering import remove_target_leakage_features
from neuralshield.data.validation import audit_dataframe_quality
from neuralshield.utils.file_utils import safe_write_df, ensure_directory
from config.logging_config import get_logger

logger = get_logger("data.preprocessing")


class PreprocessingPipeline:
    """Configurable, leakage-safe dataset preparation pipeline."""
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        self.config = config or ProcessingConfig()
        
    def fit_transform(
        self,
        raw_df: pd.DataFrame,
        dataset_name: str = "Dataset",
    ) -> Dict[str, Any]:
        """Executes full cleaning pipeline, recording transformation metrics.
        
        Returns:
            Dict containing:
                - 'cleaned_df': Preprocessed DataFrame
                - 'audit_report': Complete metrics dictionary
                - 'initial_shape': (rows, cols)
                - 'final_shape': (rows, cols)
        """
        logger.info(f"Initiating pipeline for '{dataset_name}' with {len(raw_df):,} initial rows")
        initial_shape = raw_df.shape
        
        # 1. Normalize Column Names
        df_norm, col_mapping = normalize_column_names(raw_df)
        
        # 2. Identify & Drop Redundant Columns (e.g. duplicate Fwd Header Length)
        dropped_cols = []
        if self.config.drop_redundant_columns:
            df_norm, dropped_cols = identify_and_drop_redundant_columns(df_norm)

        # 2b. Remove Target Leakage Identifiers (Flow ID, Source IP, Destination IP, Timestamp)
        leakage_dropped = []
        if getattr(self.config, "drop_leakage_columns", True):
            df_norm, leakage_dropped = remove_target_leakage_features(df_norm)
            
        # 3. Detect and Sanitize Infinite and NaN values
        inf_stats = {"pos_inf_count": 0, "neg_inf_count": 0, "nan_initial_count": 0}
        if self.config.handle_infinities:
            df_norm, inf_stats = sanitize_infinite_and_nan(df_norm, replace_strategy="nan")
            
        # 4. Handle Exact Duplicates
        duplicates_dropped = 0
        if self.config.drop_exact_duplicates:
            df_norm, duplicates_dropped = handle_duplicates(df_norm)
            
        # 5. Normalize Target Labels
        label_audit = {}
        target_col = self.config.target_column
        df_norm, label_audit = normalize_labels(df_norm, target_col=target_col)
        
        final_shape = df_norm.shape
        
        # 6. Comprehensive Quality Validation Audit
        quality_audit = audit_dataframe_quality(
            df_norm,
            target_col=target_col,
            context_name=dataset_name,
        )
        
        pipeline_report = {
            "dataset_name": dataset_name,
            "initial_rows": initial_shape[0],
            "initial_columns": initial_shape[1],
            "final_rows": final_shape[0],
            "final_columns": final_shape[1],
            "dropped_columns": dropped_cols,
            "leakage_dropped": leakage_dropped,
            "duplicates_removed": duplicates_dropped,
            "infinite_stats": inf_stats,
            "label_audit": label_audit,
            "quality_audit": quality_audit,
        }
        
        logger.info(
            f"Pipeline complete: {initial_shape} -> {final_shape}. "
            f"Quality Score: {quality_audit['quality_score']}/100"
        )
        
        return {
            "cleaned_df": df_norm,
            "audit_report": pipeline_report,
            "initial_shape": initial_shape,
            "final_shape": final_shape,
        }

    def export_cleaned_dataset(
        self,
        df: pd.DataFrame,
        filename: str,
        output_dir: Union[str, Path] = PROCESSED_DATA_DIR,
        format: Optional[str] = None,
    ) -> Path:
        """Exports preprocessed data to disk with Parquet or CSV."""
        fmt = format or self.config.export_format
        dest_dir = ensure_directory(output_dir)
        dest_path = dest_dir / filename
        return safe_write_df(df, dest_path, format=fmt)
