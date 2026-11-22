# NeuralShield AI — System Architecture
**Document:** `docs/ARCHITECTURE.md`  
**Version:** 0.1.0 (Phase 1 Foundation)  

---

## 1. Architectural Philosophy

NeuralShield AI is engineered following clean architecture principles:
- **Separation of Concerns:** Core domain logic (`src/neuralshield`) is completely decoupled from presentation layers (`app_pages`, `streamlit_app.py`).
- **Defensive Data Handling:** No assumptions are made regarding file health. Ingestion modules validate encodings, column schemas, infinities, and missing values.
- **Leakage Prevention by Design:** Target leakage columns (IPs, IDs, Timestamps) and exact duplicate rows are strictly isolated prior to model preparation.

---

## 2. Component Diagram

```mermaid
flowchart TD
    subgraph Ingestion ["Data Ingestion & Discovery Layer"]
        RAW[("Raw CIC-IDS2017 CSVs")] --> DISC["discovery.py"]
        SAMPLE[("Synthetic Sample")] --> DISC
        DISC --> LOAD["loader.py (Chunk-Aware)"]
    end

    subgraph Sanitation ["Data Sanitation & Hygiene Layer"]
        LOAD --> COL_NORM["cleaning.py: normalize_column_names()"]
        COL_NORM --> REDUN["cleaning.py: drop_redundant_columns()"]
        REDUN --> INF_SAN["cleaning.py: sanitize_infinite_and_nan()"]
        INF_SAN --> DEDUP["cleaning.py: handle_duplicates()"]
        DEDUP --> LBL_NORM["cleaning.py: normalize_labels()"]
    end

    subgraph Validation ["Audit & Quality Validation Layer"]
        LBL_NORM --> AUDIT["validation.py: audit_dataframe_quality()"]
        AUDIT --> SCORE["Data Quality Index (0-100)"]
    end

    subgraph Analytics ["Analytics & Feature Engineering"]
        AUDIT --> STATS["statistics.py & distributions.py"]
        AUDIT --> CORR["correlations.py (Multicollinearity)"]
        AUDIT --> FEAT["features/engineering.py (Domain Derivations)"]
        AUDIT --> RISK["intelligence/risk_engine.py (Heuristic Baseline)"]
    end

    subgraph Presentation ["Cybersecurity Command Center UI"]
        STATS --> UI_EXP["app_pages/data_explorer.py"]
        SCORE --> UI_QUAL["app_pages/data_quality.py"]
        RISK --> UI_OVER["app_pages/overview.py"]
        UI_EXP --> APP["streamlit_app.py"]
        UI_QUAL --> APP
        UI_OVER --> APP
    end
```

---

## 3. Directory Layout & Module Responsibilities

```text
NeuralShield-AI/
├── streamlit_app.py               # Main UI entrypoint & global styling
├── requirements.txt               # Locked reproducible dependencies
├── pyproject.toml                 # Package definition & pytest config
├── config/
│   ├── settings.py                # Paths, taxonomy, color palette
│   └── logging_config.py          # Centralized logging setup
├── data/
│   ├── raw/cic_ids2017/           # Untracked official benchmark CSVs
│   ├── processed/                 # Sanitized Parquet/CSV outputs
│   ├── sample/                    # Verified synthetic demo fixture
│   └── external/                  # External reference datasets
├── src/neuralshield/
│   ├── data/                      # Discovery, loading, cleaning, validation
│   ├── analysis/                  # Statistics, distributions, correlations
│   ├── features/                  # Domain feature derivations & leakage guards
│   ├── intelligence/              # Heuristic cybersecurity risk scoring engine
│   ├── visualization/             # Command-center Plotly dark charts
│   └── utils/                     # Safe I/O, encodings, and validators
├── app_pages/                     # Streamlit presentation views
├── notebooks/                     # Exploratory Data Analysis notebook
└── tests/                         # Pytest test suite (21 unit tests)
```
