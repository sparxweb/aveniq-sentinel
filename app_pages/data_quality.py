"""Data Quality page: Missing values, infinite values, deduplication, anomalies, and quality audit."""

import json
import streamlit as st
import pandas as pd
from pathlib import Path
from config.settings import SAMPLE_DATA_DIR, RAW_DATA_DIR, DATA_QUALITY_REPORTS_DIR, UIThemeConfig
from neuralshield.data.source_manager import (
    load_active_dataset,
    render_data_source_banner,
    render_onboarding_guide,
)
from neuralshield.data.validation import audit_dataframe_quality, inspect_numerical_anomalies
from neuralshield.data.cleaning import (
    normalize_column_names,
    identify_and_drop_redundant_columns,
    sanitize_infinite_and_nan,
    handle_duplicates,
    normalize_labels,
)
from neuralshield.visualization.charts import (
    plot_quality_gauge,
    plot_correlation_heatmap,
)

theme = UIThemeConfig()


def render_data_quality():
    """Renders the Data Quality and Hygiene Audit console."""
    st.markdown(
        """
        <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 18px 20px; margin-bottom: 20px;">
            <h2 style="color: #E8F0EB; margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.3px;">
                DATA QUALITY // INTEGRITY & HYGIENE AUDIT
            </h2>
            <p style="color: #8B9A91; margin: 4px 0 0 0; font-size: 13px;">
                Audit missing values, non-finite infinity artifacts, duplicate network flows, and numerical consistency.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Load dataset through unified source manager
    raw_df, source_info = load_active_dataset()
    render_data_source_banner(source_info)

    if raw_df is None or raw_df.empty:
        render_onboarding_guide()
        return

    # Compute audit
    audit = audit_dataframe_quality(raw_df, target_col="label", context_name=source_info.get("source_name", "Active Capture"))
    q_score = audit["quality_score"]

    # Top KPI row with animated quality gauge
    col_gauge, col_stats = st.columns([1, 2])
    with col_gauge:
        gauge_fig = plot_quality_gauge(q_score, title="Data Quality Score")
        st.plotly_chart(gauge_fig, use_container_width=True)

    with col_stats:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(
                f"""
                <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 14px; margin-bottom: 12px;">
                    <div style="color: #8B9A91; font-size: 11px; text-transform: uppercase; font-weight: 600;">Missing Value Cells</div>
                    <div style="color: {'#16C784' if audit['total_missing_values'] == 0 else '#F59E0B'}; font-size: 22px; font-weight: 700; margin: 2px 0;">
                        {audit['total_missing_values']}
                    </div>
                    <div style="color: #8B9A91; font-size: 11px;">{len(audit['columns_with_missing'])} columns affected</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""
                <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 14px;">
                    <div style="color: #8B9A91; font-size: 11px; text-transform: uppercase; font-weight: 600;">Infinite Values (+inf / -inf)</div>
                    <div style="color: {'#16C784' if audit['total_infinite_values'] == 0 else '#EF4444'}; font-size: 22px; font-weight: 700; margin: 2px 0;">
                        {audit['total_infinite_values']}
                    </div>
                    <div style="color: #8B9A91; font-size: 11px;">Division by zero rate artifacts</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m2:
            st.markdown(
                f"""
                <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 14px; margin-bottom: 12px;">
                    <div style="color: #8B9A91; font-size: 11px; text-transform: uppercase; font-weight: 600;">Exact Duplicate Records</div>
                    <div style="color: {'#16C784' if audit['duplicate_rows'] == 0 else '#F59E0B'}; font-size: 22px; font-weight: 700; margin: 2px 0;">
                        {audit['duplicate_rows']} ({audit['duplicate_percentage']}%)
                    </div>
                    <div style="color: #8B9A91; font-size: 11px;">Pre-split leakage prevention target</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            anomalies = audit.get("numerical_anomalies", {})
            neg_count = len(anomalies.get("negative_value_violations", {}))
            st.markdown(
                f"""
                <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 14px;">
                    <div style="color: #8B9A91; font-size: 11px; text-transform: uppercase; font-weight: 600;">Numerical Inconsistencies</div>
                    <div style="color: {'#16C784' if neg_count == 0 else '#EF4444'}; font-size: 22px; font-weight: 700; margin: 2px 0;">
                        {neg_count}
                    </div>
                    <div style="color: #8B9A91; font-size: 11px;">Negative values in unsigned metrics</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Detailed Audit Tabs
    tab_summary, tab_reports, tab_cleaning = st.tabs([
        "Data Hygiene Audit Table",
        "Generated Audit Artifacts",
        "Data Cleaning Pipeline Runner",
    ])

    with tab_summary:
        st.subheader("Field-Level Quality Telemetry")
        summary_path = DATA_QUALITY_REPORTS_DIR / "data_quality_summary.csv"
        if summary_path.is_file():
            sum_df = pd.read_csv(summary_path)
            st.dataframe(sum_df, use_container_width=True, hide_index=True)
        else:
            col_audit_rows = []
            for col in raw_df.columns:
                n_miss = int(raw_df[col].isna().sum())
                n_inf = int(np.isinf(raw_df[col]).sum()) if pd.api.types.is_numeric_dtype(raw_df[col]) else 0
                col_audit_rows.append({
                    "Feature Name": col,
                    "Data Type": str(raw_df[col].dtype),
                    "Missing Values": n_miss,
                    "Infinite Values": n_inf,
                    "Status": "OK" if (n_miss == 0 and n_inf == 0) else "NEEDS SANITIZATION",
                })
            st.dataframe(pd.DataFrame(col_audit_rows), use_container_width=True, hide_index=True)

    with tab_reports:
        st.subheader("Physical Quality Audit Reports on Disk")
        reports = list(DATA_QUALITY_REPORTS_DIR.glob("*.*"))
        if reports:
            rep_df = pd.DataFrame([
                {"Report Artifact": r.name, "File Format": r.suffix.upper()[1:], "File Size": f"{r.stat().st_size:,} bytes", "Disk Path": str(r)}
                for r in reports
            ])
            st.dataframe(rep_df[["Report Artifact", "File Format", "File Size"]], use_container_width=True, hide_index=True)
        else:
            st.info("No report files found in `reports/data_quality/`.")

    with tab_cleaning:
        st.subheader("Execute In-Memory Data Cleaning Pipeline")
        st.markdown(
            "Execute the verified Phase 2 data cleaning pipeline: header normalization, redundant column pruning (`fwd_header_length_1`), "
            "infinity conversion to median, and exact duplicate elimination."
        )
        if st.button("Run Preprocessing Pipeline", key="run_cleaning_btn"):
            with st.spinner("Processing network flow data..."):
                from neuralshield.data.preprocessing import PreprocessingPipeline
                pipeline = PreprocessingPipeline()
                result = pipeline.fit_transform(raw_df, dataset_name="Interactive Run")
                cleaned_df = result["cleaned_df"]
                pipeline_audit = result["audit_report"]

                st.session_state["cleaned_df"] = cleaned_df
                st.session_state["quality_score"] = pipeline_audit["quality_audit"]["quality_score"]

                st.success(
                    f"Pipeline Completed! "
                    f"Initial shape: {result['initial_shape']} -> Cleaned shape: {result['final_shape']} "
                    f"| Quality Score: {st.session_state['quality_score']}/100"
                )
                st.dataframe(cleaned_df.head(50), use_container_width=True)
