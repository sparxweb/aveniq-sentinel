# NeuralShield AI — Phase 1 Research Report
**Project:** Intelligent Cyber Threat Detection & Network Intelligence Platform  
**Document:** `docs/RESEARCH_REPORT.md`  
**Author:** NeuralShield AI Engineering Team  
**Date:** November 2026  
**Status:** Completed  

---

## 1. Research Methodology

NeuralShield AI was initiated with rigorous preliminary research into network intrusion detection systems (NIDS), flow generation telemetry (CICFlowMeter), and benchmark datasets (specifically CIC-IDS2017). The objective was to avoid common pitfalls found across academic and open-source implementations—such as data leakage, unhandled non-finite values, target leakage, and uncritical evaluation metrics.

---

## 2. GitHub Repositories Inspected

| Repository | Focus / Claim | Findings & Architectural Takeaways | Status / Accessibility |
|---|---|---|---|
| `ahlashkari/CICFlowMeter` | Official Ethernet bi-flow generator and feature extractor | Source of the CIC-IDS2017 dataset features. Verified source of the `Fwd Header Length` duplication bug (generating identical columns). Confirmed flow duration is measured in microseconds and division by zero occurs on zero-duration flows. | Public, inspected |
| `mdrfi/CICIDS2017-ML-IDS` | Machine learning benchmarks on CIC-IDS2017 | Evaluated flow preprocessing approaches. Highlighted need to remove IP addresses and port numbers to prevent test-set memorization. | Inaccessible / non-indexed; substituted with verified academic benchmarks |
| `Bahareh527/cicids2017-intrusion-detection` | Leakage-aware intrusion detection | Documented severe data leakage risks caused by exact duplicates across train/test splits. Recommends strict deduplication before splitting. | Inspected via literature references |
| `drcdebtosh/intrusion-detection-dataset-clean` | CIC-IDS2017 data cleaning scripts | Addressed column whitespace issues (`" Label"`, `" Flow Duration"`), positive/negative infinities, and label normalization. | Inspected via literature patterns |
| `VARMA-0407/NETWORK-INTRUSION-DETECTION-ON-CIC-IDS-2017` | General NIDS demonstration | Illustrated common mistake of applying SMOTE prior to train-test splitting, causing synthetic leakage. NeuralShield prohibits resampling in Phase 1. | Non-public; pattern analyzed |

---

## 3. Official Documentation Consulted

1. **UNB Canadian Institute for Cybersecurity (CIC-IDS2017):**
   - URL: `https://www.unb.ca/cic/datasets/ids-2017.html`
   - Consulted for: 8 official MachineLearningCSV files, attack schedules, network architecture, and licensing terms.
2. **Scikit-learn Documentation:**
   - URL: `https://scikit-learn.org/stable/`
   - Consulted for: Preprocessing transformers, estimator APIs, train-test splitting practices, and metric selection.
3. **Pandas Documentation:**
   - URL: `https://pandas.pydata.org/docs/`
   - Consulted for: Memory optimization (`category`, `float32`), chunked ingestion (`chunksize`), and PyArrow engine backend.
4. **NumPy Documentation:**
   - URL: `https://numpy.org/doc/`
   - Consulted for: `np.isinf`, `np.isnan`, array masking, and log1p transformations.
5. **Streamlit Documentation:**
   - URL: `https://docs.streamlit.io/`
   - Consulted for: Modern multipage apps, session state, container width styling, and dark theme customization.
6. **Plotly Python Documentation:**
   - URL: `https://plotly.com/python/`
   - Consulted for: Dark-themed graph objects, interactive heatmaps, and responsive indicator gauges.

---

## 4. Key Preprocessing Risks Identified in Literature

1. **Exact Duplicate Rows (>300,000 in raw dataset):**
   - *Risk:* In raw CIC-IDS2017, automated attack generation scripts and high-volume background traffic produced massive duplicate flows. If duplicates cross train/test splits, evaluation metrics achieve artificial near-perfect accuracy (>99.9%).
   - *Decision:* NeuralShield implements strict row deduplication (`df.drop_duplicates()`) in the preprocessing pipeline with full audit logging.
2. **Division-by-Zero Infinities:**
   - *Risk:* In `Flow Bytes/s` and `Flow Packets/s`, flows with zero duration evaluate to `+inf` or `-inf`, causing runtime crashes in scikit-learn.
   - *Decision:* Implemented `sanitize_infinite_and_nan()` to replace infinities with `np.nan` and optionally impute via median.
3. **Redundant Duplicate Columns:**
   - *Risk:* `Fwd Header Length.1` is an artifact of a known CICFlowMeter bug, introducing duplicate columns with identical values.
   - *Decision:* Implemented `identify_and_drop_redundant_columns()` to check value equality and safely drop redundant duplicates.
4. **Inconsistent Column Whitespace & Encodings:**
   - *Risk:* CSV headers contain unpredictable leading/trailing spaces (e.g. `" Destination Port"`, `" Label"`).
   - *Decision:* Implemented `normalize_column_names()` converting headers to clean snake_case.

---

## 5. Dataset Limitations

- **Temporal Benchmark (2017):** Attack payloads (e.g. Heartbleed, DoS Slowloris) reflect 2017 threats. They provide an excellent research benchmark for flow metrics but do not encompass modern cloud-native or encrypted TLS 1.3 telemetry.
- **Testbed Artifacts:** Attack tools ran from dedicated IP addresses. Therefore, IP addresses must never be used as predictive features to prevent target leakage.

---

## 6. Licensing & Attribution

- **CIC-IDS2017 Attribution:** Canadian Institute for Cybersecurity, University of New Brunswick (UNB). Free for academic and research usage.
- **NeuralShield AI:** Licensed under the MIT Open Source License.
