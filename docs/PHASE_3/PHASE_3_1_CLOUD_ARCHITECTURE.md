# AVENIQ SENTINEL — PHASE 3.1: CLOUD ML TRAINING ARCHITECTURE
**Product:** Aveniq Sentinel  
**Company:** Aveniq (Startup)  
**Engineering Phase:** Phase 3.1 — Cloud ML Foundation, Dataset Profiling & Temporal Splitting  
**Date:** November 23, 2026  
**Primary Cloud Compute:** Kaggle Notebooks (Free Tier, 30 hrs/week, 16–30 GB RAM)  
**Backup Cloud Compute:** Google Colaboratory (Free Tier, 12 GB RAM)  
**Local System Policy:** ZERO Large-Scale Model Training on User Laptop  

---

## 1. ARCHITECTURAL OBJECTIVE & HARDWARE ISOLATION MANDATE

The primary mandate of Phase 3.1 is establishing an air-gapped, cloud-first machine learning engineering workflow for Aveniq Sentinel. 

Training models on the full UNB CIC-IDS2017 benchmark dataset (~2.83 million network flow records across 8 multi-gigabyte CSV captures) demands extensive memory bandwidth and vector operations. Conducting training on the user's local laptop introduces risks of thermal throttling, out-of-memory (OOM) operating system panics, and prolonged system unresponsiveness.

Therefore, the platform enforces a strict five-tier architectural separation:

```
+-----------------------------------------------------------------------------------+
|                        AVENIQ SENTINEL FIVE-TIER ML TOPOLOGY                      |
+-----------------------------------------------------------------------------------+

 [ TIER A: LOCAL DEVELOPMENT ]          [ TIER B: CLOUD DATA & TRAINING ]
  • Git branch management                • Kaggle input mount (/kaggle/input/cicids2017)
  • Feature contract definition          • Streaming chunked reader (100k rows/chunk)
  • Unit & integration testing           • Lossless numeric downcasting (float32)
  • Streamlit Command Center UI          • Chronological temporal partitioning
  • Air-gapped code authoring            • Scikit-learn model fitting (CPU-optimized)
                │                                      │
                ▼                                      ▼
 [ TIER E: LOCAL INFERENCE ]            [ TIER C: CLOUD MODEL EVALUATION ]
  • Streamlit SOC operations             • Imbalance-aware metrics (PR-AUC, Macro-F1)
  • Single-flow & batch scoring          • Known-attack classification report
  • LightGBM / RF inference              • Zero-day / Unseen-attack OOD evaluation
  • Explanatory attribution              • False Positive Rate (FPR < 0.1% constraint)
                ▲                                      │
                │                                      ▼
                │                      [ TIER D: ARTIFACT PACKAGING & TRANSFER ]
                │                       • Lightweight model serialization (joblib)
                └────────────────────── • Cryptographic SHA-256 hash manifest
                                        • Transfer via GitHub Release assets / Kaggle
```

---

## 2. COMPONENT INTERFACES & RESPONSIBILITIES

### Tier A: Local Application & Development
- **Location:** Local Developer Workstation (`c:\Users\HP\OneDrive\Desktop\NEURALSHIELD AI`).
- **Scope:** Application scaffolding, UI development in Streamlit, data quality validation logic, unit tests in Pytest, and architectural specifications.
- **Data Footprint:** Operates exclusively on deterministic synthetic baseline fixtures (`data/sample/`, 1,505 flows) or user-uploaded flow captures. Raw 3.1 GB CSV captures are excluded from local memory.

### Tier B: Remote Data Preparation & Training
- **Location:** Kaggle Cloud Environment (`/kaggle/working/`, `/kaggle/input/cicids2017/`).
- **Scope:** Mounts the full 8-file CIC-IDS2017 dataset via Kaggle's native dataset interface. Executes chunked ingestion (`chunk_size=100_000`), lossless downcasting (`float64` $\rightarrow$ `float32`, `int64` $\rightarrow$ `int32`), and feature synthesis with zero swap-file thrashing.
- **Hardware Requirement:** Operates entirely within Kaggle's free standard CPU instance (4 vCPUs, 30 GB RAM). No GPU is required for the baseline Scikit-learn model stack.

### Tier C: Cloud Model Evaluation
- **Scope:** Evaluates trained estimators strictly under chronological constraints.
- **Separation of Metrics:**
  - **Known-Class Evaluation:** Measures multi-class discrimination on attack vectors present during training (e.g. Patator, DoS, Heartbleed).
  - **Novelty / Zero-Day Evaluation:** Measures anomaly detection performance on attacks exclusive to the test period (e.g. Web Attacks, Infiltration, Botnet, PortScan, DDoS).
- **Primary Metrics:** Precision-Recall AUC (PR-AUC), Macro F1-Score, and False Positive Rate (FPR). Raw accuracy is explicitly disqualified as a success metric due to the ~80% natural Benign class dominance.

### Tier D: Model Artifact Packaging & Transfer
- **Scope:** Serializes trained model pipelines (`model.joblib`), scaler objects, and feature contracts into compact binary archives.
- **Integrity Guarantee:** Accompanied by an `experiment_manifest.json` recording experiment ID, feature schema version, random seed, training period, and a cryptographic SHA-256 hash.
- **Storage Policy:** Model binaries (> 50 MB) are excluded from public git commits via `.gitignore` and delivered through GitHub Release Assets or secure Kaggle output links.

### Tier E: Local Inference & SOC Visualization
- **Scope:** Loads certified model artifacts locally into the Aveniq Sentinel Streamlit dashboard (`app_pages/`).
- **Integrity Check:** Before deserializing any model file, the platform calculates its SHA-256 checksum and compares it against the manifest to guarantee artifact provenance and prevent arbitrary code execution.
- **Analyst UX:** Real-time threat classification, confidence scoring, and behavioral contrast for incoming telemetry.

---

## 3. ZERO-COST COMPUTE & AIR-GAP COMPLIANCE

1. **Zero Paid Compute:** The architecture operates entirely on Kaggle Notebooks' free quota (30 hours weekly CPU/GPU allotment) and Google Colab free tier.
2. **Deterministic Reproducibility:** Every experiment fixes `random_state=42`, logs exact library versions, and standardizes feature order.
3. **Air-Gap Compliance:** The cloud notebooks execute solely on public benchmark datasets; no private client data or local credentials ever leave the developer workstation.
