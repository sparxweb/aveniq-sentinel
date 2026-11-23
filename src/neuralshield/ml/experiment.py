"""Experiment Configuration & Model Artifact Contract.

Standardizes metadata recording, reproducibility configurations, artifact contracts,
and cryptographic SHA-256 integrity verification for trained model files.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import hashlib
from datetime import datetime

from config.logging_config import get_logger

logger = get_logger("ml.experiment")


@dataclass
class ExperimentMetadata:
    """Standardized metadata recorded for every training run."""
    experiment_id: str
    created_at: str
    dataset_name: str
    dataset_version: str
    feature_schema_version: str
    train_period: List[str]
    val_period: List[str]
    test_period: List[str]
    model_type: str
    hyperparameters: Dict[str, Any]
    metrics: Dict[str, Any]
    target_classes: List[str]
    unseen_test_classes: List[str]
    random_seed: int
    python_version: str
    sklearn_version: str
    environment: str  # "Kaggle", "Colab", "Local"
    artifact_hash: Optional[str] = None


class ExperimentContract:
    """Manages metadata serialization and artifact integrity."""

    @staticmethod
    def compute_sha256(filepath: Path) -> str:
        """Calculates SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def save_experiment_manifest(
        metadata: ExperimentMetadata,
        output_dir: Path,
        artifact_path: Optional[Path] = None,
    ) -> Path:
        """Saves experiment metadata manifest as JSON with SHA-256 hash."""
        output_dir.mkdir(parents=True, exist_ok=True)
        meta_dict = asdict(metadata)

        if artifact_path and artifact_path.is_file():
            meta_dict["artifact_hash"] = ExperimentContract.compute_sha256(artifact_path)
            meta_dict["artifact_filename"] = artifact_path.name
            meta_dict["artifact_size_bytes"] = artifact_path.stat().st_size

        manifest_path = output_dir / f"{metadata.experiment_id}_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(meta_dict, f, indent=2)

        logger.info(f"Saved experiment manifest: {manifest_path}")
        return manifest_path

    @staticmethod
    def verify_artifact_integrity(
        manifest_path: Path,
        artifact_path: Path,
    ) -> Dict[str, Any]:
        """Cryptographically verifies that a model file matches its manifest hash."""
        if not manifest_path.is_file():
            return {"valid": False, "error": f"Manifest not found: {manifest_path}"}
        if not artifact_path.is_file():
            return {"valid": False, "error": f"Artifact not found: {artifact_path}"}

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        expected_hash = manifest.get("artifact_hash")
        if not expected_hash:
            return {"valid": False, "error": "Manifest does not contain an artifact_hash field."}

        actual_hash = ExperimentContract.compute_sha256(artifact_path)
        is_match = (actual_hash == expected_hash)

        return {
            "valid": is_match,
            "expected_hash": expected_hash,
            "actual_hash": actual_hash,
            "experiment_id": manifest.get("experiment_id", "unknown"),
            "model_type": manifest.get("model_type", "unknown"),
        }
