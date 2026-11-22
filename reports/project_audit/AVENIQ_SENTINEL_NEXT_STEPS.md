# AVENIQ SENTINEL // ENGINEERING ROADMAP & PHASE 3 SPRINT BACKLOG
**Product Name:** Aveniq Sentinel  
**Company:** Aveniq  
**GitHub Target:** [https://github.com/sparxweb/aveniq-sentinel](https://github.com/sparxweb/aveniq-sentinel)  
**Audit Date:** 2026-11-22 20:28:01 UTC  

---

## 1. PHASE 3 SPRINT BACKLOG: MACHINE LEARNING DETECTION ENGINE

With Phase 1 (Architecture & Research) and Phase 2 (Data Engineering & EDA) verified at 100%, the project is primed for Phase 3 execution:

```
+-------------------------------------------------------------------------------+
|                      PHASE 3 IMPLEMENTATION WORKFLOW                          |
+-------------------------------------------------------------------------------+
                                        |
       +--------------------------------+--------------------------------+
       |                                                                 |
+------v------+                                                   +------v------+
| Temporal CV |                                                   | Unsupervised|
| Partitioning|                                                   | Anomaly     |
+------+------+                                                   | Detection   |
       |                                                          +------^------+
+------v------+      +--------------------+      +-------------+         |
| Supervised  | ---> | Hyperparameter     | ---> | Metric      | --------+
| Classifiers |      | Optimization &     |      | Evaluation  |
| (RF, LGBM)  |      | Imbalance Handling |      | (PR-AUC, F1)|
+-------------+      +--------------------+      +-------------+
```

### Action Items:
1. **Temporal Cross-Validation Module (`src/neuralshield/models/split.py`):**
   - Implement temporal non-overlapping train/validation/test partitions based on CIC-IDS2017 flow timestamps.
   - Prevent data leakage from recurring persistent connections.
2. **Supervised Classifier Suite (`src/neuralshield/models/supervised.py`):**
   - **Baseline:** Logistic Regression with L2 regularization and inverse class frequency weighting.
   - **Primary Detector:** Balanced Random Forest Classifier (100 estimators, max depth 20).
   - **High-Velocity Detector:** LightGBM / XGBoost multi-class classifier with early stopping.
3. **Unsupervised Anomaly Detector (`src/neuralshield/models/anomaly.py`):**
   - Implement Isolation Forest trained strictly on benign baseline traffic to identify zero-day attacks.
   - Benchmark Local Outlier Factor (LOF) for high-density cluster divergence.
4. **Comprehensive Metric Evaluator (`src/neuralshield/models/evaluate.py`):**
   - Compute Precision-Recall AUC (PR-AUC), F1-Score (Macro and Weighted), and False Positive Rate at 99% Recall.
   - Output normalized confusion matrices and cost-weighted threat classification tables.
5. **Model Registry & Integrity Guard (`src/neuralshield/models/registry.py`):**
   - Serialize model weights alongside metadata JSON specifying training hyperparams, feature names, and SHA-256 checksums.

---

## 2. PHASE 4 SPRINT BACKLOG: NETWORK GRAPH INTELLIGENCE
1. **Graph Construction Pipeline (`src/neuralshield/intelligence/graph.py`):**
   - Construct directed bipartite communication graphs with edge weights reflecting packet volume and byte frequency.
2. **Centrality & Pivot Analysis:**
   - Calculate In-Degree and Out-Degree centrality to isolate scanning sources and exfiltration sinks.
   - Implement PageRank to identify Command & Control (C2) hub candidates.
3. **Graph Visualization Component (`app_pages/`):**
   - Render interactive NetworkX topologies within the Streamlit interface using PyVis / Plotly network layouts.

---
*Report verified by Aveniq Automated Quality Engine.*