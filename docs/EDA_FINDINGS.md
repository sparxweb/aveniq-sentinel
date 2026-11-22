# NeuralShield AI — Phase 2 Exploratory Data Analysis & Empirical Findings
**Project:** NeuralShield AI — Intelligent Cyber Threat Detection & Network Intelligence Platform  
**Document:** `docs/EDA_FINDINGS.md`  
**Author:** NeuralShield AI Engineering Team  
**Date:** November 2026  
**Status:** Completed  

---

## 1. Executive Summary

This report documents the statistical, behavioral, and structural insights uncovered during Phase 2 Exploratory Data Analysis (EDA) of network flow telemetry. By contrasting normal network behavior (Benign) against distinct attack categories, we establish empirical baselines that will guide feature selection, dimensionality reduction, and model architecture in Phase 3.

---

## 2. Dataset Dimensions & Class Distribution

### 2.1 Scale and Imbalance Topology
The benchmark CIC-IDS2017 dataset comprises ~2.83 million flows across 15 distinct classes (1 benign, 14 attack types):
- **Benign Traffic:** ~80.3% of total flows across the 5 collection days.
- **High-Volume Attacks:**
  - DoS (Hulk, GoldenEye, Slowloris, SlowHTTPTest): ~8.9%
  - DDoS (LOIC): ~4.5%
  - PortScan: ~5.6%
- **Extreme Minority Attacks:**
  - Infiltration: < 0.002% (~36 records)
  - Heartbleed: < 0.0004% (~11 records)
  - Web Attack - SQL Injection: < 0.001% (~21 records)

### 2.2 Analytical Implications
- **Deceptive Accuracy:** A naive model predicting `Benign` for all flows achieves >80% accuracy while failing 100% of intrusion detection objectives.
- **Metric Mandate:** In Phase 3, accuracy must be superseded by **Precision-Recall AUC (PR-AUC)**, **Macro F1-Score**, and **False Alarm Rate (FAR)** at fixed sensitivity thresholds.
- **Resampling Strategy:** Resampling techniques (such as SMOTE or Tomek links) must strictly be applied within cross-validation training folds, never globally across the dataset.

---

## 3. Empirical Behavioral Contrasts: Benign vs. Attack

Using `neuralshield.analysis.comparisons`, we computed robust location (median) and scale (interquartile range, IQR) metrics along with divergence ratios:
$$\text{Divergence Ratio} = \frac{\text{Median}_{\text{Attack}} + \epsilon}{\text{Median}_{\text{Benign}} + \epsilon}$$

### 3.1 Flow Duration & Timing Dynamics
- **Benign Traffic:** Characterized by diverse, heavy-tailed duration profiles (median ~31,000 $\mu$s, with long-lived HTTP keep-alive, streaming, and background TCP connections).
- **Volumetric Attacks (DDoS, DoS Hulk):** Characterized by ultra-short, bursty flows (median < 1,000 $\mu$s). Attackers generate massive concurrent flow requests designed to exhaust server socket state tables without maintaining sessions.
- **Slow & Low Attacks (Slowloris, SlowHTTPTest):** Invert this behavior; flows deliberately prolong duration with microscopic byte transmissions to hold thread pools open indefinitely.

### 3.2 Packet Length & Byte Volume Asymmetry
- **Benign Sessions:** Exhibit balanced bidirectional communication. The forward path carries requests (headers, URLs), while the backward path carries larger responses (HTML, CSS, JSON payloads). The packet length distribution is bimodal (peaks at small ACK packets ~40–60 bytes and maximum segment size ~1460–1500 bytes).
- **DDoS / Floods:** Heavy forward packet volume with zero or minimal backward response packets (backward packet count median = 0 in SYN/UDP floods). The `packet_symmetry_ratio` approaches 1.0 (purely unidirectional forward traffic).
- **Infiltration / Data Exfiltration:** Characterized by anomalous forward payload sizes and abnormal flow byte rates.

### 3.3 TCP Flag Signatures
TCP control flags provide high-entropy discriminatory signatures:
- **PortScan:** Marked by elevated `SYN_FLAG_COUNT` and `RST_FLAG_COUNT` with near-zero `ACK_FLAG_COUNT`. Scanners issue rapid SYN or FIN probes across port ranges and tear down connections immediately.
- **SYN Floods:** High SYN flag density per flow with absent ACK flags.
- **Benign Traffic:** Consistent presence of `ACK`, `PSH`, and clean connection termination sequences.

---

## 4. Multicollinearity & Correlation Analysis

Using `neuralshield.analysis.correlations.detect_multicollinear_pairs()`, feature pairs with Pearson $|r| \ge 0.90$ were systematically mapped.

### 4.1 Highly Collinear Clusters
1. **Packet Counts:**
   - `total_fwd_packets` and `subflow_fwd_packets`: $r = 1.000$ (Identical for single-subflow captures).
   - `total_backward_packets` and `subflow_bwd_packets`: $r = 1.000$.
2. **Byte Volumes:**
   - `total_length_of_fwd_packets` and `subflow_fwd_bytes`: $r = 1.000$.
   - `total_length_of_bwd_packets` and `subflow_bwd_bytes`: $r = 1.000$.
3. **Segment & Packet Sizes:**
   - `fwd_packet_length_mean` and `avg_fwd_segment_size`: $r = 1.000$ (Semantically identical definitions in CICFlowMeter).
   - `bwd_packet_length_mean` and `avg_bwd_segment_size`: $r = 1.000$.
   - `average_packet_size` and `packet_length_mean`: $r \approx 0.998$.
4. **Header Lengths:**
   - `fwd_header_length` and `fwd_header_length.1`: $r = 1.000$ (Direct duplicate column bug).

### 4.2 Feature Reduction Strategy for Phase 3
Retaining perfectly collinear features introduces numerical instability in linear models, inflates memory footprint, and dilutes tree-based feature importance. In Phase 3:
- Drop subflow duplicate metrics (`subflow_*`).
- Drop redundant average segment sizes in favor of packet length means.
- Prioritize high-signal composite ratios: `packet_symmetry_ratio`, `byte_symmetry_ratio`, `syn_to_ack_ratio`, and `log_flow_duration`.

---

## 5. Machine Learning Readiness & Modeling Hypotheses

Based on Phase 2 EDA, the following hypotheses are established for Phase 3:

1. **Tree-Based Ensembles are Optimal:**
   - Features exhibit heavy skewness, extreme outliers, multimodal distributions, and sharp threshold boundaries (e.g. TCP flag counts). Non-parametric tree models (Random Forest, LightGBM, XGBoost) natively handle unscaled features and non-linear interactions without requiring strict Gaussian normalization.
2. **Validation Scheme Must Prevent Temporal Leakage:**
   - Due to network burstiness, adjacent flows share temporal correlation. Standard random cross-validation will overfit. Validation must utilize **Day-Based Holdout** (e.g. Train Monday–Thursday, Test Friday) or **Stratified Group K-Fold**.
3. **Class Imbalance Strategy:**
   - Due to extreme rarity (<0.01%) of certain attacks, cost-sensitive learning (`class_weight='balanced'`) and Focal Loss will outperform naive synthetic oversampling.
