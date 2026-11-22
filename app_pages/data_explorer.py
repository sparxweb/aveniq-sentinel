"""Data Explorer page: Dataset loading, preview, column schema, sampling, and interactive filtering."""

import streamlit as st
import pandas as pd
from pathlib import Path
from config.settings import SAMPLE_DATA_DIR, RAW_DATA_DIR, UIThemeConfig
from neuralshield.data.loader import DatasetLoader, sample_dataframe
from neuralshield.data.source_manager import (
    detect_data_source,
    render_data_source_banner,
    render_onboarding_guide,
    load_active_dataset,
)
from neuralshield.visualization.charts import (
    plot_class_distribution,
    plot_flow_scatter,
)

theme = UIThemeConfig()


def render_data_explorer():
    """Renders the interactive data exploration console with sampling and projection."""
    st.markdown(
        """
        <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 18px 20px; margin-bottom: 20px;">
            <h2 style="color: #E8F0EB; margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.3px;">
                DATA EXPLORER // FLOW TELEMETRY INSPECTION
            </h2>
            <p style="color: #8B9A91; margin: 4px 0 0 0; font-size: 13px;">
                Inspect network flow schema, distribution of flow durations, packet volumes, and filter telemetry.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Data source selection sidebar
    st.sidebar.markdown(
        "<div style='font-size: 11px; color: #8B9A91; font-weight: 600; text-transform: uppercase; margin-bottom: 6px;'>Dataset Input</div>",
        unsafe_allow_html=True,
    )
    data_option = st.sidebar.radio(
        "Select Dataset Input",
        ["Synthetic Demonstration Sample", "Upload Custom Network CSV", "Raw Directory CSV"],
        label_visibility="collapsed",
    )

    df = None
    source_name = ""

    if data_option == "Synthetic Demonstration Sample":
        sample_path = SAMPLE_DATA_DIR / "cic_ids2017_sample.parquet"
        csv_sample = SAMPLE_DATA_DIR / "cic_ids2017_sample.csv"
        if sample_path.is_file():
            df = pd.read_parquet(sample_path)
            source_info = detect_data_source(df, source_name="Synthetic Demonstration Fixture", source_path=sample_path)
        elif csv_sample.is_file():
            df = pd.read_csv(csv_sample)
            source_info = detect_data_source(df, source_name="Synthetic Demonstration Fixture (CSV)", source_path=csv_sample)
        else:
            source_info = detect_data_source(None)
            st.warning("Sample dataset not found at `data/sample/`. Please verify project repository.")

    elif data_option == "Upload Custom Network CSV":
        uploaded = st.sidebar.file_uploader("Upload Network Flow CSV", type=["csv"])
        if uploaded is not None:
            try:
                df = pd.read_csv(uploaded, low_memory=False)
                source_info = detect_data_source(df, source_name=f"Custom Upload: {uploaded.name}")
            except Exception as e:
                st.error(f"Failed to read CSV: {e}")
                source_info = detect_data_source(None)
        else:
            df, source_info = load_active_dataset()

    elif data_option == "Raw Directory CSV":
        raw_files = list(RAW_DATA_DIR.glob("*.csv"))
        if raw_files:
            chosen = st.sidebar.selectbox("Choose Benchmark File", [f.name for f in raw_files])
            try:
                loader = DatasetLoader()
                df = loader.load_single_file(RAW_DATA_DIR / chosen, nrows=50_000)
                source_info = detect_data_source(df, source_name=f"CIC-IDS2017 Raw: {chosen}", source_path=RAW_DATA_DIR / chosen)
            except Exception as e:
                st.error(f"Error loading raw CSV: {e}")
                source_info = detect_data_source(None)
        else:
            st.info("No raw CSVs found in `data/raw/cic_ids2017/`. Using active dataset instead.")
            df, source_info = load_active_dataset()

    if df is not None:
        st.session_state["active_df"] = df
        st.session_state["data_source_info"] = source_info

    # Render standardized data source transparency banner
    render_data_source_banner(source_info)

    # Display empty state if no dataset loaded
    if df is None or df.empty:
        render_onboarding_guide()
        return

    # Data Summary Telemetry Bar
    mem_kb = df.memory_usage(deep=True).sum() / 1024
    mem_str = f"{mem_kb / 1024:.2f} MB" if mem_kb >= 1024 else f"{mem_kb:.1f} KB"
    numeric_count = len(df.select_dtypes(include=["number"]).columns)
    categoric_count = len(df.columns) - numeric_count

    st.markdown(
        f"""
        <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 12px 16px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <div style="font-size: 13px; color: #E8F0EB;">
                <span style="color: #8B9A91;">Active Source:</span> <b>{source_info.get('source_name', 'Active Dataset')}</b>
            </div>
            <div style="display: flex; gap: 16px; font-size: 12px; color: #8B9A91;">
                <span>Rows: <b style="color: #16C784;">{len(df):,}</b></span>
                <span>Columns: <b style="color: #E8F0EB;">{len(df.columns)}</b> ({numeric_count} num, {categoric_count} cat)</span>
                <span>Memory: <b style="color: #E8F0EB;">{mem_str}</b></span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Search and Filter Toolbar
    f_col1, f_col2 = st.columns([3, 1])
    with f_col1:
        search_query = st.text_input("Filter Flow Records by Keyword (Column or Label)", placeholder="e.g. Benign, DDoS, PortScan, 443, 80")
    with f_col2:
        row_limit = st.slider("Display Limit", min_value=10, max_value=min(1000, len(df)), value=min(100, len(df)), step=10)

    # Filter records
    display_df = df
    if search_query:
        mask = df.astype(str).apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
        display_df = df[mask]
        st.caption(f"Showing {len(display_df):,} matching flows out of {len(df):,} total records.")

    # Data Tabs
    t_records, t_scatter, t_schema = st.tabs(["Flow Records Table", "Bivariate Telemetry Scatter", "Column Schema Details"])

    with t_records:
        st.dataframe(display_df.head(row_limit), use_container_width=True)

    with t_scatter:
        numeric_cols = list(df.select_dtypes(include=["number"]).columns)
        if len(numeric_cols) >= 2:
            s_c1, s_c2, s_c3 = st.columns(3)
            with s_c1:
                x_axis = st.selectbox("X-Axis Telemetry", numeric_cols, index=0)
            with s_c2:
                default_y = 1 if len(numeric_cols) > 1 else 0
                y_axis = st.selectbox("Y-Axis Telemetry", numeric_cols, index=default_y)
            with s_c3:
                label_candidates = [c for c in df.columns if "label" in c.lower()]
                color_axis = label_candidates[0] if label_candidates else None
                st.markdown(f"<div style='font-size: 12px; color: #8B9A91; margin-top: 28px;'>Color mapping: <b>{color_axis or 'None'}</b></div>", unsafe_allow_html=True)

            scatter_fig = plot_flow_scatter(df, x_col=x_axis, y_col=y_axis, color_col=color_axis)
            st.plotly_chart(scatter_fig, use_container_width=True)
        else:
            st.info("Insufficient numeric columns for scatter visualization.")

    with t_schema:
        schema_records = []
        for col in df.columns:
            schema_records.append({
                "Column Name": col,
                "Data Type": str(df[col].dtype),
                "Non-Null Count": int(df[col].notna().sum()),
                "Missing Count": int(df[col].isna().sum()),
                "Unique Values": int(df[col].nunique()),
            })
        st.dataframe(pd.DataFrame(schema_records), use_container_width=True, hide_index=True)
