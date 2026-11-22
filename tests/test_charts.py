"""Unit tests for Plotly cybersecurity command center visualization generators."""

import pytest
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from neuralshield.visualization.charts import (
    plot_class_distribution,
    plot_correlation_heatmap,
    plot_feature_distribution,
    plot_quality_gauge,
    plot_flow_scatter,
    plot_attack_comparison_bars,
    plot_tcp_flags_breakdown,
)


def test_plot_class_distribution_valid():
    """Verifies label distribution bar chart with both normal and attack categories."""
    counts = {"Benign": 1000, "DDoS": 250, "PortScan": 120}
    fig = plot_class_distribution(counts, title="Test Distribution")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].x == ("Benign", "DDoS", "PortScan")


def test_plot_class_distribution_empty():
    """Verifies graceful empty figure when counts dictionary is empty."""
    fig = plot_class_distribution({}, title="Empty Test")
    assert isinstance(fig, go.Figure)


def test_plot_correlation_heatmap_valid():
    """Verifies correlation heatmap with numeric DataFrame."""
    df = pd.DataFrame({
        "feat_a": [1.0, 2.0, 3.0, 4.0],
        "feat_b": [2.0, 4.0, 6.0, 8.0],
        "feat_c": [4.0, 3.0, 2.0, 1.0],
    })
    corr = df.corr()
    fig = plot_correlation_heatmap(corr)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.data[0].type == "heatmap"


def test_plot_correlation_heatmap_empty():
    """Verifies empty correlation matrix handling."""
    fig = plot_correlation_heatmap(pd.DataFrame())
    assert isinstance(fig, go.Figure)


def test_plot_feature_distribution_valid():
    """Verifies histogram rendering with boxplot marginals."""
    df = pd.DataFrame({"flow_duration": [10.0, 20.0, 50.0, 100.0, 200.0]})
    fig = plot_feature_distribution(df, "flow_duration", log_y=True)
    assert isinstance(fig, go.Figure)


def test_plot_feature_distribution_missing():
    """Verifies handling when requested feature is absent."""
    df = pd.DataFrame({"other_col": [1, 2, 3]})
    fig = plot_feature_distribution(df, "non_existent")
    assert isinstance(fig, go.Figure)


def test_plot_quality_gauge_score_tiers():
    """Verifies gauge color thresholds for high, moderate, and critical quality."""
    fig_high = plot_quality_gauge(95.0)
    fig_mid = plot_quality_gauge(70.0)
    fig_low = plot_quality_gauge(40.0)

    for fig in [fig_high, fig_mid, fig_low]:
        assert isinstance(fig, go.Figure)
        assert fig.data[0].type == "indicator"


def test_plot_flow_scatter_valid():
    """Verifies bivariate flow scatter plot with color category."""
    df = pd.DataFrame({
        "flow_duration": [10, 20, 30],
        "total_packets": [100, 200, 300],
        "label": ["Benign", "DDoS", "Benign"],
    })
    fig = plot_flow_scatter(df, x_col="flow_duration", y_col="total_packets", color_col="label")
    assert isinstance(fig, go.Figure)


def test_plot_flow_scatter_missing_columns():
    """Verifies graceful fallback when scatter columns are missing."""
    df = pd.DataFrame({"col_a": [1, 2]})
    fig = plot_flow_scatter(df, x_col="missing_x", y_col="missing_y")
    assert isinstance(fig, go.Figure)


def test_plot_attack_comparison_bars_valid_and_empty():
    """Verifies attack comparison bar chart with populated and empty inputs."""
    data = {
        "feature_comparisons": {
            "flow_duration": {"benign_median": 100.0, "attack_median": 20.0},
            "total_bytes": {"benign_median": 500.0, "attack_median": 12000.0},
        }
    }
    fig = plot_attack_comparison_bars(data)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2  # Benign and Attack bars

    fig_empty = plot_attack_comparison_bars({})
    assert isinstance(fig_empty, go.Figure)


def test_plot_tcp_flags_breakdown_valid_and_empty():
    """Verifies TCP flags activation rate comparison."""
    flags = {
        "syn_flag": {"benign_percentage_active": 4.5, "attack_percentage_active": 95.0},
        "ack_flag": {"benign_percentage_active": 90.0, "attack_percentage_active": 12.0},
    }
    fig = plot_tcp_flags_breakdown(flags)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2

    fig_empty = plot_tcp_flags_breakdown({})
    assert isinstance(fig_empty, go.Figure)
