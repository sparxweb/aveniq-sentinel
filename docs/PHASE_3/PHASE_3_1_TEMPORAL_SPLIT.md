# AVENIQ SENTINEL — PHASE 3.1: CHRONOLOGICAL TEMPORAL SPLITTING STRATEGY
**Product:** Aveniq Sentinel  
**Company:** Aveniq  
**Date:** November 23, 2026  
**Evaluation Paradigm:** Strict Day-Based Chronological Partitioning  
**Guaranteed Safeguards:** Zero Chronological Leakage, Zero Row-Level Contamination, Transparent Novel Attack Tracking  

---

## 1. WHY RANDOM K-FOLD SPLITTING FAILS ON NETWORK TRAFFIC

Standard machine learning practitioners frequently apply random row-level k-fold cross-validation (`train_test_split(shuffle=True)`) to network intrusion datasets. In network security, **random splitting creates severe, fatal data leakage**:

1. **Microsecond Burst Contamination:** Cyber attacks (e.g., DoS, PortScan, Brute-Force) generate thousands of identical flow packets within milliseconds from the same IP address and socket pair. Random row-level splitting places 80% of these burst packets in the training set and 20% in the test set.
2. **Memorization vs Generalization:** The model memorizes exact packet lengths, ephemeral port numbers, and inter-arrival intervals of that specific burst, achieving a deceptively high test score (e.g., 99.9% accuracy, 0.999 F1).
3. **Catastrophic Real-World Failure:** When deployed in a production SOC, the model is exposed to future traffic originating hours or days later with different timing dynamics and IP addresses, resulting in catastrophic failure.

**Aveniq Sentinel enforces strict chronological temporal splitting**: Models trained on historical days must generalize forward to future, unseen days.

---

## 2. TEMPORAL BOUNDARY DESIGN

The 5-day capture timeline is partitioned chronologically into 3 distinct operational windows:

```
MONDAY (July 3)     TUESDAY (July 4)     WEDNESDAY (July 5)     THURSDAY (July 6)     FRIDAY (July 7)
[---- Pure Benign --][-- FTP/SSH Patator --][-- DoS / Heartbleed --] [--- Web / Infiltration ---][-- Botnet / PortScan / DDoS --]
└─────────────────────────────────────────────────────────────┘ └─────────────────────────────────────────────┘
                TRAINING & VALIDATION PERIOD                                      FINAL UNTOUCHED TEST PERIOD
               (~1.67 Million Flow Records)                                       (~1.16 Million Flow Records)
               [ 80% Train  |  20% Chronological Val ]
```

### 1. Training Period (Monday - Wednesday)
- **Monday:** 529,918 flows (Benign baseline).
- **Tuesday:** 445,909 flows (Benign + FTP-Patator, SSH-Patator).
- **Wednesday Morning:** DoS Hulk, DoS GoldenEye, DoS Slowloris, DoS SlowHTTPTest, Heartbleed.
- **Total Training Pool:** ~1,668,530 flows.

### 2. Validation Period (Late Wednesday)
- Carved chronologically from the end of Wednesday's traffic (or a 20% temporal slice of the training period).
- Used for hyperparameter tuning, tree depth calibration, and anomaly threshold selection.

### 3. Final Untouched Test Period (Thursday - Friday)
- **Thursday:** 458,968 flows (Web Attacks, Infiltration).
- **Friday:** 703,245 flows (Botnet, PortScan, DDoS).
- **Total Test Pool:** ~1,162,213 flows.
- **Rule:** This data remains completely untouched until final model certification.

---

## 3. UNSEEN ATTACK VECTORS & OUT-OF-DISTRIBUTION (OOD) EVALUATION

A critical finding uncovered during Phase 3.1 profiling is that **attack categories are not uniformly distributed across days**:

```
+---------------------------------------------------------------------------------+
|                        ATTACK VECTOR TEMPORAL TAXONOMY                          |
+------------------------------------+--------------------------------------------+
| KNOWN TRAINING ATTACKS             | UNSEEN TEST ATTACKS                        |
| (Present in Mon - Wed)             | (ONLY appear in Thu - Fri)                 |
+------------------------------------+--------------------------------------------+
| • FTP-Patator                      | • Web Attack - Brute Force                 |
| • SSH-Patator                      | • Web Attack - XSS                         |
| • DoS Hulk                         | • Web Attack - SQL Injection               |
| • DoS GoldenEye                    | • Infiltration                             |
| • DoS slowloris                    | • Botnet (Ares)                            |
| • DoS Slowhttptest                 | • PortScan                                 |
| • Heartbleed                       | • DDoS (LOIC)                              |
+------------------------------------+--------------------------------------------+
```

### Evaluation Protocol for Unseen Classes:
1. **Never Silently Drop Unseen Classes:** The test dataset must reflect realistic network conditions where attackers deploy novel tactics.
2. **Two-Tier Test Evaluation:**
   - **Tier 1 (Known Attack Evaluation):** Evaluates multi-class supervised models on classes present in training.
   - **Tier 2 (Novelty / Zero-Day Detection):** Evaluates unsupervised anomaly detectors (Isolation Forest) and binary intrusion classifiers on the **unseen attack test set**. Measures whether the model successfully flags novel attacks as anomalous without having ever seen them during training.

---

## 4. LEAKAGE PREVENTION CONTROLS

Before any feature vectors are generated from temporal splits, the following columns are unconditionally purged:
- `Timestamp`: Prevents models from using chronological hour-of-day as an attack proxy.
- `Source IP` & `Destination IP`: Eliminates attacker/victim IP memorization.
- `Flow ID`: Drops artificial socket identifiers.
- `Source Port`: Drops ephemeral client-side port numbers.
