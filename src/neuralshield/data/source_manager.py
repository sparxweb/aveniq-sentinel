"""Unified data source detection, validation and transparency management."""

from pathlib import Path
from typing import Dict, Any, Optional, Union
import pandas as pd
import streamlit as st

from config.settings import RAW_DATA_DIR, SAMPLE_DATA_DIR
from config.logging_config import get_logger

logger = get_logger("data.source_manager")

# Source Category Identifiers
SOURCE_OFFICIAL = "Official Dataset"
SOURCE_USER = "User Dataset"
SOURCE_DEMO = "Demonstration Data"
SOURCE_NONE = "No Dataset Loaded"


def detect_data_source(
    df: Optional[pd.DataFrame] = None,
    source_name: Optional[str] = None,
    source_path: Optional[Union[str, Path]] = None,
    source_type_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Detects and returns standardized metadata describing the active dataset source.
    Ensures the application never presents synthetic sample values as actual production telemetry.
    """
    if source_type_override:
        s_type = source_type_override
    elif source_path:
        p = Path(source_path)
        if RAW_DATA_DIR in p.parents or p.parent == RAW_DATA_DIR:
            s_type = SOURCE_OFFICIAL
        elif SAMPLE_DATA_DIR in p.parents or p.parent == SAMPLE_DATA_DIR or "sample" in p.name.lower():
            s_type = SOURCE_DEMO
        else:
            s_type = SOURCE_USER
    elif source_name:
        s_lower = source_name.lower()
        if "official" in s_lower or "cic-ids2017 raw" in s_lower or "machinelearningcsv" in s_lower:
            s_type = SOURCE_OFFICIAL
        elif "sample" in s_lower or "synthetic" in s_lower or "demonstration" in s_lower:
            s_type = SOURCE_DEMO
        elif "upload" in s_lower or "custom" in s_lower or "user" in s_lower:
            s_type = SOURCE_USER
        else:
            s_type = SOURCE_USER
    elif df is not None and not df.empty:
        # Check if df matches default synthetic sample size
        if len(df) == 1505 or len(df) <= 2000:
            s_type = SOURCE_DEMO
        else:
            s_type = SOURCE_USER
    else:
        s_type = SOURCE_NONE

    row_count = len(df) if df is not None else 0
    col_count = len(df.columns) if df is not None else 0

    if s_type == SOURCE_OFFICIAL:
        label = "Official CIC-IDS2017 Dataset"
        badge_class = "badge-emerald"
        is_real = True
        desc = "Official PCAP network flow capture from the UNB CIC-IDS2017 benchmark suite."
        disclaimer = None
    elif s_type == SOURCE_USER:
        label = source_name or "Custom User Network Capture"
        badge_class = "badge-cyan"
        is_real = True
        desc = "User-supplied network flow capture uploaded or provided during this session."
        disclaimer = "Analyzing user-provided network telemetry. Ensure headers conform to CIC-IDS flow standard."
    elif s_type == SOURCE_DEMO:
        label = "Synthetic Demonstration Fixture"
        badge_class = "badge-amber"
        is_real = False
        desc = f"Deterministic demonstration fixture ({row_count:,} flows) for algorithm validation."
        disclaimer = (
            "⚠️ DEMONSTRATION DATA: Displaying synthetic baseline fixtures (1,505 flows). "
            "Values represent demonstration samples, not active production network telemetry."
        )
    else:
        label = "No Dataset Available"
        badge_class = "badge-neutral"
        is_real = False
        desc = "No network flow capture is currently loaded in memory or discovered in repository."
        disclaimer = "No active data source. Please provide a network flow capture to enable operational centers."

    return {
        "source_type": s_type,
        "source_name": label,
        "badge_class": badge_class,
        "is_real_telemetry": is_real,
        "flow_count": row_count,
        "feature_count": col_count,
        "description": desc,
        "disclaimer": disclaimer,
    }


def render_data_source_banner(source_info: Dict[str, Any]) -> None:
    """Renders a transparent, standardized visual banner indicating active data source."""
    s_type = source_info.get("source_type", SOURCE_NONE)
    s_name = source_info.get("source_name", "Unknown Source")
    badge_cls = source_info.get("badge_class", "badge-neutral")
    flows = source_info.get("flow_count", 0)
    features = source_info.get("feature_count", 0)
    disclaimer = source_info.get("disclaimer")

    border_color = (
        "rgba(16, 185, 129, 0.4)" if s_type == SOURCE_OFFICIAL
        else ("rgba(245, 158, 11, 0.4)" if s_type == SOURCE_DEMO
              else ("rgba(6, 182, 212, 0.4)" if s_type == SOURCE_USER
                    else "rgba(239, 68, 68, 0.4)"))
    )

    bg_color = (
        "rgba(16, 185, 129, 0.05)" if s_type == SOURCE_OFFICIAL
        else ("rgba(245, 158, 11, 0.05)" if s_type == SOURCE_DEMO
              else ("rgba(6, 182, 212, 0.05)" if s_type == SOURCE_USER
                    else "rgba(239, 68, 68, 0.05)"))
    )

    badge_label = s_type.upper()

    html = f"""
    <div style="background-color: {bg_color}; border: 1px solid {border_color}; border-radius: 6px; padding: 10px 14px; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px;">
        <div style="display: flex; align-items: center; gap: 10px;">
            <span class="cyber-badge {badge_cls}">● {badge_label}</span>
            <span style="color: #E8F0EB; font-weight: 600; font-size: 13px;">{s_name}</span>
            <span style="color: #8B9A91; font-size: 12px;">({flows:,} flows • {features} features)</span>
        </div>
        <div style="font-size: 11px; color: #8B9A91;">
            {'Verified Production Capture' if source_info.get('is_real_telemetry') else 'Deterministic Sandbox Fixture'}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    if disclaimer and s_type == SOURCE_DEMO:
        st.markdown(
            f"""
            <div style="background-color: rgba(245, 158, 11, 0.08); border-left: 3px solid #F59E0B; padding: 8px 12px; margin-bottom: 16px; font-size: 12px; color: #F59E0B;">
                {disclaimer}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_onboarding_guide() -> None:
    """Renders onboarding instructions when no dataset is present."""
    st.markdown(
        """
        <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 24px; margin: 20px 0;">
            <h3 style="color: #10B981; margin-top: 0;">Dataset Onboarding & Ingestion Guide</h3>
            <p style="color: #8B9A91; font-size: 13px;">
                Aveniq Sentinel operates strictly offline with zero external network dependencies.
                To analyze real network flow records, you can supply data through either of these methods:
            </p>
            <ol style="color: #E8F0EB; font-size: 13px; line-height: 1.8;">
                <li><b>Official Benchmark Captures:</b> Place official CIC-IDS2017 <code>.csv</code> files into <code>data/raw/</code>.</li>
                <li><b>Custom Network Telemetry:</b> Use the <b>Flow Data Explorer</b> to upload any network flow CSV.</li>
                <li><b>Demonstration Fixture:</b> Run <code>python data/sample/generate_sample.py</code> to create a deterministic local fixture.</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_active_dataset() -> tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """Loads active dataset from session state or falls back to sample fixture with clear metadata."""
    if "active_df" in st.session_state and st.session_state["active_df"] is not None:
        source_info = st.session_state.get(
            "data_source_info",
            detect_data_source(st.session_state["active_df"])
        )
        return st.session_state["active_df"], source_info

    # Attempt to load from sample fixture
    sample_parquet = SAMPLE_DATA_DIR / "cic_ids2017_sample.parquet"
    sample_csv = SAMPLE_DATA_DIR / "cic_ids2017_sample.csv"

    if sample_parquet.is_file():
        df = pd.read_parquet(sample_parquet)
        source_info = detect_data_source(df, source_path=sample_parquet)
    elif sample_csv.is_file():
        df = pd.read_csv(sample_csv)
        source_info = detect_data_source(df, source_path=sample_csv)
    else:
        df = None
        source_info = detect_data_source(None)

    if df is not None:
        st.session_state["active_df"] = df
        st.session_state["data_source_info"] = source_info

    return df, source_info
