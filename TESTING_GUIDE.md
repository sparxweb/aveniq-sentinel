# Aveniq Sentinel — Engineering Testing Guide

**Document:** `TESTING_GUIDE.md`  
**Product:** Aveniq Sentinel  
**Company:** Aveniq  
**Repository:** [https://github.com/sparxweb/aveniq-sentinel](https://github.com/sparxweb/aveniq-sentinel)  
**Audience:** Data Scientists, ML Engineers, QA Engineers, Contributors  
**Test Framework:** `pytest 9.2.0`  
**Status:** **54 Tests Passing (100% Pass Rate)**  

---

## 1. Testing Philosophy & Standards

Aveniq Sentinel employs a defensive, rigorous testing methodology designed to validate mathematical accuracy, memory stability, and data security:

- **Mathematical Correctness:** Tests verify that rate calculations, ratios, and quantile statistics match theoretical expectations without numerical artifacts.
- **Data Leakage Immunity:** Tests verify that target identifiers (`Flow ID`, `Source IP`, `Destination IP`, `Timestamp`) are strictly removed and that exact duplicate flows are discarded before cross-validation partitioning.
- **Edge-Case Resilience:** Tests explicitly evaluate non-ideal conditions: empty DataFrames, missing files, corrupted columns, infinite rates, and single-class inputs.
- **Zero Mock Fabrications:** All test fixtures utilize realistic synthetic network flows with verified distributions.

---

## 2. Test Suite Architecture

The test suite is structured across 10 specialized test modules in `tests/`:

| Module | Scope Tested | Test Count |
|---|---|:---:|
| [`tests/test_cleaning.py`](tests/test_cleaning.py) | Header normalization, duplicate Fwd Header Length removal, infinity sanitization, exact duplicate dropping, and label standardization. | 5 |
| [`tests/test_loader.py`](tests/test_loader.py) | Dataset loading, lossless numeric downcasting, deterministic stratified sampling, chunked generators, and selective column reading. | 9 |
| [`tests/test_features.py`](tests/test_features.py) | Domain feature engineering (`packet_symmetry_ratio`, `byte_symmetry_ratio`, `syn_to_ack_ratio`), feature cataloging, and target leakage stripping. | 4 |
| [`tests/test_validation.py`](tests/test_validation.py) | Data quality auditing, numerical anomaly detection, quality index scoring, and the automated 6-file report generation suite. | 6 |
| [`tests/test_comparisons.py`](tests/test_comparisons.py) | Non-parametric behavioral contrasts (medians, IQR, divergence ratios) and TCP control flag activation rates. | 3 |
| [`tests/test_statistics.py`](tests/test_statistics.py) | Quantile calculations, descriptive statistics, and multicollinearity pair detection ($|r| \ge 0.90$). | 4 |
| [`tests/test_schema.py`](tests/test_schema.py) | Single-file schema inspection and cross-file schema consistency comparisons. | 3 |
| [`tests/test_charts.py`](tests/test_charts.py) | All Plotly chart generators: class distributions, heatmaps, histograms with log toggles, quality gauges, scatter plots, and empty-state fallbacks. | 11 |
| [`tests/test_entrypoints.py`](tests/test_entrypoints.py) | Primary `app.py`, package `src/neuralshield/dashboard.py`, `streamlit_app.py`, and all 5 operational page renderers. | 4 |
| [`tests/test_pipeline_edge_cases.py`](tests/test_pipeline_edge_cases.py) | Empty DataFrame exceptions, clean feature preservation, target leakage exclusion, lossless downcasting guarantees, and missing file error handling. | 5 |
| **Total Test Count** | | **54** |

---

## 3. Test Fixtures (`tests/conftest.py`)

Common fixtures are centralized in `tests/conftest.py`:

- `clean_synthetic_df`: Generates a pristine, normalized DataFrame with realistic network traffic metrics (packet counts, durations, ports, flags, and labels).
- `dirty_synthetic_df`: Generates a deliberately corrupted DataFrame containing raw unstripped whitespace in column headers (`" Flow Duration"`, `" Label "`), duplicate columns (`"Fwd Header Length.1"`), division-by-zero infinities (`+inf`, `-inf`), duplicate flow rows, and missing cells.

---

## 4. How to Execute Tests

### Run Full Test Suite (Recommended)
```powershell
# From project root
pytest tests/ -v
```

*Or via the virtual environment directly:*
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

### Run a Specific Test Module
```powershell
# Test charts only
pytest tests/test_charts.py -v

# Test pipeline edge cases only
pytest tests/test_pipeline_edge_cases.py -v
```

### Run with Short Tracebacks & Failure Early-Exit
```powershell
pytest tests/ -q --tb=short -x
```

### Run Application Syntax and Entrypoint Check
```powershell
python -c "import app; import streamlit_app; from neuralshield import dashboard; print('All entrypoints valid.')"
```

---

## 5. Adding New Tests

When contributing new capabilities in feature branches:
1. Create a corresponding test file in `tests/test_<feature>.py`.
2. Follow pytest conventions: prefix test functions with `test_`.
3. Test both the golden path and edge cases:
   - What happens if the input DataFrame is empty?
   - What happens if an expected column is missing?
   - What happens if the data contains `NaN` or `np.inf`?
4. Run `pytest tests/ -v` to confirm that all 54+ tests pass before committing.
