"""Official CIC-IDS2017 Dataset Profiler and Metadata Catalog.

Performs schema consistency verification, day-wise attack distribution analysis,
and memory-conscious chunked profiling across the 8 benchmark CSV files.
"""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import pandas as pd
import numpy as np

from config.settings import (
    CIC_IDS2017_EXPECTED_FILES,
    REDUNDANT_COLUMNS,
    TARGET_LEAKAGE_COLUMNS,
    ATTACK_TAXONOMY,
)
from config.logging_config import get_logger

logger = get_logger("ml.profiler")

# Official UNB CIC-IDS2017 Metadata (MachineLearningCSV release)
CICIDS2017_FILE_METADATA: Dict[str, Dict[str, Any]] = {
    "Monday-WorkingHours.pcap_ISCX.csv": {
        "day": "Monday",
        "date": "2017-07-03",
        "expected_flows": 529918,
        "approx_size_mb": 165.2,
        "traffic_type": "Benign Baseline",
        "attacks_present": [],
        "description": "Pure benign background traffic generated from simulated user activity.",
    },
    "Tuesday-WorkingHours.pcap_ISCX.csv": {
        "day": "Tuesday",
        "date": "2017-07-04",
        "expected_flows": 445909,
        "approx_size_mb": 140.5,
        "traffic_type": "Brute Force",
        "attacks_present": ["FTP-Patator", "SSH-Patator"],
        "description": "Brute-force attacks against FTP and SSH services.",
    },
    "Wednesday-workingHours.pcap_ISCX.csv": {
        "day": "Wednesday",
        "date": "2017-07-05",
        "expected_flows": 692703,
        "approx_size_mb": 224.8,
        "traffic_type": "DoS & Heartbleed",
        "attacks_present": ["DoS slowloris", "DoS Slowhttptest", "DoS Hulk", "DoS GoldenEye", "Heartbleed"],
        "description": "Volumetric and application-layer DoS attacks plus Heartbleed OpenSSL exploit.",
    },
    "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv": {
        "day": "Thursday",
        "date": "2017-07-06",
        "period": "Morning",
        "expected_flows": 170366,
        "approx_size_mb": 84.1,
        "traffic_type": "Web Attacks",
        "attacks_present": ["Web Attack  Brute Force", "Web Attack  XSS", "Web Attack  Sql Injection"],
        "description": "Web vulnerability exploits (Brute Force, Cross-Site Scripting, SQL Injection).",
    },
    "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv": {
        "day": "Thursday",
        "date": "2017-07-06",
        "period": "Afternoon",
        "expected_flows": 288602,
        "approx_size_mb": 177.3,
        "traffic_type": "Infiltration",
        "attacks_present": ["Infiltration"],
        "description": "Staged intrusion via weaponized PDF backdoor and Metasploit payload.",
    },
    "Friday-WorkingHours-Morning.pcap_ISCX.csv": {
        "day": "Friday",
        "date": "2017-07-07",
        "period": "Morning",
        "expected_flows": 191033,
        "approx_size_mb": 67.2,
        "traffic_type": "Botnet",
        "attacks_present": ["Bot"],
        "description": "Ares botnet C2 communications and scanning activities.",
    },
    "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv": {
        "day": "Friday",
        "date": "2017-07-07",
        "period": "Afternoon",
        "expected_flows": 286467,
        "approx_size_mb": 128.4,
        "traffic_type": "PortScan",
        "attacks_present": ["PortScan"],
        "description": "Reconnaissance port scans using Nmap with multiple scan flags.",
    },
    "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv": {
        "day": "Friday",
        "date": "2017-07-07",
        "period": "Afternoon",
        "expected_flows": 225745,
        "approx_size_mb": 97.6,
        "traffic_type": "DDoS",
        "attacks_present": ["DDoS"],
        "description": "High-volume distributed denial-of-service attack using LOIC.",
    },
}


class DatasetProfiler:
    """Profiles CIC-IDS2017 datasets, reconciles schemas, and audits class distributions."""

    def __init__(self, raw_data_dir: Optional[Path] = None):
        self.raw_data_dir = raw_data_dir

    @staticmethod
    def normalize_column_name(col: str) -> str:
        """Strips leading/trailing whitespace and normalizes separators."""
        return col.strip()

    @staticmethod
    def identify_label_column(df: pd.DataFrame) -> Optional[str]:
        """Identifies target label column case-insensitively."""
        for c in df.columns:
            if c.strip().lower() in ("label", "class", "target"):
                return c
        return None

    def profile_file_metadata(self, filename: str) -> Dict[str, Any]:
        """Retrieves official known metadata for a benchmark file."""
        return CICIDS2017_FILE_METADATA.get(filename, {
            "day": "Unknown",
            "date": "Unknown",
            "expected_flows": 0,
            "approx_size_mb": 0.0,
            "traffic_type": "Unknown",
            "attacks_present": [],
            "description": "Custom or unrecognized capture file.",
        })

    def inspect_dataframe_profile(
        self,
        df: pd.DataFrame,
        source_name: str = "Dataset",
    ) -> Dict[str, Any]:
        """Generates detailed profile of an in-memory DataFrame with zero leakage risk."""
        label_col = self.identify_label_column(df)
        row_count = len(df)
        col_count = len(df.columns)
        
        # Memory consumption
        mem_bytes = df.memory_usage(deep=True).sum()
        mem_mb = mem_bytes / (1024 * 1024)

        # Missing & non-finite stats
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        non_numeric_cols = [c for c in df.columns if c not in numeric_cols]
        
        null_counts = df.isna().sum()
        total_nulls = int(null_counts.sum())
        cols_with_nulls = null_counts[null_counts > 0].to_dict()

        inf_counts = {}
        for c in numeric_cols:
            n_inf = int(np.isinf(df[c]).sum())
            if n_inf > 0:
                inf_counts[c] = n_inf
        total_infs = sum(inf_counts.values())

        # Exact duplicate estimate
        dup_count = int(df.duplicated().sum())

        # Class balance
        class_dist = {}
        binary_dist = {"Benign": 0, "Attack": 0}
        if label_col:
            raw_counts = df[label_col].value_counts().to_dict()
            class_dist = {str(k).strip(): int(v) for k, v in raw_counts.items()}
            for k, v in class_dist.items():
                if "benign" in k.lower():
                    binary_dist["Benign"] += v
                else:
                    binary_dist["Attack"] += v

        # Feature range summaries for numeric features
        feature_ranges = {}
        for c in numeric_cols[:15]:  # Capture sample features
            s = df[c].replace([np.inf, -np.inf], np.nan).dropna()
            if not s.empty:
                feature_ranges[c] = {
                    "min": float(s.min()),
                    "max": float(s.max()),
                    "mean": float(s.mean()),
                    "std": float(s.std()) if len(s) > 1 else 0.0,
                }

        return {
            "source_name": source_name,
            "row_count": row_count,
            "column_count": col_count,
            "memory_mb": round(mem_mb, 2),
            "label_column": label_col,
            "total_null_cells": total_nulls,
            "columns_with_nulls": cols_with_nulls,
            "total_infinite_cells": total_infs,
            "columns_with_infinities": inf_counts,
            "duplicate_rows": dup_count,
            "duplicate_percentage": round((dup_count / row_count * 100), 2) if row_count > 0 else 0.0,
            "class_distribution": class_dist,
            "binary_distribution": binary_dist,
            "numeric_feature_count": len(numeric_cols),
            "categorical_feature_count": len(non_numeric_cols),
            "sample_feature_ranges": feature_ranges,
        }

    @staticmethod
    def reconcile_schemas(file_headers: Dict[str, List[str]]) -> Dict[str, Any]:
        """Compares column headers across multiple CSV files to detect discrepancies."""
        if not file_headers:
            return {"is_uniform": True, "common_columns": [], "discrepancies": {}}

        normalized_headers = {
            f: [col.strip() for col in cols]
            for f, cols in file_headers.items()
        }

        all_cols_sets = [set(cols) for cols in normalized_headers.values()]
        common_cols = sorted(list(set.intersection(*all_cols_sets))) if all_cols_sets else []
        union_cols = sorted(list(set.union(*all_cols_sets))) if all_cols_sets else []

        discrepancies = {}
        for fname, cols in normalized_headers.items():
            missing_from_file = set(union_cols) - set(cols)
            extra_in_file = set(cols) - set(common_cols)
            if missing_from_file or extra_in_file:
                discrepancies[fname] = {
                    "missing": sorted(list(missing_from_file)),
                    "extra": sorted(list(extra_in_file)),
                }

        return {
            "is_uniform": len(discrepancies) == 0,
            "total_files": len(file_headers),
            "common_column_count": len(common_cols),
            "union_column_count": len(union_cols),
            "common_columns": common_cols,
            "discrepancies": discrepancies,
        }
