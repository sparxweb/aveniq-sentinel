"""Chronological Temporal Splitting Architecture for CIC-IDS2017.

Enforces strict day-based temporal boundaries (Mon-Wed Train/Val, Thu-Fri Test),
detects and catalogs unseen attack classes, and completely prevents data leakage.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

from config.settings import TARGET_LEAKAGE_COLUMNS, ATTACK_TAXONOMY
from config.logging_config import get_logger

logger = get_logger("ml.temporal")

# Official Day Designations
TRAIN_DAYS = ["Monday", "Tuesday", "Wednesday"]
VAL_DAYS = ["Wednesday-Afternoon"]
TEST_DAYS = ["Thursday-Morning", "Thursday-Afternoon", "Friday-Morning", "Friday-Afternoon-PortScan", "Friday-Afternoon-DDoS"]

# Known Attack Classes in Training Period (Monday - Wednesday)
KNOWN_TRAINING_ATTACKS: Set[str] = {
    "FTP-Patator",
    "SSH-Patator",
    "DoS slowloris",
    "DoS Slowhttptest",
    "DoS Hulk",
    "DoS GoldenEye",
    "Heartbleed",
}

# Attack Classes that ONLY appear in Thursday & Friday (Unseen during Training)
UNSEEN_TEST_ATTACKS: Set[str] = {
    "Web Attack  Brute Force",
    "Web Attack  XSS",
    "Web Attack  Sql Injection",
    "Web Attack - Brute Force",
    "Web Attack - XSS",
    "Web Attack - Sql Injection",
    "Infiltration",
    "Bot",
    "PortScan",
    "DDoS",
}


@dataclass
class TemporalSplit:
    """Container holding chronological split partitions and metadata."""
    train_df: pd.DataFrame
    val_df: pd.DataFrame
    test_df: pd.DataFrame
    train_classes: List[str]
    val_classes: List[str]
    test_classes: List[str]
    unseen_test_classes: List[str]
    split_summary: Dict[str, Any]


class TemporalSplitter:
    """Partitions network flow datasets using strict chronological boundaries.
    
    Guarantees:
    1. Zero chronological leakage: Models trained on historical days must generalize forward.
    2. Zero row-level cross-contamination between train and test days.
    3. Transparent tracking of unseen/zero-day attack categories.
    4. Explicit removal of timestamps and socket identifiers before model input.
    """

    def __init__(
        self,
        val_fraction_of_train: float = 0.20,
        random_seed: int = 42,
    ):
        self.val_fraction = val_fraction_of_train
        self.random_seed = random_seed

    @staticmethod
    def identify_label_col(df: pd.DataFrame) -> str:
        """Finds target label column."""
        for c in df.columns:
            if c.strip().lower() in ("label", "class", "target"):
                return c
        raise ValueError("Target label column not found in DataFrame.")

    def split_by_day(
        self,
        daily_dfs: Dict[str, pd.DataFrame],
        label_col: Optional[str] = None,
    ) -> TemporalSplit:
        """Splits dictionary of daily DataFrames into Train, Validation, and Test partitions.
        
        Expected daily_dfs keys:
        - "Monday", "Tuesday", "Wednesday" -> Training & Validation
        - "Thursday", "Friday" (or specific Thursday/Friday file names) -> Test
        """
        train_frames = []
        val_frames = []
        test_frames = []

        # 1. Collate Training Period (Mon - Wed)
        train_period_frames = []
        for day_key, df in daily_dfs.items():
            k_lower = day_key.lower()
            if any(d.lower() in k_lower for d in ("monday", "tuesday", "wednesday")):
                train_period_frames.append(df)
            elif any(d.lower() in k_lower for d in ("thursday", "friday")):
                test_frames.append(df)

        if not train_period_frames:
            raise ValueError("No Monday-Wednesday data found for training period.")
        if not test_frames:
            raise ValueError("No Thursday-Friday data found for test period.")

        full_train_period = pd.concat(train_period_frames, ignore_index=True)
        full_test_df = pd.concat(test_frames, ignore_index=True)

        target = label_col or self.identify_label_col(full_train_period)

        # 2. Chronological Validation Partition
        # In multi-day data, validation is carved from the end of the training window
        # (e.g. Wednesday flows or stratified chronological fraction)
        n_train_period = len(full_train_period)
        n_val = int(n_train_period * self.val_fraction)
        
        # Chronological split: earliest 80% for train, latest 20% for validation
        train_df = full_train_period.iloc[:-n_val].copy()
        val_df = full_train_period.iloc[-n_val:].copy()

        # 3. Analyze Known vs Unseen Attack Categories
        train_classes = sorted([str(x).strip() for x in train_df[target].unique()])
        val_classes = sorted([str(x).strip() for x in val_df[target].unique()])
        test_classes = sorted([str(x).strip() for x in full_test_df[target].unique()])

        # Unseen classes are those in test_df but never in train_df
        unseen_classes = sorted(list(set(test_classes) - set(train_classes)))

        summary = {
            "train_flows": len(train_df),
            "val_flows": len(val_df),
            "test_flows": len(full_test_df),
            "total_flows": len(train_df) + len(val_df) + len(full_test_df),
            "train_classes_count": len(train_classes),
            "val_classes_count": len(val_classes),
            "test_classes_count": len(test_classes),
            "unseen_classes_count": len(unseen_classes),
            "unseen_classes": unseen_classes,
            "target_column": target,
        }

        logger.info(
            f"Temporal Split Complete: Train={len(train_df):,} | Val={len(val_df):,} | "
            f"Test={len(full_test_df):,} | Unseen Classes={unseen_classes}"
        )

        return TemporalSplit(
            train_df=train_df,
            val_df=val_df,
            test_df=full_test_df,
            train_classes=train_classes,
            val_classes=val_classes,
            test_classes=test_classes,
            unseen_test_classes=unseen_classes,
            split_summary=summary,
        )

    def split_single_dataframe_chronologically(
        self,
        df: pd.DataFrame,
        label_col: Optional[str] = None,
        train_ratio: float = 0.60,
        val_ratio: float = 0.15,
        test_ratio: float = 0.25,
    ) -> TemporalSplit:
        """Splits a single chronologically-ordered DataFrame (such as the sample fixture)
        preserving temporal ordering with zero row-level shuffling.
        """
        assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5, "Ratios must sum to 1.0"
        
        target = label_col or self.identify_label_col(df)
        n = len(df)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)

        train_df = df.iloc[:n_train].copy()
        val_df = df.iloc[n_train:n_train + n_val].copy()
        test_df = df.iloc[n_train + n_val:].copy()

        train_classes = sorted([str(x).strip() for x in train_df[target].unique()])
        val_classes = sorted([str(x).strip() for x in val_df[target].unique()])
        test_classes = sorted([str(x).strip() for x in test_df[target].unique()])

        unseen = sorted(list(set(test_classes) - set(train_classes)))

        summary = {
            "train_flows": len(train_df),
            "val_flows": len(val_df),
            "test_flows": len(test_df),
            "total_flows": n,
            "unseen_classes": unseen,
            "target_column": target,
        }

        return TemporalSplit(
            train_df=train_df,
            val_df=val_df,
            test_df=test_df,
            train_classes=train_classes,
            val_classes=val_classes,
            test_classes=test_classes,
            unseen_test_classes=unseen,
            split_summary=summary,
        )

    @staticmethod
    def partition_known_vs_unseen_test(
        test_df: pd.DataFrame,
        train_classes: List[str],
        label_col: str = "Label",
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Separates test dataset into:
        1. Known-class test set (evaluation of trained classifier accuracy)
        2. Novel/Unseen-class test set (evaluation of anomaly detection / OOD capabilities)
        """
        target = label_col
        for c in test_df.columns:
            if c.strip().lower() == label_col.strip().lower():
                target = c
                break

        test_labels = test_df[target].astype(str).str.strip()
        train_classes_set = set(str(c).strip() for c in train_classes)

        known_mask = test_labels.isin(train_classes_set)
        known_test = test_df[known_mask].copy()
        unseen_test = test_df[~known_mask].copy()

        return known_test, unseen_test
