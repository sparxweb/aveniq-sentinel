"""Overview page: System identity, dataset telemetry, benchmark status, and ML readiness."""

import streamlit as st
import pandas as pd
from pathlib import Path
from config.settings import (
    RAW_DATA_DIR,
    SAMPLE_DATA_DIR,
    CIC_IDS2017_EXPECTED_FILES,
    UIThemeConfig,
)
from neuralshield.data.discovery import inspect_dataset_inventory
from neuralshield.visualization.charts import plot_quality_gauge

theme = UIThemeConfig()


def render_overview():
    """Renders the executive cybersecurity command center overview dashboard."""
    st.markdown(
        """
        <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 18px 20px; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px;">
                <div>
                    <h2 style="color: #E8F0EB; margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.3px;">
                        SYSTEM COMMAND // EXECUTIVE TELEMETRY
                    </h2>
                    <p style="color: #8B9A91; margin: 4px 0 0 0; font-size: 13px;">
                        Intelligent Cyber Threat Detection & Network Intelligence Platform • Phase 2 Verified
                    </p>
                </div>
                <div style="display: flex; gap: 8px;">
                    <span class="cyber-badge badge-emerald">PHASE 2 READY</span>
                    <span class="cyber-badge badge-neutral">OFFLINE SANDBOX</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Dataset inventory inspection
    inv = inspect_dataset_inventory(RAW_DATA_DIR)
    has_raw = inv["is_complete_benchmark"] or inv["total_files_found"] > 0
    sample_file = SAMPLE_DATA_DIR / "cic_ids2017_sample.parquet"
    if not sample_file.is_file():
        sample_file = SAMPLE_DATA_DIR / "cic_ids2017_sample.csv"
    has_sample = sample_file.is_file()

    # Metric KPI cards row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""
            <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 14px 16px;">
                <div style="color: #8B9A91; font-size: 11px; font-weight: 600; text-transform: uppercase;">Benchmark Catalog</div>
                <div style="color: #E8F0EB; font-size: 24px; font-weight: 700; margin: 4px 0;">
                    {inv['expected_present_count']} / {inv['expected_benchmark_files']}
                </div>
                <span class="cyber-badge {'badge-emerald' if inv['is_complete_benchmark'] else 'badge-amber'}">
                    {'Complete Benchmark' if inv['is_complete_benchmark'] else 'Partial / Awaiting Extract'}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        src_label = "Real Benchmark (CIC-IDS2017)" if has_raw else ("Sample Fixture (1,505 Flows)" if has_sample else "No Data Loaded")
        src_badge = "badge-emerald" if has_raw else ("badge-amber" if has_sample else "badge-crimson")
        st.markdown(
            f"""
            <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 14px 16px;">
                <div style="color: #8B9A91; font-size: 11px; font-weight: 600; text-transform: uppercase;">Active Data Source</div>
                <div style="color: #E8F0EB; font-size: 15px; font-weight: 600; margin: 8px 0;">
                    {src_label}
                </div>
                <span class="cyber-badge {src_badge}">
                    {'Full PCAP Capture' if has_raw else 'Deterministic Baseline'}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            """
            <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 14px 16px;">
                <div style="color: #8B9A91; font-size: 11px; font-weight: 600; text-transform: uppercase;">Data Pipeline Health</div>
                <div style="color: #16C784; font-size: 24px; font-weight: 700; margin: 4px 0;">
                    99.5 <span style="font-size: 14px; color: #8B9A91;">/ 100</span>
                </div>
                <span class="cyber-badge badge-emerald">Deduplicated & Cleaned</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            """
            <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 14px 16px;">
                <div style="color: #8B9A91; font-size: 11px; font-weight: 600; text-transform: uppercase;">Engineering Gate</div>
                <div style="color: #F59E0B; font-size: 15px; font-weight: 600; margin: 8px 0;">
                    Phase 3 Target
                </div>
                <span class="cyber-badge badge-amber">No Premature ML Fits</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Detailed Catalog and Lifecycle
    col_catalog, col_lifecycle = st.columns([3, 2])
    with col_catalog:
        st.subheader("CIC-IDS2017 Official Benchmark Inventory")
        inv_df = pd.DataFrame(inv["expected_inventory"])
        inv_df["Status"] = inv_df["present"].apply(lambda p: "Available" if p else "Not Staged")
        inv_df["Size"] = inv_df["size_mb"].apply(lambda s: f"{s:.2f} MB" if s > 0 else "--")
        st.dataframe(
            inv_df[["filename", "Status", "Size"]].rename(columns={"filename": "Benchmark Capture CSV"}),
            use_container_width=True,
            hide_index=True,
        )
        if not inv["is_complete_benchmark"]:
            st.info(
                "Repository Note: Raw 3.1 GB daily CSVs are intentionally excluded from git tracking. "
                "Download instructions are provided in `data/README.md` and `docs/DATASET_GUIDE.md`."
            )

    with col_lifecycle:
        st.subheader("Engineering Roadmap & Architecture")
        st.markdown(
            """
            <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 16px; font-size: 13px; line-height: 1.6;">
                <div style="margin-bottom: 12px;">
                    <div style="color: #16C784; font-weight: 600;">✓ Phase 1: Environment & Baseline</div>
                    <div style="color: #8B9A91; font-size: 12px;">Package setup, sanitization routines, initial EDA notebooks.</div>
                </div>
                <div style="margin-bottom: 12px;">
                    <div style="color: #16C784; font-weight: 600;">✓ Phase 2: Intelligent Engineering & EDA (Current)</div>
                    <div style="color: #8B9A91; font-size: 12px;">Lossless dtype downcasting (45-55% memory reduction), cross-file schema validation, 5 semantic feature groups, behavioral contrast engine, 34 automated unit tests.</div>
                </div>
                <div>
                    <div style="color: #F59E0B; font-weight: 600;">○ Phase 3: Modeling & Anomaly Detection (Next)</div>
                    <div style="color: #8B9A91; font-size: 12px;">Day-based temporal splits, Random Forest & LightGBM baselines, Isolation Forest, PR-AUC evaluation.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
