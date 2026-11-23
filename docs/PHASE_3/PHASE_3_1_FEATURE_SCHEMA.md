# AVENIQ SENTINEL — PHASE 3.1: MACHINE LEARNING FEATURE CONTRACT & SCHEMA SPECIFICATION

**Product:** Aveniq Sentinel  
**Company:** Aveniq  
**Author:** Principal Machine Learning Engineer & Cybersecurity ML Research Engineer  
**Status:** Approved & Implemented (`src/neuralshield/ml/feature_contract.py`)  
**Target Benchmark:** UNB CIC-IDS2017 Benchmark Dataset (8-File Suite, ~2.83M Flows)

---

## 1. Executive Summary & Purpose

In network intrusion detection systems (NIDS), subtle data leakage and malformed features frequently produce artificially inflated test performance (e.g., >99.9% accuracy) that catastrophically collapses in real-world deployment. The most egregious vectors of leakage and instability are:
1. **Direct Identity Leakage:** IP addresses, MAC addresses, port mappings, and timestamps that allow the model to memorize specific attacker infrastructure or session time rather than generalizable behavioral flow dynamics.
2. **Data Type Memory Explosion:** Using default `float64` / `int64` across ~2.83M records consumes over 2 GB of memory, causing out-of-memory (OOM) failures in constrained environments (e.g., standard free-tier Kaggle 16 GB RAM containers when training ensembles).
3. **Infinite and Malformed Values:** Division by zero in network flow rate statistics (`Flow Bytes/s`, `Flow Packets/s`) yielding IEEE `inf`, `-inf`, or `NaN`.
4. **Target Contamination:** Target labels inadvertently retained in feature matrices during unsupervised or semi-supervised anomaly modeling.

The **Aveniq Sentinel Feature Contract** defines an unyielding, programmatic specification for input feature verification, type downcasting, leakage rejection, and numeric sanitization.

---

## 2. Leakage Protection & Prohibited Column Catalog

Any dataset submitted to the training pipeline is audited against `PROHIBITED_LEAKAGE_COLUMNS`. If any of these fields are present in the feature matrix $X$, the contract immediately flags or drops them before downstream estimator consumption.

| Prohibited Feature / Pattern | Risk Categorization | Why It Causes Spurious Learning | Action Taken |
| :--- | :--- | :--- | :--- |
| `Flow ID` | **Critical Leakage** | Unique flow identifier; memorizes exact flows. | **REJECT / DROP** |
| `Source IP` / `Src IP` / `src_ip` | **Critical Leakage** | Model memorizes attacker IP (`192.168.10.50`, etc.) rather than attack characteristics. | **REJECT / DROP** |
| `Destination IP` / `Dst IP` / `dst_ip` | **Critical Leakage** | Model memorizes victim server IP (`192.168.10.51`, etc.). | **REJECT / DROP** |
| `Timestamp` / `Date` / `Time` | **Critical Leakage** | Enables temporal shortcut learning (e.g., "all flows at 10:15 AM are attacks"). | **REJECT / DROP** |
| `Source Port` / `Src Port` | **High Leakage Risk** | Ephemeral high ports (>1024) act as pseudo-identifiers; client ports vary randomly. | **REJECT / DROP** |
| `Destination Port` / `Dst Port` | **Contextual Leakage** | While well-known ports (80, 443, 21, 22) carry protocol meaning, raw port numbers cause models to classify all port 21 traffic as FTP-Patator. Sanitized into high-level protocol flags in feature engineering rather than raw IDs. | **REJECT / DROP** (from raw continuous feature matrix) |
| `Label` / `Attack_Cat` | **Target Leakage** | True classification labels must never enter feature matrix $X$. | **EXTRACT TO $y$** |

---

## 3. Approved Core ML Feature Matrix (78 Features)

All valid ML inputs must conform to continuous or discrete numerical definitions, downcast to IEEE 754 single precision (`float32`).

### 3.1 Flow Timing & Duration Features
- `Flow Duration` (float32, $\mu s$): Total duration of bidirectional flow.
- `Flow IAT Mean`, `Flow IAT Std`, `Flow IAT Max`, `Flow IAT Min` (float32, $\mu s$): Inter-arrival time between flow packets.
- `Fwd IAT Total`, `Fwd IAT Mean`, `Fwd IAT Std`, `Fwd IAT Max`, `Fwd IAT Min` (float32, $\mu s$): Inter-arrival time of forward packets.
- `Bwd IAT Total`, `Bwd IAT Mean`, `Bwd IAT Std`, `Bwd IAT Max`, `Bwd IAT Min` (float32, $\mu s$): Inter-arrival time of backward packets.
- `Active Mean`, `Active Std`, `Active Max`, `Active Min` (float32, $\mu s$): Time flow was active before going idle.
- `Idle Mean`, `Idle Std`, `Idle Max`, `Idle Min` (float32, $\mu s$): Time flow was idle before becoming active.

### 3.2 Packet Volume & Rate Statistics
- `Total Fwd Packets`, `Total Backward Packets` (float32): Packet counts in forward and backward directions.
- `Total Length of Fwd Packets`, `Total Length of Bwd Packets` (float32, bytes): Payload byte aggregates.
- `Flow Bytes/s`, `Flow Packets/s` (float32, rate): Flow throughput metrics. *Requires clipping of inf values.*
- `Fwd Packets/s`, `Bwd Packets/s` (float32, rate): Directional packet throughput rates.
- `Down/Up Ratio` (float32): Ratio of download (backward) to upload (forward) packets.
- `Average Packet Size`, `Avg Fwd Segment Size`, `Avg Bwd Segment Size` (float32, bytes): Segment-level averages.

### 3.3 Packet Length Distribution Metrics
- `Fwd Packet Length Max`, `Fwd Packet Length Min`, `Fwd Packet Length Mean`, `Fwd Packet Length Std` (float32, bytes).
- `Bwd Packet Length Max`, `Bwd Packet Length Min`, `Bwd Packet Length Mean`, `Bwd Packet Length Std` (float32, bytes).
- `Min Packet Length`, `Max Packet Length`, `Packet Length Mean`, `Packet Length Std`, `Packet Length Variance` (float32, bytes).

### 3.4 TCP Header, Flag & Window Metrics
- `Fwd Header Length`, `Bwd Header Length` (float32, bytes): Directional IP/TCP header lengths.
- `FIN Flag Count`, `SYN Flag Count`, `RST Flag Count`, `PSH Flag Count`, `ACK Flag Count`, `URG Flag Count`, `CWE Flag Count`, `ECE Flag Count` (float32, binary indicator 0.0 or 1.0): TCP state transition counters.
- `Fwd PSH Flags`, `Bwd PSH Flags`, `Fwd URG Flags`, `Bwd URG Flags` (float32, binary indicator): Directional flag counts.
- `Init_Win_bytes_forward`, `Init_Win_bytes_backward` (float32, bytes): Initial TCP window byte sizes (crucial for OS/client fingerprinting without IP leakage).
- `act_data_pkt_fwd` (float32): Number of forward packets carrying at least 1 byte of TCP data payload.
- `min_seg_size_forward` (float32, bytes): Minimum segment size observed in forward direction.

### 3.5 Bulk Transfer Sub-Flow Metrics
- `Fwd Avg Bytes/Bulk`, `Fwd Avg Packets/Bulk`, `Fwd Avg Bulk Rate` (float32).
- `Bwd Avg Bytes/Bulk`, `Bwd Avg Packets/Bulk`, `Bwd Avg Bulk Rate` (float32).
- `Subflow Fwd Packets`, `Subflow Fwd Bytes`, `Subflow Bwd Packets`, `Subflow Bwd Bytes` (float32).

---

## 4. Missing Value, Infinity & Extreme Outlier Handling

In raw network capture processing, zero-duration flows cause division-by-zero errors in rate calculations.

```
                  ┌───────────────────────────────┐
                  │ Raw CSV Stream / DataFrame    │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │ Column Normalization & Strip  │
                  │ (Whitespace removed, lowercase│
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │ Leakage Column Quarantine     │
                  │ (IPs, Timestamps, Ports, IDs) │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │ IEEE Inf / -Inf Replacement   │
                  │ Replace with NaN, then        │
                  │ impute with Column Median     │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │ NaN Imputation (Median)       │
                  │ Fallback: 0.0 if all NaN      │
                  └──────────────┬────────────────┘
                                 │
                                 ▼
                  ┌───────────────────────────────┐
                  │ Float32 Downcasting & Matrix  │
                  │ Memory optimization (~50% dec)│
                  └───────────────────────────────┘
```

1. **Infinity Sanitization:** All positive infinity (`np.inf`) and negative infinity (`-np.inf`) are converted to `np.nan`.
2. **Median Imputation:** NaNs are replaced with the pre-computed training set median for each feature. If a column is entirely null, it is zero-filled.
3. **No Row Deletion in Evaluation:** While corrupt rows may be audited during profiling, test evaluation matrices must maintain shape integrity to preserve true flow distribution metrics.

---

## 5. Memory Optimization Protocol

| Data Type | Memory Per 1M Rows (78 Features) | Memory for Full CIC-IDS2017 (2.83M Rows) | Stability & Precision |
| :--- | :--- | :--- | :--- |
| `float64` (Default Pandas) | ~624 MB | ~1,766 MB (~1.77 GB) | Excessive 64-bit precision; double memory pressure |
| `float32` (Aveniq Contract) | **~312 MB** | **~883 MB (~0.88 GB)** | **Full dynamic range for network metrics; 50% memory reduction** |

By strictly enforcing `float32` downcasting:
- Ensembles (Random Forest, Gradient Boosting) train substantially faster.
- Memory headroom remains available in Kaggle 16 GB RAM limits for validation matrix copies and cross-validation folds.

---

## 6. Implementation Reference

The feature contract is programmatically executed via:
```python
from neuralshield.ml import FeatureContract

contract = FeatureContract()

# Validate incoming dataframe for leakage
validation_results = contract.validate_dataframe(df)
if not validation_results["valid"]:
    print(f"Leakage detected: {validation_results['violations']}")

# Prepare sanitized X and y matrices
X, y = contract.prepare_feature_matrix(df, label_col="label")
assert X.dtype == np.float32
assert not np.isnan(X).any()
assert not np.isinf(X).any()
```
