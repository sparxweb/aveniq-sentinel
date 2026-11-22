"""Configuration settings for NeuralShield AI platform."""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any


# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw" / "cic_ids2017"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
EXTERNAL_DATA_DIR = DATA_DIR / "external"
REPORTS_DIR = PROJECT_ROOT / "reports"
DATA_QUALITY_REPORTS_DIR = REPORTS_DIR / "data_quality"
FIGURES_DIR = REPORTS_DIR / "figures"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"


# Official CIC-IDS2017 8 CSV files (MachineLearningCSV release)
CIC_IDS2017_EXPECTED_FILES = [
    "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
    "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
    "Friday-WorkingHours-Morning.pcap_ISCX.csv",
    "Monday-WorkingHours.pcap_ISCX.csv",
    "Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv",
    "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv",
    "Tuesday-WorkingHours.pcap_ISCX.csv",
    "Wednesday-workingHours.pcap_ISCX.csv",
]


# Known duplicate and redundant columns in CIC-IDS2017 dataset
REDUNDANT_COLUMNS = [
    "Fwd Header Length.1",
    "fwd_header_length.1",
    "fwd_header_length_1",
]


# Sensitive or target-leakage columns to exclude from ML modeling
TARGET_LEAKAGE_COLUMNS = [
    "Flow ID",
    "Source IP",
    "Destination IP",
    "Timestamp",
    "flow_id",
    "source_ip",
    "destination_ip",
    "timestamp",
]


# Canonical target column names
LABEL_COLUMN_CANDIDATES = ["Label", "label", " Label", "Label ", "Class", "class"]


# Standardized attack category taxonomy
ATTACK_TAXONOMY: Dict[str, str] = {
    "BENIGN": "Benign",
    "DDoS": "DDoS",
    "PortScan": "PortScan",
    "Bot": "Botnet",
    "Infiltration": "Infiltration",
    "Web Attack  Brute Force": "Web Attack - Brute Force",
    "Web Attack  XSS": "Web Attack - XSS",
    "Web Attack  Sql Injection": "Web Attack - SQL Injection",
    "Web Attack - Brute Force": "Web Attack - Brute Force",
    "Web Attack - XSS": "Web Attack - XSS",
    "Web Attack - Sql Injection": "Web Attack - SQL Injection",
    "FTP-Patator": "Brute Force - FTP",
    "SSH-Patator": "Brute Force - SSH",
    "DoS slowloris": "DoS - Slowloris",
    "DoS Slowhttptest": "DoS - SlowHTTPTest",
    "DoS Hulk": "DoS - Hulk",
    "DoS GoldenEye": "DoS - GoldenEye",
    "Heartbleed": "Heartbleed",
}


@dataclass
class ProcessingConfig:
    """Configurable preprocessing settings."""
    chunk_size: int = 100_000
    random_state: int = 42
    drop_exact_duplicates: bool = True
    handle_infinities: bool = True
    drop_redundant_columns: bool = True
    drop_leakage_columns: bool = True
    target_column: str = "label"
    max_memory_mb: float = 2048.0
    export_format: str = "parquet"  # "parquet" or "csv"
    low_memory: bool = True


@dataclass
class UIThemeConfig:
    """Cybersecurity Command Center color scheme and styling."""
    bg_primary: str = "#080B0A"
    bg_secondary: str = "#101614"
    accent_primary: str = "#16C784"  # Emerald green (safe/normal)
    accent_danger: str = "#EF4444"   # Crimson red (attack/threat)
    accent_warning: str = "#F59E0B"  # Amber warning
    text_primary: str = "#E8F0EB"
    text_secondary: str = "#8B9A91"
    border_color: str = "#1D2824"
    card_bg: str = "#121A17"
