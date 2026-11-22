# NeuralShield AI — Machine Learning Data Readiness Specification
**Document:** `docs/ML_DATA_PREPARATION.md`  
**Purpose:** Phase 3 Architecture Recommendations & Safeguard Specifications  

---

## 1. Cross-Validation & Splitting Architecture

### The Pitfall of Random Splitting
Standard random k-fold cross-validation (`train_test_split(shuffle=True)`) is fundamentally flawed for CIC-IDS2017:
1. **Temporal Clustering:** Attack scripts generate bursts of hundreds of flows within seconds. Random splitting places flows from the exact same burst in both train and test sets, artificially inflating test accuracy above 99.8%.
2. **Duplicate Traffic:** High-volume repetitive attacks share identical feature vectors. Random splits lead to severe test-set memorization.

### Recommended Phase 3 Splitting Strategy
- **Day-Based Partitioning (Cross-Day Generalization):**
  - Train on Monday (Benign baseline) + Tuesday/Wednesday attacks.
  - Validate on Thursday (Web attacks & Infiltration).
  - Test on Friday (DDoS & PortScan).
- **Stratified Group-Based Splitting:** If cross-day partitioning is not feasible due to specific attack isolation, apply stratified temporal block splitting where test partitions are chronologically subsequent to training blocks.

---

## 2. Class Imbalance Strategy (Prohibiting Premature SMOTE)

In CIC-IDS2017, benign flows comprise >80% of all traffic, whereas attacks like *Heartbleed* (11 flows) or *Infiltration* (36 flows) represent extreme minorities.

### Prescribed Methodology for Phase 3:
1. **Strict Train-Fold Isolation:** Resampling algorithms (e.g. SMOTE, RandomUnderSampler) must **never** be applied prior to splitting. Synthetic interpolations crossing into validation/test partitions corrupt real-world evaluation.
2. **Algorithmic Cost-Sensitive Learning:** Prefer class-weighted loss functions (`class_weight='balanced'` in Random Forest / SVM) or focal loss in gradient boosting before attempting synthetic oversampling.
3. **Primary Evaluation Metrics:** Prohibit raw accuracy. Use **Precision-Recall AUC (PR-AUC)**, **Macro F1-Score**, and **False Positive Rate at 99% Recall**.

---

## 3. Scaling & Transformation Directives
- **Robust Scaling:** Features like `flow_duration` and `flow_bytes_per_sec` contain legitimate extreme outliers. Standard scaling ($\mu=0, \sigma=1$) is distorted by extreme values. Use `RobustScaler` (median and IQR-based) or `QuantileTransformer`.
- **Fit on Train Only:** `scaler.fit(X_train)` and `scaler.transform(X_test)`. Never call `fit` on combined datasets.
