# AVENIQ SENTINEL — PHASE 3.1: EXPERIMENT CONTRACT & ARTIFACT INTEGRITY SPECIFICATION

**Product:** Aveniq Sentinel  
**Company:** Aveniq  
**Author:** Principal Machine Learning Engineer & Cybersecurity ML Research Engineer  
**Status:** Approved & Implemented (`src/neuralshield/ml/experiment.py`)  
**Target Repository:** `https://github.com/sparxweb/aveniq-sentinel`

---

## 1. Executive Summary

In a decoupled cloud ML lifecycle, models are trained and validated on ephemeral remote cloud compute instances (Kaggle Notebooks / Google Colaboratory) and subsequently transferred to the local repository (`models/`) for serving via the Streamlit dashboard and inference engines.

Without rigorous artifact governance, distributed training suffers from critical failure modes:
1. **Silent Model Corruption:** Truncated transfers, pickling version mismatches, or byte corruption causing undefined behavior during inference.
2. **Untracked Model Drift:** Deploying a model without knowing which dataset version, temporal split, git commit, or feature contract created it.
3. **Malicious / Unauthorized Model Substitution:** Loading unverified serialized binaries (`.joblib`, `.pkl`) which can execute arbitrary code upon deserialization.

The **Aveniq Sentinel Experiment Contract** enforces cryptographic integrity, immutable metadata logging, and strict verification gates prior to artifact ingestion.

---

## 2. Cloud-to-Local Model Transfer Protocol

The artifact lifecycle follows a unidirectional, cryptographically sealed promotion pipeline:

```
[ Phase 1: Cloud Execution ]
   Kaggle Notebook (Python 3.11, Scikit-learn)
      ├── Train model on Temporal Split (Mon-Wed)
      ├── Evaluate on Known & Unseen Attacks (Thu-Fri)
      ├── Serialize model via joblib (compression=3)
      ├── Compute SHA-256 Digest of all binaries
      └── Generate `manifest.json` with ExperimentMetadata
            │
            ▼ (Secure Manual / GitHub Release Download)
[ Phase 2: Local Ingestion & Validation ]
   Local Environment (`c:\Users\HP\OneDrive\Desktop\NEURALSHIELD AI\models\`)
      ├── Place downloaded `model.joblib` and `manifest.json`
      ├── Execute `ExperimentContract.verify_artifact_integrity()`
      │      ├── Recompute SHA-256 of local file
      │      ├── Match against `manifest.json` digest
      │      └── Check Python and Scikit-learn compatibility
      └── Gate Decision:
             ├── IF Valid: Model Approved for Streamlit Dashboard Serving
             └── IF Corrupt: REJECT, ALERT, and Halt Loading
```

---

## 3. Experiment Metadata Specification (`ExperimentMetadata`)

Every trained artifact must be accompanied by an immutable JSON manifest matching the schema below:

```json
{
  "experiment_id": "EXP-20261123-CICIDS2017-RF-V1",
  "model_name": "random_forest_temporal_baseline",
  "model_type": "RandomForestClassifier",
  "framework": "scikit-learn",
  "framework_version": "1.4.2",
  "dataset_version": "CIC-IDS2017-UNB-Official-8Files",
  "temporal_split_strategy": "Mon-Wed Train/Val, Thu-Fri Test (Chronological)",
  "train_days": ["Monday", "Tuesday", "Wednesday"],
  "test_days": ["Thursday", "Friday"],
  "feature_contract_version": "1.0.0",
  "feature_count": 78,
  "features": [
    "flow_duration",
    "total_fwd_packets",
    "total_backward_packets",
    "..."
  ],
  "hyperparameters": {
    "n_estimators": 100,
    "max_depth": 20,
    "min_samples_split": 10,
    "n_jobs": -1,
    "random_state": 42
  },
  "metrics": {
    "train_accuracy": 0.9984,
    "known_test_f1_macro": 0.9621,
    "known_test_recall": 0.9580,
    "unseen_test_anomaly_detection_rate": 0.8412,
    "overall_test_accuracy": 0.9450
  },
  "artifact_filename": "random_forest_baseline.joblib",
  "artifact_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "created_at": "2026-11-23T14:30:00Z",
  "git_commit": "e89271a"
}
```

---

## 4. SHA-256 Cryptographic Verification Gate

The verification algorithm streams the binary file in 65,536-byte chunks to calculate the digest without saturating RAM:

$$\text{SHA-256}(B) = H(B_0 \parallel B_1 \parallel \dots \parallel B_k)$$

### Verification Conditions:
1. **Digest Equivalence:** Calculated hash must strictly match `artifact_sha256`.
2. **Environment Match:** Warning logged if Scikit-learn major version differs between training and local inference environments.
3. **Feature Count Agreement:** Incoming model must expect exactly 78 features matching `FeatureContract.CORE_ML_FEATURES`.

---

## 5. Security & Reproducibility Guarantees

1. **Zero Unverified Deserialization:**
   - In accordance with standard Python security practices (CVE-2024 mitigations), unauthenticated `.pkl` or `.joblib` files are never unpickled without prior SHA-256 verification.
2. **Audit Trail Completeness:**
   - The exact training configuration, features, and evaluation scores are embedded directly alongside the weight matrices.
3. **Reproducibility Guarantee:**
   - Any external engineer or auditor with access to the raw CIC-IDS2017 dataset and the manifest can reproduce the exact test split and benchmark comparison.
