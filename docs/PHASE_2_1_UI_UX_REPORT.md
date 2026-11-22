# AVENIQ SENTINEL — PHASE 2.1 UI/UX DESIGN SYSTEM & ERGONOMICS REPORT
**Product:** Aveniq Sentinel  
**Company:** Aveniq (sparxweb)  
**Interface Stack:** Streamlit 1.67.0 + Plotly 7.1.0 + Custom CSS Design System  
**Design Paradigm:** Dark SOC SaaS (Security Operations Center Command Center)  
**Date:** November 22, 2026  

---

## 1. DESIGN PHILOSOPHY & PALETTE SPECIFICATION

Aveniq Sentinel's user interface is purposefully engineered for cybersecurity analysts, SOC operators, and data scientists working in low-light operations environments. The design completely eschews default white themes and generic Bootstrap stylings in favor of an authoritative, high-contrast dark telemetry theme.

### Color Hierarchy
```
Background Deep:       #0B0F19  (Dark obsidian; reduces eye fatigue)
Container / Cards:     #101614  (Deep slate with subtle dark green tint)
Card Borders:          #1D2824  (Precision divider boundaries)
Primary Accent:        #10B981  (Emerald green: operational / clean status)
Secondary Accent:      #06B6D4  (Cyan telemetry: user inputs / custom data)
Warning Accent:        #F59E0B  (Amber: demonstration mode / partial state)
Critical Accent:       #EF4444  (Crimson: detected anomalies / errors)
Text Primary:          #E8F0EB  (Crisp platinum text for high legibility)
Text Muted / Subtitle: #8B9A91  (Muted sage for technical metadata)
```

---

## 2. COMPONENT ARCHITECTURE & ERGONOMICS

### 2.1 Standardized Banner & Header Architecture
Every operational center features a synchronized telemetry header displaying:
- Operational Center Title & Subtitle
- Active Data Source Transparency Banner
- Status Badge (`● OFFICIAL`, `● USER`, `● DEMO`, `● NO DATA`)
- Flow and Feature Count Badges
- Sandbox & Privacy Compliance Indicator (`Offline Sandbox • Zero Data Leakage`)

### 2.2 Operational Center Ergonomic Structure

1. **Center 1: Overview & Architecture (`app_pages/overview.py`)**
   - 4 Top-line Executive KPI cards: Benchmark Catalog Status, Active Data Source, Data Pipeline Health, Engineering Gate.
   - CIC-IDS2017 Benchmark Catalog tabular inventory with real file sizes.
   - Architectural Roadmap Tracker with Phase 1, Phase 2, and Phase 3 milestones.
   - **Live Component-Level Operational Health Grid**: Evaluates all 7 core platform engines in real-time with truthful status indicators and detailed diagnostics.

2. **Center 2: Flow Data Explorer (`app_pages/data_explorer.py`)**
   - Multi-mode Ingestion Selector: Synthetic Demonstration Sample, Custom Network CSV Upload, Raw Benchmark CSV Loader.
   - Summary Telemetry Bar displaying active source name, flow count, feature count (numeric vs categorical), and memory consumption.
   - Interactive Data Preview with customizable row slider.
   - Flow Scatter & Distribution Projection using dark SOC Plotly traces.

3. **Center 3: Data Quality & Hygiene Audit (`app_pages/data_quality.py`)**
   - Animated Quality Gauge displaying the 0-100 composite data hygiene score.
   - Missing Value, Infinite Value, and Duplicate Flow KPI cards.
   - Comprehensive column-level null and anomaly breakdown table.
   - One-click export for downloadable JSON and HTML quality audit reports.

4. **Center 4: Advanced EDA (`app_pages/eda_center.py`)**
   - 4 Analytical Tabs:
     - *Tab 1: Class Balance & Extreme Imbalance:* Pie and bar distributions highlighting the severe 80/20 class skew common to network traffic.
     - *Tab 2: Benign vs Attack Behavioral Contrast:* Feature divergence metrics, median ratio comparisons, and behavioral divergence bar charts.
     - *Tab 3: Feature Distributions & Skewness:* Interactive histogram, box plot, and skewness/kurtosis telemetry for selected flow metrics.
     - *Tab 4: Multicollinearity & Correlations:* Full Pearson correlation heatmap with high-collinearity pair identification (|r| > 0.85).

5. **Center 5: Ingestion & Processing Center (`app_pages/processing_center.py`)**
   - Memory Optimization Controls: Chunk size slider (10K to 250K rows) and lossless numeric downcasting toggle.
   - Live Memory Telemetry Card: Shows original float64 resident RAM vs optimized float32 RAM with exact percentage reduction.
   - One-Click Sanitation Pipeline Runner exporting cleansed datasets to `data/processed/` in Parquet or CSV.

---

## 3. ACCESSIBILITY & PERFORMANCE STANDARDS

- **Zero External Network Dependencies:** All fonts, styling, icons, and Plotly scripts render completely offline without CDN calls.
- **High Contrast Ratio:** Body text achieves a contrast ratio of > 8.5:1 against card backgrounds, exceeding WCAG AAA standards.
- **Session State Synchronization:** Any dataset uploaded or selected in one tab is immediately synchronized to `st.session_state["active_df"]` and visible across all operational centers without redundant disk re-reads.
