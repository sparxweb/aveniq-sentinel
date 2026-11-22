"""Unit tests for Streamlit application entrypoints, routers, and page renderers."""

import pytest
import importlib


def test_app_entrypoint_structure():
    """Verifies that app.py defines main and can be imported safely."""
    import app
    assert hasattr(app, "main")
    assert callable(app.main)
    assert hasattr(app, "initialize_session_state")
    assert hasattr(app, "apply_cyber_theme")


def test_package_dashboard_entrypoint():
    """Verifies that src/neuralshield/dashboard.py delegates to app.py."""
    from neuralshield import dashboard
    assert hasattr(dashboard, "main")
    assert callable(dashboard.main)


def test_streamlit_app_alias():
    """Verifies that streamlit_app.py exists and delegates to app.py."""
    import streamlit_app
    assert hasattr(streamlit_app, "main")
    assert callable(streamlit_app.main)


def test_all_operational_page_renderers():
    """Verifies all 5 page modules can be imported and their render functions are callable."""
    from app_pages.overview import render_overview
    from app_pages.data_explorer import render_data_explorer
    from app_pages.data_quality import render_data_quality
    from app_pages.eda_center import render_eda_center
    from app_pages.processing_center import render_processing_center

    assert callable(render_overview)
    assert callable(render_data_explorer)
    assert callable(render_data_quality)
    assert callable(render_eda_center)
    assert callable(render_processing_center)
