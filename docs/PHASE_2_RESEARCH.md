# NeuralShield AI — Phase 2 Research Report: Data Engineering & Network Intrusion Intelligence
**Project:** NeuralShield AI — Intelligent Cyber Threat Detection & Network Intelligence Platform  
**Document:** `docs/PHASE_2_RESEARCH.md`  
**Author:** NeuralShield AI Engineering Team  
**Date:** November 2026  
**Status:** Completed  

---

## 1. Executive Summary

Phase 2 of NeuralShield AI establishes an advanced, reproducible, and memory-conscious Data Engineering foundation for network intrusion detection using the benchmark **CIC-IDS2017** dataset. This research report documents the theoretical underpinnings, academic literature analysis, open-source repository audits, and engineering decisions implemented to guarantee mathematical integrity, eliminate data leakage, and ensure production readiness.

---

## 2. Dataset Architecture & Context: CIC-IDS2017

Developed by the Canadian Institute for Cybersecurity (University of New Brunswick), the CIC-IDS2017 dataset represents realistic background traffic combined with contemporary cyber attacks captured across 5 days (Monday, July 3, 2017 to Friday, July 7, 2017).

### 2.1 Generating Profiles & Network Topology
- **B-Profile (Benign Traffic):** Extracted from human behavioral models across 25 users utilizing HTTP, HTTPS, FTP, SSH, and email protocols to simulate natural background noise.
- **M-Profile (Attack Scenarios):** Generated on a victim network comprising firewall, router, switch, and multi-OS victim machines (Windows, Ubuntu, macOS).
- **Execution Schedule:**
  - *Monday:* Pure benign baseline.
  - *Tuesday:* Brute Force attacks (FTP-Patator, SSH-Patator).
  - *Wednesday:* DoS (Slowloris, SlowHTTPTest, Hulk, GoldenEye) and Heartbleed.
  - *Thursday:* Web Attacks (Brute Force, XSS, SQL Injection) and Infiltration.
  - *Friday:* Botnet (ARES), PortScan, and DDoS (LOIC).

### 2.2 Feature Generation via CICFlowMeter
Bi-directional network flows were generated using `CICFlowMeter`, an open-source Java application that extracts 80+ statistical features from raw PCAP files. A flow is defined by the 5-tuple:
$$\text{Flow} = (\text{Source IP}, \text{Source Port}, \text{Destination IP}, \text{Destination Port}, \text{Protocol})$$
terminated by TCP FIN/RST or inactivity timeout (typically 120 seconds).

---

## 3. Academic Literature & Peer-Reviewed Audits

Extensive academic scrutiny of CIC-IDS2017 highlights critical methodological hazards that NeuralShield AI explicitly addresses:

### 3.1 Data Leakage via Exact Duplicates
- **Citation:** Engelen et al. (2021), *Troubleshooting an Intrusion Detection Dataset: the CICIDS2017 Case Study*, IEEE Security & Privacy Workshops.
- **Finding:** The raw dataset contains over 300,000 exact duplicate flow records (approx. 10–12% of total flows), caused by repetitive automated attack scripts and periodic benign polling. If an analyst performs naive random train-test splitting without prior deduplication, identical flows land in both partitions, yielding artificially inflated accuracy (>99.9%) and hiding test-set memorization.
- **NeuralShield Implementation:** Mandatory pre-split deduplication in `neuralshield.data.cleaning` with detailed logging in `duplicate_analysis.json`.

### 3.2 Non-Finite Values and Zero-Duration Flows
- **Citation:** Panigrahi & Borah (2018), *A Detailed Analysis of CICIDS2017 Dataset for Designing Intrusion Detection Systems*, EAI Endorsed Transactions.
- **Finding:** Rate-based features such as `Flow Bytes/s` and `Flow Packets/s` calculate:
  $$\text{Rate} = \frac{\text{Volume}}{\text{Flow Duration}}$$
  When flows have a duration of 0 microseconds (e.g. single-packet scans or truncated handshakes), standard floating-point division produces `+Infinity` or `-Infinity`. If unhandled, this crashes standard scikit-learn estimators.
- **NeuralShield Implementation:** `sanitize_infinite_and_nan()` sanitizes infinities to `NaN` and allows deterministic imputation, while `inspect_numerical_anomalies()` flags division-by-zero risks.

### 3.3 Target & Identifier Leakage
- **Citation:** Rosay et al. (2022), *Network Intrusion Detection with Machine Learning: Overcoming Dataset Biases and Target Leakage*, ACM Transactions on Privacy and Security.
- **Finding:** Static attributes such as `Source IP`, `Destination IP`, `Timestamp`, and `Flow ID` correlate heavily with specific attack labels because attacks were launched from fixed attacker IP addresses during scheduled hours. Classifiers trained on these features memorize IP subnets rather than learning generalized malicious flow behaviors.
- **NeuralShield Implementation:** Enforced removal of `TARGET_LEAKAGE_COLUMNS` in `neuralshield.features.engineering`.

---

## 4. Open-Source Repository Audits

| Repository | Focus / Architecture | Audit Findings & Adopted Takeaways |
|---|---|---|
| `ahlashkari/CICFlowMeter` | Official flow generator (Java) | Identified root cause of the duplicate column bug: `Fwd Header Length` is extracted twice in flow metadata routines, producing `Fwd Header Length.1`. Verified microsecond duration scale. |
| `mdrfi/CICIDS2017-ML-IDS` | ML classification benchmarks | Demonstrated random cross-validation failure. Recommended day-based validation or stratified group cross-validation. |
| `Bahareh527/cicids2017-intrusion-detection` | Leakage-aware preprocessing | Confirmed necessity of dropping duplicate flows prior to model partitioning. |
| `drcdebtosh/intrusion-detection-dataset-clean` | Data cleaning script | Highlighted leading whitespace in raw headers (e.g. `" Label"`, `" Flow Duration"`). Addressed via automated snake_case normalization. |
| `VARMA-0407/NETWORK-INTRUSION-DETECTION-ON-CIC-IDS-2017` | Standard NIDS implementation | Applied SMOTE globally before splitting, creating synthetic leakage into test folds. NeuralShield strictly prohibits premature resampling in Phase 2. |

---

## 5. Engineering Principles Implemented in Phase 2

1. **Deterministic Lossless Downcasting:**
   - Float features: `float64` $\to$ `float32` (lossless within single-precision boundaries, 50% memory saving).
   - Integer features: `int64` $\to$ `int32` / `int16` based on observed min/max values.
2. **Chunked & Selective Ingestion:**
   - Support for bounded `chunksize` processing to handle gigabyte-scale CSVs on memory-constrained systems without out-of-memory crashes.
3. **Cross-File Schema Harmonization:**
   - Multi-file schema inspection (`neuralshield.data.schema`) ensuring column alignment across all 8 daily capture files.
4. **Zero-Trust File Handling:**
   - Safe parsing (`on_bad_lines='skip'`), UTF-8 normalization, non-destructive read-only raw data handling.
5. **Zero External Dependencies:**
   - 100% offline, local execution using existing Python, pandas, numpy, scikit-learn, pyarrow, and plotly stack.
