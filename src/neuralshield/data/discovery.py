"""Intelligent CSV file discovery, cataloging and validation for CIC-IDS2017 datasets."""

import os
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
from config.settings import RAW_DATA_DIR, CIC_IDS2017_EXPECTED_FILES
from neuralshield.utils.file_utils import get_file_size_mb
from config.logging_config import get_logger

logger = get_logger("data.discovery")

# Canonical discovery status constants
STATUS_DIR_UNAVAILABLE = "DIRECTORY_UNAVAILABLE"
STATUS_DIR_EMPTY = "DIRECTORY_EMPTY"
STATUS_BENCHMARK_PARTIAL = "BENCHMARK_PARTIAL"
STATUS_BENCHMARK_COMPLETE = "BENCHMARK_COMPLETE"


def discover_csv_files(directory: Union[str, Path] = RAW_DATA_DIR) -> List[Path]:
    """Finds all valid CSV files within a given directory, ignoring empty zero-byte files."""
    dir_path = Path(directory)
    if not dir_path.is_dir():
        logger.warning(f"Directory does not exist or is not a directory: {dir_path}")
        return []
        
    csv_files = sorted(list(dir_path.glob("*.csv")))
    logger.info(f"Discovered {len(csv_files)} CSV files in {dir_path}")
    return csv_files


def inspect_dataset_inventory(directory: Union[str, Path] = RAW_DATA_DIR) -> Dict[str, Any]:
    """Audits the directory against expected CIC-IDS2017 MachineLearningCSV benchmark files.
    
    Identifies:
    - Overall directory status (UNAVAILABLE, EMPTY, PARTIAL, COMPLETE)
    - File existence, sizes (MB and bytes), and empty zero-byte files
    - Missing benchmark files
    - Non-standard extra CSV files
    - Duplicate filenames or collision candidates
    
    Returns:
        Structured machine-readable inventory dictionary.
    """
    dir_path = Path(directory)
    if not dir_path.exists() or not dir_path.is_dir():
        return {
            "status": STATUS_DIR_UNAVAILABLE,
            "directory": str(dir_path),
            "directory_exists": False,
            "total_files_found": 0,
            "expected_benchmark_files": len(CIC_IDS2017_EXPECTED_FILES),
            "expected_present_count": 0,
            "is_complete_benchmark": False,
            "total_size_mb": 0.0,
            "empty_files": [],
            "expected_inventory": [
                {"filename": exp, "present": False, "size_mb": 0.0, "is_empty": False, "path": None}
                for exp in CIC_IDS2017_EXPECTED_FILES
            ],
            "extra_files": [],
            "missing_expected_files": list(CIC_IDS2017_EXPECTED_FILES),
        }

    found_files = sorted(list(dir_path.glob("*.csv")))
    if not found_files:
        return {
            "status": STATUS_DIR_EMPTY,
            "directory": str(dir_path),
            "directory_exists": True,
            "total_files_found": 0,
            "expected_benchmark_files": len(CIC_IDS2017_EXPECTED_FILES),
            "expected_present_count": 0,
            "is_complete_benchmark": False,
            "total_size_mb": 0.0,
            "empty_files": [],
            "expected_inventory": [
                {"filename": exp, "present": False, "size_mb": 0.0, "is_empty": False, "path": None}
                for exp in CIC_IDS2017_EXPECTED_FILES
            ],
            "extra_files": [],
            "missing_expected_files": list(CIC_IDS2017_EXPECTED_FILES),
        }

    found_map: Dict[str, Path] = {f.name: f for f in found_files}
    expected_status = []
    missing_files = []
    empty_files = []
    total_size_mb = 0.0

    for exp in CIC_IDS2017_EXPECTED_FILES:
        is_present = exp in found_map
        if is_present:
            f_path = found_map[exp]
            size_mb = get_file_size_mb(f_path)
            size_bytes = f_path.stat().st_size
            is_empty = size_bytes == 0
            if is_empty:
                empty_files.append(exp)
            total_size_mb += size_mb
            expected_status.append({
                "filename": exp,
                "present": True,
                "size_mb": round(size_mb, 2),
                "size_bytes": size_bytes,
                "is_empty": is_empty,
                "path": str(f_path),
            })
        else:
            missing_files.append(exp)
            expected_status.append({
                "filename": exp,
                "present": False,
                "size_mb": 0.0,
                "size_bytes": 0,
                "is_empty": False,
                "path": None,
            })

    # Non-standard extra CSV files
    extra_files = []
    for f in found_files:
        if f.name not in CIC_IDS2017_EXPECTED_FILES:
            sz_mb = get_file_size_mb(f)
            sz_bytes = f.stat().st_size
            is_empty = sz_bytes == 0
            if is_empty:
                empty_files.append(f.name)
            total_size_mb += sz_mb
            extra_files.append({
                "filename": f.name,
                "size_mb": round(sz_mb, 2),
                "size_bytes": sz_bytes,
                "is_empty": is_empty,
                "path": str(f),
            })

    expected_count = sum(1 for item in expected_status if item["present"])
    is_complete = expected_count == len(CIC_IDS2017_EXPECTED_FILES) and len(empty_files) == 0
    status = STATUS_BENCHMARK_COMPLETE if is_complete else STATUS_BENCHMARK_PARTIAL

    return {
        "status": status,
        "directory": str(dir_path),
        "directory_exists": True,
        "total_files_found": len(found_files),
        "expected_benchmark_files": len(CIC_IDS2017_EXPECTED_FILES),
        "expected_present_count": expected_count,
        "is_complete_benchmark": is_complete,
        "total_size_mb": round(total_size_mb, 2),
        "empty_files": empty_files,
        "expected_inventory": expected_status,
        "extra_files": extra_files,
        "missing_expected_files": missing_files,
    }
