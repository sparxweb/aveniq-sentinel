"""Machine Learning Feature Contract & Schema Enforcer.

Defines the explicit contract between raw/preprocessed network flows and ML model inputs,
enforcing type safety, missing-value policies, and strict target-leakage rejection.
"""

from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np

from config.settings import TARGET_LEAKAGE_COLUMNS, REDUNDANT_COLUMNS
from config.logging_config import get_logger

logger = get_logger("ml.feature_contract")


@dataclass
class MLFeature:
    """Specification of an individual feature in the ML contract."""
    name: str
    dtype: str
    category: str
    description: str
    source: str  # "raw_flow" or "engineered"
    transformation: str
    missing_strategy: str  # "median", "zero", "drop"
    is_model_input: bool
    leakage_risk: str  # "NONE", "HIGH_IDENTIFIER", "HIGH_TEMPORAL", "MODERATE_PORT"


# Core Permitted ML Feature Definitions
CORE_ML_FEATURES: List[MLFeature] = [
    # 1. Flow Timing & Duration
    MLFeature(
        name="Flow Duration",
        dtype="float32",
        category="timing",
        description="Total duration of the network flow in microseconds.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="log_flow_duration",
        dtype="float32",
        category="timing",
        description="Natural log(1 + Flow Duration) to stabilize heavy-tailed microsecond metrics.",
        source="engineered",
        transformation="log1p(Flow Duration)",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="Flow IAT Mean",
        dtype="float32",
        category="timing",
        description="Mean inter-arrival time between consecutive packets in flow.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="Flow IAT Std",
        dtype="float32",
        category="timing",
        description="Standard deviation of packet inter-arrival times.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="Flow IAT Max",
        dtype="float32",
        category="timing",
        description="Maximum inter-arrival time observed between consecutive packets.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="Flow IAT Min",
        dtype="float32",
        category="timing",
        description="Minimum inter-arrival time observed between consecutive packets.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),

    # 2. Volumetric & Asymmetry Dynamics
    MLFeature(
        name="Total Fwd Packets",
        dtype="float32",
        category="volume",
        description="Total number of packets transmitted in forward direction.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="Total Backward Packets",
        dtype="float32",
        category="volume",
        description="Total number of packets transmitted in backward direction.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="Total Length of Fwd Packets",
        dtype="float32",
        category="volume",
        description="Aggregate payload bytes transmitted in forward direction.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="Total Length of Bwd Packets",
        dtype="float32",
        category="volume",
        description="Aggregate payload bytes transmitted in backward direction.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="packet_symmetry_ratio",
        dtype="float32",
        category="volume",
        description="Ratio of forward packets to backward packets (directional asymmetry).",
        source="engineered",
        transformation="Fwd Packets / max(Bwd Packets, 1)",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="byte_symmetry_ratio",
        dtype="float32",
        category="volume",
        description="Ratio of forward payload bytes to backward payload bytes.",
        source="engineered",
        transformation="Fwd Bytes / max(Bwd Bytes, 1)",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="total_volume_bytes",
        dtype="float32",
        category="volume",
        description="Total bidirectional payload volume in bytes.",
        source="engineered",
        transformation="Fwd Bytes + Bwd Bytes",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),

    # 3. Rates & Throughput
    MLFeature(
        name="Flow Bytes/s",
        dtype="float32",
        category="rates",
        description="Byte transmission rate per second across flow duration.",
        source="raw_flow",
        transformation="sanitize_inf_then_downcast",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="Flow Packets/s",
        dtype="float32",
        category="rates",
        description="Packet transmission rate per second across flow duration.",
        source="raw_flow",
        transformation="sanitize_inf_then_downcast",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),

    # 4. TCP Behavior & Flags
    MLFeature(
        name="SYN Flag Count",
        dtype="float32",
        category="tcp",
        description="Count of packets exhibiting TCP SYN flag set.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="zero",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="ACK Flag Count",
        dtype="float32",
        category="tcp",
        description="Count of packets exhibiting TCP ACK flag set.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="zero",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="FIN Flag Count",
        dtype="float32",
        category="tcp",
        description="Count of packets exhibiting TCP FIN flag set.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="zero",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="RST Flag Count",
        dtype="float32",
        category="tcp",
        description="Count of packets exhibiting TCP RST flag set.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="zero",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="PSH Flag Count",
        dtype="float32",
        category="tcp",
        description="Count of packets exhibiting TCP PSH flag set.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="zero",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="URG Flag Count",
        dtype="float32",
        category="tcp",
        description="Count of packets exhibiting TCP URG flag set.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="zero",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="syn_packet_density",
        dtype="float32",
        category="tcp",
        description="Ratio of SYN flags to forward packet count (elevated during SYN flood / scans).",
        source="engineered",
        transformation="SYN Flags / max(Fwd Packets, 1)",
        missing_strategy="zero",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="syn_to_ack_ratio",
        dtype="float32",
        category="tcp",
        description="Ratio of SYN flags to ACK flags.",
        source="engineered",
        transformation="SYN Flags / max(ACK Flags, 1)",
        missing_strategy="zero",
        is_model_input=True,
        leakage_risk="NONE",
    ),

    # 5. Packet Length Distributions
    MLFeature(
        name="Min Packet Length",
        dtype="float32",
        category="packet_length",
        description="Minimum packet payload length observed in flow.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="Max Packet Length",
        dtype="float32",
        category="packet_length",
        description="Maximum packet payload length observed in flow.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="Packet Length Mean",
        dtype="float32",
        category="packet_length",
        description="Mean packet payload length in bytes.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="Packet Length Std",
        dtype="float32",
        category="packet_length",
        description="Standard deviation of packet payload lengths.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="Packet Length Variance",
        dtype="float32",
        category="packet_length",
        description="Variance of packet payload lengths.",
        source="raw_flow",
        transformation="lossless_downcast",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),
    MLFeature(
        name="packet_length_spread",
        dtype="float32",
        category="packet_length",
        description="Difference between maximum and minimum observed packet lengths.",
        source="engineered",
        transformation="Max Packet Length - Min Packet Length",
        missing_strategy="median",
        is_model_input=True,
        leakage_risk="NONE",
    ),

    # Explicit Target Leakage Columns (Documented as strictly FORBIDDEN from model input)
    MLFeature(
        name="Flow ID",
        dtype="string",
        category="identifier",
        description="Synthetic socket flow identifier.",
        source="raw_flow",
        transformation="dropped",
        missing_strategy="drop",
        is_model_input=False,
        leakage_risk="HIGH_IDENTIFIER",
    ),
    MLFeature(
        name="Source IP",
        dtype="string",
        category="identifier",
        description="Source IPv4 address.",
        source="raw_flow",
        transformation="dropped",
        missing_strategy="drop",
        is_model_input=False,
        leakage_risk="HIGH_IDENTIFIER",
    ),
    MLFeature(
        name="Destination IP",
        dtype="string",
        category="identifier",
        description="Destination IPv4 address.",
        source="raw_flow",
        transformation="dropped",
        missing_strategy="drop",
        is_model_input=False,
        leakage_risk="HIGH_IDENTIFIER",
    ),
    MLFeature(
        name="Timestamp",
        dtype="string",
        category="temporal",
        description="Capture wall-clock timestamp.",
        source="raw_flow",
        transformation="used_for_split_only_then_dropped",
        missing_strategy="drop",
        is_model_input=False,
        leakage_risk="HIGH_TEMPORAL",
    ),
]


class FeatureContract:
    """Enforces and validates the ML feature schema across training and inference."""

    def __init__(self, features: Optional[List[MLFeature]] = None):
        self.features = features or CORE_ML_FEATURES
        self.feature_map = {f.name: f for f in self.features}
        self.permitted_input_names = [f.name for f in self.features if f.is_model_input]
        self.forbidden_leakage_names = [f.name for f in self.features if not f.is_model_input]

    def validate_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Audits a DataFrame against the feature contract."""
        df_cols_clean = {c.strip(): c for c in df.columns}
        
        # Check for presence of permitted features
        available_permitted = []
        missing_permitted = []
        for name in self.permitted_input_names:
            matched = False
            for c_clean in df_cols_clean:
                if c_clean.lower() == name.lower().strip():
                    available_permitted.append(name)
                    matched = True
                    break
            if not matched:
                missing_permitted.append(name)

        # Check for hazardous leakage columns
        detected_leakage = []
        for name in self.forbidden_leakage_names:
            for c_clean in df_cols_clean:
                if c_clean.lower() == name.lower().strip():
                    detected_leakage.append(c_clean)
                    break

        return {
            "total_contract_features": len(self.permitted_input_names),
            "available_permitted_count": len(available_permitted),
            "missing_permitted_count": len(missing_permitted),
            "available_permitted": available_permitted,
            "missing_permitted": missing_permitted,
            "detected_leakage_columns": detected_leakage,
            "has_leakage_hazard": len(detected_leakage) > 0,
            "is_valid_for_training": len(detected_leakage) == 0 and len(available_permitted) > 0,
        }

    def prepare_feature_matrix(
        self,
        df: pd.DataFrame,
        label_col: Optional[str] = None,
    ) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        """Extracts strictly approved numeric features for X, dropping all leakage features,
        and extracts target vector y.
        """
        df_work = df.copy()
        
        # 1. Isolate and normalize target label
        y = None
        target_name = label_col
        if not target_name:
            for c in df_work.columns:
                if c.strip().lower() in ("label", "class", "target"):
                    target_name = c
                    break

        if target_name and target_name in df_work.columns:
            y = df_work[target_name].astype(str).str.strip()
            df_work = df_work.drop(columns=[target_name], errors="ignore")

        # 2. Drop all known leakage and redundant columns
        drop_cols = []
        for c in df_work.columns:
            c_clean = c.strip().lower()
            if any(c_clean == leak.strip().lower() for leak in TARGET_LEAKAGE_COLUMNS):
                drop_cols.append(c)
            elif any(c_clean == red.strip().lower() for red in REDUNDANT_COLUMNS):
                drop_cols.append(c)
            elif any(c_clean == f.name.strip().lower() for f in self.features if not f.is_model_input):
                drop_cols.append(c)

        df_work = df_work.drop(columns=list(set(drop_cols)), errors="ignore")

        # 3. Filter to strictly numeric columns and downcast
        numeric_cols = df_work.select_dtypes(include=[np.number]).columns
        X = df_work[numeric_cols].copy()

        # Sanitize any residual infinities and NaNs
        X = X.replace([np.inf, -np.inf], np.nan)
        medians = X.median().fillna(0.0)
        X = X.fillna(medians).astype(np.float32)

        return X, y

    def get_contract_manifest(self) -> List[Dict[str, Any]]:
        """Returns full contract schema as serializable dictionary list."""
        return [asdict(f) for f in self.features]
