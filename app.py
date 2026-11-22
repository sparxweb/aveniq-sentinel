r"""Aveniq Sentinel — Intelligent Cyber Threat Detection & Network Intelligence Platform.
Aveniq Startup Cybersecurity Command Center UI.

Launch via:
    python -m streamlit run app.py
or:
    .\.venv\Scripts\python.exe -m streamlit run app.py
"""

import sys
from pathlib import Path

# Ensure project root and src/ are in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from config.settings import UIThemeConfig
from app_pages.overview import render_overview
from app_pages.data_explorer import render_data_explorer
from app_pages.data_quality import render_data_quality
from app_pages.eda_center import render_eda_center
from app_pages.processing_center import render_processing_center

theme = UIThemeConfig()


def initialize_session_state() -> None:
    """Initializes shared application session state safely."""
    defaults = {
        "loaded_df": None,
        "cleaned_df": None,
        "audit_report": None,
        "current_dataset_name": "CIC-IDS2017 Sample Fixture",
        "quality_score": 99.5,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def apply_cyber_theme() -> None:
    """Applies the professional Cybersecurity Command Center dark theme."""
    st.markdown(
        f"""
        <style>
            /* Base application background and typography */
            .stApp {{
                background-color: {theme.bg_primary};
                color: {theme.text_primary};
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Roboto, sans-serif;
            }}
            
            /* Sidebar container */
            section[data-testid="stSidebar"] {{
                background-color: {theme.bg_secondary};
                border-right: 1px solid {theme.border_color};
            }}
            
            /* Clean section headings */
            h1, h2, h3, h4, h5, h6 {{
                color: {theme.text_primary};
                font-weight: 600;
                letter-spacing: -0.2px;
            }}
            
            /* Professional dataframes */
            div[data-testid="stDataFrame"] {{
                border: 1px solid {theme.border_color};
                border-radius: 6px;
                background-color: {theme.card_bg};
            }}
            
            /* Streamlit action buttons */
            div.stButton > button:first-child {{
                background-color: {theme.accent_primary};
                color: #080B0A;
                font-weight: 600;
                font-size: 13px;
                border: 1px solid {theme.accent_primary};
                border-radius: 4px;
                padding: 6px 16px;
                transition: all 0.15s ease-in-out;
            }}
            div.stButton > button:first-child:hover {{
                background-color: #059669;
                color: #FFFFFF;
                border-color: #059669;
            }}
            
            /* Metric cards and KPI containers */
            div[data-testid="metric-container"] {{
                background-color: {theme.card_bg};
                border: 1px solid {theme.border_color};
                border-radius: 6px;
                padding: 12px 14px;
            }}
            
            /* Tabs styling */
            button[data-baseweb="tab"] {{
                color: {theme.text_secondary} !important;
                font-weight: 500 !important;
                font-size: 13px !important;
            }}
            button[data-baseweb="tab"][aria-selected="true"] {{
                color: {theme.accent_primary} !important;
                border-bottom-color: {theme.accent_primary} !important;
            }}
            
            /* Custom status badges */
            .cyber-badge {{
                display: inline-block;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.3px;
            }}
            .badge-emerald {{
                background-color: rgba(16, 185, 129, 0.12);
                color: #10B981;
                border: 1px solid rgba(16, 185, 129, 0.3);
            }}
            .badge-amber {{
                background-color: rgba(245, 158, 11, 0.12);
                color: #F59E0B;
                border: 1px solid rgba(245, 158, 11, 0.3);
            }}
            .badge-crimson {{
                background-color: rgba(239, 68, 68, 0.12);
                color: #EF4444;
                border: 1px solid rgba(239, 68, 68, 0.3);
            }}
            .badge-neutral {{
                background-color: rgba(139, 154, 145, 0.12);
                color: #8B9A91;
                border: 1px solid rgba(139, 154, 145, 0.25);
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_header() -> None:
    """Renders the top branding card in the sidebar."""
    st.sidebar.markdown(
        """
        <div style="padding: 12px 0 16px 0; border-bottom: 1px solid #1D2824; margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 26px;">🛡️</span>
                <div>
                    <h2 style="color: #16C784; font-size: 19px; margin: 0; font-weight: 700; letter-spacing: 0.4px;">
                        AVENIQ SENTINEL
                    </h2>
                    <p style="color: #8B9A91; font-size: 11px; margin: 2px 0 0 0; text-transform: uppercase; letter-spacing: 0.8px;">
                        Aveniq Cyber Intelligence
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_footer() -> None:
    """Renders the system telemetry footer in the sidebar."""
    st.sidebar.markdown("<br><hr style='border-color: #1D2824; margin: 12px 0;'>", unsafe_allow_html=True)
    st.sidebar.markdown(
        """
        <div style="color: #8B9A91; font-size: 11px; line-height: 1.6;">
            <div><b style="color: #E8F0EB;">Product:</b> Aveniq Sentinel v0.2.0</div>
            <div><b style="color: #E8F0EB;">Startup:</b> Aveniq (sparxweb)</div>
            <div><b style="color: #E8F0EB;">Benchmark:</b> CIC-IDS2017</div>
            <div><b style="color: #E8F0EB;">Engine:</b> Python 3.11 / Streamlit 1.67</div>
            <div style="margin-top: 8px;">
                <span class="cyber-badge badge-emerald">● SYSTEM OPERATIONAL</span>
            </div>
            <div style="margin-top: 6px; font-size: 10px; color: #6B7280;">
                Offline Sandbox • Zero Data Leakage
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Main application routine."""
    # 1. Page Configuration (must be the first Streamlit call)
    st.set_page_config(
        page_title="Aveniq Sentinel // Command Center",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 2. State & Styling Initialization
    initialize_session_state()
    apply_cyber_theme()
    render_sidebar_header()

    # 3. Primary Command Center Navigation
    navigation_map = {
        "Overview & Architecture": render_overview,
        "Flow Data Explorer": render_data_explorer,
        "Data Quality & Audit": render_data_quality,
        "Advanced EDA": render_eda_center,
        "Ingestion & Processing Center": render_processing_center,
    }

    st.sidebar.markdown(
        "<div style='font-size: 11px; color: #8B9A91; font-weight: 600; text-transform: uppercase; margin-bottom: 6px;'>Operational Centers</div>",
        unsafe_allow_html=True,
    )

    selected_center = st.sidebar.radio(
        label="Operational Centers",
        options=list(navigation_map.keys()),
        index=0,
        label_visibility="collapsed",
    )

    render_sidebar_footer()

    # 4. Defensive Page Rendering
    page_renderer = navigation_map.get(selected_center)
    if page_renderer:
        try:
            page_renderer()
        except Exception as e:
            st.error(f"Operational center encountered an issue: {e}")
            st.info("Check data availability in `data/sample/` or review logs for details.")


if __name__ == "__main__":
    main()
