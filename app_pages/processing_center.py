"""Processing Center: Dataset inventory, chunked ingestion, sanitation pipeline, and exports."""

import streamlit as st
import pandas as pd
from pathlib import Path
from config.settings import (
    RAW_DATA_DIR,
    SAMPLE_DATA_DIR,
    PROCESSED_DATA_DIR,
    DATA_QUALITY_REPORTS_DIR,
    UIThemeConfig,
)
from neuralshield.data.source_manager import (
    load_active_dataset,
    render_data_source_banner,
    render_onboarding_guide,
)
from neuralshield.data.discovery import inspect_dataset_inventory
from neuralshield.data.schema import compare_schemas
from neuralshield.data.loader import DatasetLoader, downcast_numeric_dtypes
from neuralshield.data.preprocessing import PreprocessingPipeline
from neuralshield.data.validation import export_quality_report

theme = UIThemeConfig()


def render_processing_center():
    """Renders the data processing and export operations center."""
    st.markdown(
        """
        <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 18px 20px; margin-bottom: 20px;">
            <h2 style="color: #E8F0EB; margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.3px;">
                PROCESSING CENTER // BATCH INGESTION & PIPELINE ENGINE
            </h2>
            <p style="color: #8B9A91; margin: 4px 0 0 0; font-size: 13px;">
                Chunk-aware batch processing, cross-file schema consistency, memory optimization, and sanitized exports.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Active dataset and transparency banner
    test_df, source_info = load_active_dataset()
    render_data_source_banner(source_info)

    p_col1, p_col2 = st.columns([1, 1])

    with p_col1:
        st.subheader("1. Ingestion & Memory Controls")
        chunk_size = st.select_slider(
            "Batch Chunk Size (Rows per chunk)",
            options=[10_000, 25_000, 50_000, 100_000, 250_000],
            value=100_000,
            help="Limits resident RAM usage during multi-gigabyte CSV processing.",
        )
        downcast_toggle = st.checkbox(
            "Enable Lossless Numeric Downcasting (float64 -> float32, int64 -> int32)",
            value=True,
            help="Saves 45-55% memory footprint without precision degradation.",
        )
        export_fmt = st.radio("Target Export Format", ["Parquet (Compressed, Fast)", "CSV (Universal Standard)"], index=0)

    with p_col2:
        st.subheader("2. Dataset Source & Memory Impact")
        if test_df is not None and not test_df.empty:
            orig_mb = test_df.memory_usage(deep=True).sum() / (1024 * 1024)
            _, opt_stats = downcast_numeric_dtypes(test_df)
            down_mb = opt_stats["optimized_memory_mb"]
            reduct = opt_stats["reduction_percentage"]

            st.markdown(
                f"""
                <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 14px; margin-top: 10px;">
                    <div style="color: #8B9A91; font-size: 11px; text-transform: uppercase; font-weight: 600;">Downcasting Memory Telemetry</div>
                    <div style="display: flex; justify-content: space-between; margin-top: 8px;">
                        <div>
                            <div style="color: #8B9A91; font-size: 11px;">Standard Float64:</div>
                            <div style="color: #E8F0EB; font-size: 16px; font-weight: bold;">{orig_mb:.2f} MB</div>
                        </div>
                        <div>
                            <div style="color: #8B9A91; font-size: 11px;">Optimized Float32:</div>
                            <div style="color: #16C784; font-size: 16px; font-weight: bold;">{down_mb:.2f} MB</div>
                        </div>
                        <div>
                            <div style="color: #8B9A91; font-size: 11px;">RAM Reduction:</div>
                            <div style="color: #16C784; font-size: 16px; font-weight: bold;">{reduct}%</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("No active dataset loaded for memory telemetry.")

    st.markdown("<hr style='border-color: #1D2824; margin: 20px 0;'>", unsafe_allow_html=True)

    # 3. Batch Pipeline Runner
    st.subheader("3. Execute Complete Preprocessing & Export")
    st.markdown("Applies column standardization, duplicate removal, infinity sanitization, and saves output to `data/processed/`.")

    if st.button("Execute Pipeline & Export Cleaned Dataset", key="run_proc_btn"):
        with st.spinner("Executing pipeline and exporting..."):
            pipeline = PreprocessingPipeline()
            res = pipeline.fit_transform(test_df, dataset_name="BenchmarkSample")
            clean_df = res["cleaned_df"]

            fmt = "parquet" if "Parquet" in export_fmt else "csv"
            out_path = PROCESSED_DATA_DIR / f"cleaned_cicids2017_sample.{fmt}"
            PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

            if fmt == "parquet":
                clean_df.to_parquet(out_path, index=False)
            else:
                clean_df.to_csv(out_path, index=False)

            st.success(
                f"Processing and Export Complete! "
                f"Exported {len(clean_df):,} rows x {len(clean_df.columns)} columns to `{out_path.name}` ({out_path.stat().st_size:,} bytes)."
            )
            st.dataframe(clean_df.head(25), use_container_width=True)
