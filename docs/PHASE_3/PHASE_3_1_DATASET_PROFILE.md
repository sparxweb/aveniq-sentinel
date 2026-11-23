# AVENIQ SENTINEL — PHASE 3.1: DATASET INVENTORY & PROFILING REPORT
**Dataset Suite:** Canadian Institute for Cybersecurity — UNB CIC-IDS2017 (MachineLearningCSV Release)  
**Official Reference:** [https://www.unb.ca/cic/datasets/ids-2017.html](https://www.unb.ca/cic/datasets/ids-2017.html)  
**Total Records:** ~2,830,743 network flows  
**Raw Data Footprint:** ~3.1 GB uncompressed (8 CSV files)  
**Profiling Date:** November 23, 2026  

---

## 1. OFFICIAL BENCHMARK FILE INVENTORY

The UNB CIC-IDS2017 dataset was captured across five consecutive business days (Monday, July 3, 2017 to Friday, July 7, 2017) using B-Profile network simulation behavior.

| Capture CSV File | Day | Date | Capture Period | Expected Flows | Approx Size | Traffic Category & Scheduled Attacks |
|:---|:---:|:---:|:---:|:---:|:---:|:---|
| `Monday-WorkingHours.pcap_ISCX.csv` | Monday | 2017-07-03 | Full Day | 529,918 | 165.2 MB | **Benign Baseline Traffic** (Normal simulated user operations) |
| `Tuesday-WorkingHours.pcap_ISCX.csv` | Tuesday | 2017-07-04 | Full Day | 445,909 | 140.5 MB | **Brute Force Attacks** (`FTP-Patator`: 7,938, `SSH-Patator`: 5,897) |
| `Wednesday-workingHours.pcap_ISCX.csv` | Wednesday | 2017-07-05 | Full Day | 692,703 | 224.8 MB | **DoS & Heartbleed** (`DoS Hulk`: 231,073, `DoS GoldenEye`: 10,293, `DoS slowloris`: 5,796, `DoS Slowhttptest`: 5,499, `Heartbleed`: 11) |
| `Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv` | Thursday | 2017-07-06 | Morning | 170,366 | 84.1 MB | **Web Vulnerability Exploits** (`Web Attack - Brute Force`: 1,507, `Web Attack - XSS`: 652, `Web Attack - SQL Injection`: 21) |
| `Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv` | Thursday | 2017-07-06 | Afternoon | 288,602 | 177.3 MB | **Infiltration** (`Infiltration`: 36, weaponized PDF payload backdoor) |
| `Friday-WorkingHours-Morning.pcap_ISCX.csv` | Friday | 2017-07-07 | Morning | 191,033 | 67.2 MB | **Botnet C2** (`Bot`: 1,966, Ares Botnet command & control) |
| `Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv` | Friday | 2017-07-07 | Afternoon | 286,467 | 128.4 MB | **PortScan Reconnaissance** (`PortScan`: 158,930, Nmap multi-flag sweeps) |
| `Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv` | Friday | 2017-07-07 | Afternoon | 225,745 | 97.6 MB | **DDoS** (`DDoS`: 128,027, LOIC volumetric flooding) |
| **TOTAL BENCHMARK** | **5 Days** | **July 3–7** | — | **2,830,743** | **~1,085 MB** | **15 Traffic Classes (1 Benign, 14 Attack Vectors)** |

---

## 2. CROSS-FILE SCHEMA AUDIT & RECONCILIATION

### 2.1 Header Discrepancies
Inspection of raw CSV files reveals minor inconsistencies that must be handled prior to merging:
1. **Leading/Trailing Whitespace:** Columns like `" Label"`, `" Destination Port"`, and `" Flow Duration"` frequently contain leading spaces in specific daily files.
2. **Duplicate Header:** The feature `"Fwd Header Length.1"` appears in multiple files as a duplicate of `"Fwd Header Length"`. The redundant copy is explicitly detected and dropped by `REDUNDANT_COLUMNS`.
3. **Casing Discrepancies:** `"Label"` vs `"label"`. Resolved by `DatasetProfiler.normalize_column_name()`.

### 2.2 Common Features Across All 8 Files
After whitespace trimming and redundancy removal, **78 common numerical and categorical features** exist across all 8 files.

---

## 3. DATA QUALITY ANOMALIES & IMPUTATION STRATEGY

| Data Quality Phenomenon | Affected Features | Root Cause | Imputation Policy in Aveniq Sentinel |
|:---|:---|:---|:---|
| **Mathematical Infinities (`+inf`, `-inf`)** | `Flow Bytes/s`, `Flow Packets/s` | Flow duration equal to 0 microseconds creates division-by-zero during rate calculations. | Detected by `sanitize_infinite_and_nan()`; replaced with the median of valid finite observations. |
| **Missing Values (`NaN`)** | `Flow Bytes/s` | Null packet payload representations in specific raw captures. | Imputed using column-level median; rows with > 50% missing values dropped. |
| **Duplicate Network Flows** | Identical 5-tuple records | Monitoring taps on both ingress and egress router interfaces capture the same packet stream twice. | Identified and deduplicated via `handle_duplicates()`, logging exact drop counts. |
| **Extreme Positive Skew** | `Flow Duration`, `Total Fwd Packets`, `Flow IAT Max` | Natural network traffic is heavy-tailed: most flows last < 100 ms, while long-lived TCP sessions last hours. | Stabilized using natural log transformations (`log1p(Flow Duration)`). |

---

## 4. CLASS DISTRIBUTION & NATURAL IMBALANCE

```
+-------------------------------------------------------------------------+
|                  CIC-IDS2017 CLASS DISTRIBUTION PROFILE                 |
+------------------------------------+---------------+--------------------+
| CLASS NAME                         | FLOW COUNT    | PERCENTAGE         |
+------------------------------------+---------------+--------------------+
| BENIGN                             | 2,273,097     | 80.30%             |
| DoS Hulk                           | 231,073       |  8.16%             |
| PortScan                           | 158,930       |  5.61%             |
| DDoS                               | 128,027       |  4.52%             |
| DoS GoldenEye                      |  10,293       |  0.36%             |
| FTP-Patator                        |   7,938       |  0.28%             |
| SSH-Patator                        |   5,897       |  0.21%             |
| DoS slowloris                      |   5,796       |  0.20%             |
| DoS Slowhttptest                   |   5,499       |  0.19%             |
| Bot                                |   1,966       |  0.07%             |
| Web Attack - Brute Force           |   1,507       |  0.05%             |
| Web Attack - XSS                   |     652       |  0.02%             |
| Infiltration                       |      36       |  0.001%            |
| Web Attack - SQL Injection         |      21       |  0.0007%           |
| Heartbleed                         |      11       |  0.0004%           |
+------------------------------------+---------------+--------------------+
| TOTAL                              | 2,830,743     | 100.00%            |
+------------------------------------+---------------+--------------------+
```

### Critical Takeaway for Phase 3 Model Training:
The bottom 6 attack classes combined account for fewer than **0.15%** of the entire dataset. A model predicting exclusively `BENIGN` achieves **80.3% accuracy** while offering zero intrusion detection capability. Models must be optimized and evaluated for **Precision-Recall AUC (PR-AUC)** and **Macro F1-Score**.
