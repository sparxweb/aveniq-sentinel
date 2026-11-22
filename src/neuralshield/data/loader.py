"""Memory-conscious CSV ingestion engine for network flow datasets."""

from pathlib import Path
from typing import Optional, Union, Generator, List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from neuralshield.utils.file_utils import safe_read_csv, get_file_size_mb
from config.logging_config import get_logger

logger = get_logger("data.loader")

# Threshold in MB for triggering memory-warning logs
LARGE_FILE_THRESHOLD_MB = 100.0


def downcast_numeric_dtypes(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """Downcasts float64 to float32 and int64 to int32/int16 where lossless,
    reducing memory consumption by 40-60%.
    
    Returns:
        (downcasted_df, memory_metrics_dict)
    """
    initial_mem_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    df_opt = df.copy()

    for col in df_opt.select_dtypes(include=["float64"]).columns:
        df_opt[col] = pd.to_numeric(df_opt[col], downcast="float")

    for col in df_opt.select_dtypes(include=["int64"]).columns:
        df_opt[col] = pd.to_numeric(df_opt[col], downcast="integer")

    final_mem_mb = df_opt.memory_usage(deep=True).sum() / (1024 * 1024)
    reduction_pct = round((1.0 - (final_mem_mb / max(initial_mem_mb, 1e-6))) * 100.0, 1)

    metrics = {
        "initial_memory_mb": round(initial_mem_mb, 2),
        "optimized_memory_mb": round(final_mem_mb, 2),
        "reduction_percentage": reduction_pct,
    }
    return df_opt, metrics


def sample_dataframe(
    df: pd.DataFrame,
    n: Optional[int] = None,
    frac: Optional[float] = None,
    random_state: int = 42,
    stratify_col: Optional[str] = None,
) -> pd.DataFrame:
    """Deterministically samples a DataFrame for memory-efficient visualizations.
    Supports stratified sampling across label classes when feasible.
    """
    if df.empty or (n is None and frac is None):
        return df

    total_rows = len(df)
    if n is not None and n >= total_rows:
        return df

    # Check if stratified sampling is possible
    if stratify_col and stratify_col in df.columns:
        try:
            # Check if each class has at least 2 samples
            counts = df[stratify_col].value_counts()
            if (counts >= 2).all():
                # Perform grouped sampling maintaining class balance
                if frac is None and n is not None:
                    frac = min(1.0, max(0.001, n / total_rows))
                return (
                    df.groupby(stratify_col, group_keys=False)
                    .apply(lambda grp: grp.sample(frac=frac, random_state=random_state), include_groups=False)
                )
        except Exception as e:
            logger.debug(f"Stratified sampling fallback to standard random sample: {e}")

    # Standard deterministic random sample
    return df.sample(n=n, frac=frac, random_state=random_state)


class DatasetLoader:
    """Provides memory-conscious ingestion of CIC-IDS2017 flow datasets."""
    
    def __init__(self, chunk_size: int = 100_000, low_memory: bool = True):
        self.chunk_size = chunk_size
        self.low_memory = low_memory
        
    def load_single_file(
        self,
        file_path: Union[str, Path],
        nrows: Optional[int] = None,
        usecols: Optional[List[str]] = None,
        optimize_memory: bool = False,
    ) -> pd.DataFrame:
        """Loads a single CSV file, safely handling encodings, sizes, and malformed rows."""
        p = Path(file_path)
        sz_mb = get_file_size_mb(p)
        if sz_mb >= LARGE_FILE_THRESHOLD_MB:
            logger.warning(
                f"File {p.name} is large ({sz_mb:.2f} MB). "
                f"Consider chunked processing or setting nrows/usecols."
            )
        else:
            logger.info(f"Loading CSV: {p.name} (File size: {sz_mb:.2f} MB)")
            
        df = safe_read_csv(p, nrows=nrows, usecols=usecols, low_memory=self.low_memory)
        if optimize_memory:
            df, _ = downcast_numeric_dtypes(df)
            
        logger.info(f"Loaded {len(df):,} rows x {len(df.columns)} columns from {p.name}")
        return df
        
    def stream_chunks(
        self,
        file_path: Union[str, Path],
        usecols: Optional[List[str]] = None,
    ) -> Generator[pd.DataFrame, None, None]:
        """Streams a large CSV file in configurable chunks for memory-constrained environments."""
        p = Path(file_path)
        logger.info(f"Streaming {p.name} in chunks of {self.chunk_size:,} rows")
        for chunk in pd.read_csv(
            p,
            chunksize=self.chunk_size,
            usecols=usecols,
            low_memory=self.low_memory,
            on_bad_lines="skip",
        ):
            yield chunk
            
    def load_multiple_files(
        self,
        file_paths: List[Union[str, Path]],
        max_rows_per_file: Optional[int] = None,
        usecols: Optional[List[str]] = None,
        optimize_memory: bool = False,
    ) -> pd.DataFrame:
        """Loads and concatenates multiple CSV files safely."""
        frames = []
        for fp in file_paths:
            df = self.load_single_file(
                fp,
                nrows=max_rows_per_file,
                usecols=usecols,
                optimize_memory=optimize_memory,
            )
            frames.append(df)
            
        if not frames:
            return pd.DataFrame()
        combined = pd.concat(frames, ignore_index=True)
        logger.info(f"Combined {len(file_paths)} files: {len(combined):,} total rows")
        return combined
