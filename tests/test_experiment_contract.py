"""Unit tests for Experiment Configuration & Artifact Contract (Phase 3.1)."""

import pytest
import json
import tempfile
from pathlib import Path

from neuralshield.ml.experiment import ExperimentContract, ExperimentMetadata


@pytest.fixture
def sample_metadata():
    return ExperimentMetadata(
        experiment_id="EXP_20261123_BASELINE_RF",
        created_at="2026-11-23T12:00:00Z",
        dataset_name="CIC-IDS2017",
        dataset_version="MachineLearningCSV-v1",
        feature_schema_version="3.1.0",
        train_period=["Monday", "Tuesday", "Wednesday"],
        val_period=["Wednesday-Afternoon"],
        test_period=["Thursday", "Friday"],
        model_type="RandomForestClassifier",
        hyperparameters={"n_estimators": 100, "max_depth": 15},
        metrics={"pr_auc": 0.942, "macro_f1": 0.891, "fpr": 0.002},
        target_classes=["Benign", "DoS", "PortScan"],
        unseen_test_classes=["Web Attack", "Botnet"],
        random_seed=42,
        python_version="3.11.16",
        sklearn_version="1.5.2",
        environment="Kaggle",
    )


def test_save_and_verify_manifest(sample_metadata):
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir)
        
        # Create dummy model file
        dummy_model = out_path / "model.joblib"
        dummy_model.write_bytes(b"DUMMY_MODEL_WEIGHTS_BINARY_BLOB_FOR_TESTING")

        # Save manifest with artifact hash
        manifest_file = ExperimentContract.save_experiment_manifest(
            sample_metadata,
            out_path,
            artifact_path=dummy_model,
        )

        assert manifest_file.is_file()
        
        # Verify artifact integrity
        res = ExperimentContract.verify_artifact_integrity(manifest_file, dummy_model)
        assert res["valid"] is True
        assert res["experiment_id"] == "EXP_20261123_BASELINE_RF"
        assert len(res["actual_hash"]) == 64  # SHA-256 length


def test_verify_tampered_artifact(sample_metadata):
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir)
        
        dummy_model = out_path / "model.joblib"
        dummy_model.write_bytes(b"ORIGINAL_BYTES")

        manifest_file = ExperimentContract.save_experiment_manifest(
            sample_metadata,
            out_path,
            artifact_path=dummy_model,
        )

        # Tamper with the model file
        dummy_model.write_bytes(b"TAMPERED_BYTES_MALICIOUS_OR_CORRUPT")

        res = ExperimentContract.verify_artifact_integrity(manifest_file, dummy_model)
        assert res["valid"] is False
        assert res["actual_hash"] != res["expected_hash"]
