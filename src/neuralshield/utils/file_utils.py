"""Safe file handling, path management and I/O utilities."""

import os
from pathlib import Path
from typing import Optional, Union, List
import pandas as pd
from config.logging_config import get_logger

logger = get_logger("utils.file_utils")


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensures a directory exists, creating parent directories if necessary."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_file_size_mb(path: Union[str, Path]) -> float:
    """Returns file size in megabytes."""
    p = Path(path)
    if not p.is_file():
        return 0.0
    return p.stat().st_size / (1024 * 1024)


def detect_file_encoding(path: Union[str, Path], sample_bytes: int = 100_000) -> str:
    """Detects encoding by testing standard encodings against sample bytes."""
    p = Path(path)
    if not p.is_file():
        return "utf-8"
        
    encodings_to_try = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
    with open(p, "rb") as f:
        raw_sample = f.read(sample_bytes)
        
    for enc in encodings_to_try:
        try:
            raw_sample.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
            
    return "latin-1"  # Latin-1 accepts any byte sequence safely


def safe_read_csv(
    path: Union[str, Path],
    nrows: Optional[int] = None,
    encoding: Optional[str] = None,
    low_memory: bool = True,
    **kwargs,
) -> pd.DataFrame:
    """Safely loads a CSV with automated encoding fallback."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"File not found: {p}")
        
    enc = encoding or detect_file_encoding(p)
    logger.debug(f"Reading CSV {p.name} with encoding={enc}")
    
    try:
        return pd.read_csv(p, nrows=nrows, encoding=enc, low_memory=low_memory, **kwargs)
    except UnicodeDecodeError:
        logger.warning(f"Decoding failed with {enc}; falling back to 'latin-1'")
        return pd.read_csv(p, nrows=nrows, encoding="latin-1", low_memory=low_memory, **kwargs)


def safe_write_df(
    df: pd.DataFrame,
    destination: Union[str, Path],
    format: str = "parquet",
) -> Path:
    """Writes a DataFrame to disk using Parquet or CSV format."""
    dest = Path(destination)
    ensure_directory(dest.parent)
    
    fmt = format.lower()
    if fmt == "parquet":
        if not dest.suffix.endswith(".parquet"):
            dest = dest.with_suffix(".parquet")
        df.to_parquet(dest, index=False, engine="pyarrow")
        logger.info(f"Saved Parquet file: {dest} ({get_file_size_mb(dest):.2f} MB)")
    elif fmt == "csv":
        if not dest.suffix.endswith(".csv"):
            dest = dest.with_suffix(".csv")
        df.to_csv(dest, index=False)
        logger.info(f"Saved CSV file: {dest} ({get_file_size_mb(dest):.2f} MB)")
    else:
        raise ValueError(f"Unsupported format '{format}'. Use 'parquet' or 'csv'.")
        
    return dest
