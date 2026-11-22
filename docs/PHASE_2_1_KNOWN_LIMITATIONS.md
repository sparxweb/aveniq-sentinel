# AVENIQ SENTINEL — PHASE 2.1 KNOWN TECHNICAL LIMITATIONS
**Product:** Aveniq Sentinel  
**Company:** Aveniq (sparxweb)  
**Date:** November 22, 2026  
**Status:** Documented Engineering Boundaries  

---

## 1. PURPOSE

In alignment with Aveniq Sentinel's commitment to empirical honesty and engineering transparency, this document articulates the current technical boundaries, physical hardware constraints, and architectural limitations of the platform at the conclusion of Phase 2.1.

---

## 2. TECHNICAL BOUNDARIES & LIMITATIONS

### 2.1 Benchmark Dataset Volume & Disk Storage
- **Limitation:** The complete official UNB CIC-IDS2017 benchmark suite comprises 8 large CSV files totaling approximately **3.1 GB** uncompressed (~2.8 million flow records).
- **Current State:** Due to standard Git file size limitations (100 MB max per file), the raw 3.1 GB daily CSVs are not checked into the Git repository.
- **Handling:** The repository includes a deterministic 1,505-flow baseline fixture (`data/sample/cic_ids2017_sample.parquet` and `.csv`). When raw files are absent, the platform operates in `DEMO MODE` with clear amber transparency disclaimers. Instructions for extracting the full benchmark are provided in `data/README.md` and `docs/DATASET_GUIDE.md`.

### 2.2 Single-Machine Memory Constraints
- **Limitation:** Loading all 2.8 million flows into a single standard Pandas DataFrame in 64-bit precision requires ~8.2 GB of RAM.
- **Mitigation Implemented:** Lossless numeric downcasting converts float64 to float32 and int64 to int32, reducing memory footprint to ~3.8 GB.
- **Operational Boundary:** Systems with less than 8 GB of total system RAM should utilize the chunked processing engine (`chunk_size=100_000`) in the Processing Center rather than attempting to load the entire multi-day benchmark into interactive memory simultaneously.

### 2.3 Class Imbalance in Attack Profiles
- **Limitation:** In the CIC-IDS2017 benchmark, attack classes exhibit extreme natural skew:
  - `BENIGN` traffic accounts for ~80.3% of all flows.
  - Rare attacks (e.g. `Infiltration`, `Heartbleed`, `Web Attack - Sql Injection`) contain fewer than 50 flows in the entire multi-day capture.
- **Impact:** Standard accuracy metrics will report ~80% even if zero attacks are identified. Phase 3 must enforce **PR-AUC (Precision-Recall Area Under Curve)** and **Macro F1-Score** rather than raw accuracy.

### 2.4 Browser-Side Rendering Limits for Scatter Plots
- **Limitation:** Plotting more than 50,000 individual SVG/WebGL points in Streamlit causes browser UI lag.
- **Mitigation Implemented:** The Flow Data Explorer applies a default sampling threshold (max 5,000 points for interactive scatter projections) while computing full statistical aggregates across the entire loaded dataset.

---

## 3. PHASE 3 PLANNED ENHANCEMENTS

1. **Temporal Train/Test Split Engine:** Replace random K-Fold splits with day-based temporal validation to mimic real-world intrusion deployment.
2. **Distributed/Dask Streaming:** Support out-of-core evaluation for memory-constrained workstations.
3. **Automated Subsampling of Minority Attacks:** SMOTE / Tomek links integration designed specifically for rare cyber intrusion profiles.
