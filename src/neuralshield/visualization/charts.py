"""Interactive Plotly charts styled with the NeuralShield Cybersecurity Command Center palette."""

from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from config.settings import UIThemeConfig

theme = UIThemeConfig()


def get_dark_layout(title: str = "") -> Dict[str, Any]:
    """Generates a standardized dark-themed Plotly layout specification."""
    return dict(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(color=theme.text_primary, size=15, family="Segoe UI, Inter, sans-serif"),
            x=0.02,
        ),
        paper_bgcolor=theme.card_bg,
        plot_bgcolor=theme.bg_secondary,
        font=dict(color=theme.text_secondary, size=12, family="Segoe UI, Inter, sans-serif"),
        margin=dict(l=40, r=30, t=50, b=40),
        xaxis=dict(
            gridcolor=theme.border_color,
            linecolor=theme.border_color,
            tickfont=dict(color=theme.text_secondary),
            title=dict(font=dict(color=theme.text_primary)),
        ),
        yaxis=dict(
            gridcolor=theme.border_color,
            linecolor=theme.border_color,
            tickfont=dict(color=theme.text_secondary),
            title=dict(font=dict(color=theme.text_primary)),
        ),
        legend=dict(
            font=dict(color=theme.text_primary),
            bgcolor="rgba(0,0,0,0)",
        ),
    )


def plot_class_distribution(
    counts: Dict[str, int],
    title: str = "Network Traffic Label Distribution",
) -> go.Figure:
    """Renders a styled bar chart of label counts with Benign in emerald and attacks in crimson."""
    if not counts:
        fig = go.Figure()
        fig.update_layout(get_dark_layout("No Data Available"))
        return fig
        
    categories = list(counts.keys())
    values = list(counts.values())
    
    # Colors: Green for Benign, Crimson for attacks
    colors = [
        theme.accent_primary if "benign" in str(cat).lower() else theme.accent_danger
        for cat in categories
    ]
    
    fig = go.Figure(
        data=[
            go.Bar(
                x=categories,
                y=values,
                marker=dict(color=colors, line=dict(color=theme.border_color, width=1)),
                text=[f"{v:,}" for v in values],
                textposition="auto",
            )
        ]
    )
    
    layout = get_dark_layout(title)
    layout["xaxis"]["tickangle"] = -30
    layout["yaxis"]["title"] = dict(text="Record Count", font=dict(color=theme.text_primary))
    fig.update_layout(layout)
    return fig


def plot_correlation_heatmap(
    corr_matrix: pd.DataFrame,
    title: str = "Feature Correlation Matrix",
) -> go.Figure:
    """Renders an interactive correlation heatmap with emerald/neutral/crimson diverging colors."""
    if corr_matrix.empty:
        fig = go.Figure()
        fig.update_layout(get_dark_layout("No Correlation Data"))
        return fig
        
    custom_colorscale = [
        [0.0, theme.accent_danger],
        [0.5, theme.bg_secondary],
        [1.0, theme.accent_primary],
    ]
    
    fig = go.Figure(
        data=go.Heatmap(
            z=corr_matrix.values,
            x=corr_matrix.columns,
            y=corr_matrix.index,
            colorscale=custom_colorscale,
            zmin=-1.0,
            zmax=1.0,
            colorbar=dict(
                title=dict(text="Corr", font=dict(color=theme.text_primary)),
                tickfont=dict(color=theme.text_secondary),
            ),
        )
    )
    
    layout = get_dark_layout(title)
    layout["xaxis"]["tickangle"] = -45
    fig.update_layout(layout)
    return fig


def plot_feature_distribution(
    df: pd.DataFrame,
    feature: str,
    title: Optional[str] = None,
    log_y: bool = False,
) -> go.Figure:
    """Plots histogram with marginal boxplot for a specific numeric feature."""
    if feature not in df.columns:
        fig = go.Figure()
        fig.update_layout(get_dark_layout("Feature Not Found"))
        return fig
        
    chart_title = title or f"Distribution: {feature}"
    
    fig = px.histogram(
        df,
        x=feature,
        marginal="box",
        log_y=log_y,
        color_discrete_sequence=[theme.accent_primary],
        opacity=0.85,
    )
    
    layout = get_dark_layout(chart_title)
    fig.update_layout(layout)
    fig.update_traces(marker_line_color=theme.border_color, marker_line_width=1)
    return fig


def plot_quality_gauge(score: float, title: str = "Data Quality Index") -> go.Figure:
    """Plots an interactive circular gauge for overall dataset health."""
    color = theme.accent_primary if score >= 80 else (theme.accent_warning if score >= 60 else theme.accent_danger)
    
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": f"<b>{title}</b>", "font": {"color": theme.text_primary, "size": 16}},
            number={"suffix": "/100", "font": {"color": color, "size": 28}},
            gauge={
                "axis": {"range": [0, 100], "tickcolor": theme.text_secondary},
                "bar": {"color": color},
                "bgcolor": theme.bg_secondary,
                "borderwidth": 1,
                "bordercolor": theme.border_color,
                "steps": [
                    {"range": [0, 60], "color": "rgba(239, 68, 68, 0.2)"},
                    {"range": [60, 80], "color": "rgba(245, 158, 11, 0.2)"},
                    {"range": [80, 100], "color": "rgba(22, 199, 132, 0.2)"},
                ],
            },
        )
    )
    
    layout = get_dark_layout("")
    layout["margin"] = dict(l=30, r=30, t=40, b=20)
    fig.update_layout(layout)
    return fig


def plot_flow_scatter(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: Optional[str] = None,
    title: str = "Network Flow Bivariate Telemetry",
) -> go.Figure:
    """Generates an interactive scatter plot of two flow metrics with logarithmic scales."""
    if x_col not in df.columns or y_col not in df.columns:
        fig = go.Figure()
        fig.update_layout(get_dark_layout("Columns Not Available"))
        return fig
        
    color_discrete_map = {
        "Benign": theme.accent_primary,
        "BENIGN": theme.accent_primary,
        "Low": theme.accent_primary,
        "Moderate": theme.accent_warning,
        "High": "#F97316",
        "Critical": theme.accent_danger,
    }
    
    fig = px.scatter(
        df.head(2000),  # Limit scatter points for crisp responsive rendering
        x=x_col,
        y=y_col,
        color=color_col if color_col in df.columns else None,
        color_discrete_map=color_discrete_map,
        opacity=0.75,
        hover_data=[c for c in ["label", "risk_level", "risk_score"] if c in df.columns],
    )
    
    layout = get_dark_layout(title)
    fig.update_layout(layout)
    return fig


def plot_attack_comparison_bars(
    comparison_dict: Dict[str, Any],
    title: str = "Benign vs Attack Feature Medians",
) -> go.Figure:
    """Renders a grouped comparison bar chart contrasting benign vs attack feature medians."""
    feat_comps = comparison_dict.get("feature_comparisons", {})
    if not feat_comps:
        fig = go.Figure()
        fig.update_layout(get_dark_layout("No Comparison Data"))
        return fig

    metrics = list(feat_comps.keys())
    benign_vals = [feat_comps[m]["benign_median"] for m in metrics]
    attack_vals = [feat_comps[m]["attack_median"] for m in metrics]

    fig = go.Figure(
        data=[
            go.Bar(
                name="Benign (Median)",
                x=metrics,
                y=benign_vals,
                marker=dict(color=theme.accent_primary),
            ),
            go.Bar(
                name="Attack (Median)",
                x=metrics,
                y=attack_vals,
                marker=dict(color=theme.accent_danger),
            ),
        ]
    )

    layout = get_dark_layout(title)
    layout["barmode"] = "group"
    layout["xaxis"]["tickangle"] = -30
    layout["yaxis"]["type"] = "log"
    layout["yaxis"]["title"] = dict(text="Median Value (Log Scale)", font=dict(color=theme.text_primary))
    fig.update_layout(layout)
    return fig


def plot_tcp_flags_breakdown(
    flag_comparisons: Dict[str, Dict[str, float]],
    title: str = "TCP Flag Activity Rate: Benign vs Attack (%)",
) -> go.Figure:
    """Renders a grouped bar chart comparing TCP flag activation rates."""
    if not flag_comparisons:
        fig = go.Figure()
        fig.update_layout(get_dark_layout("No Flag Data"))
        return fig

    flags = list(flag_comparisons.keys())
    b_rates = [flag_comparisons[f]["benign_percentage_active"] for f in flags]
    a_rates = [flag_comparisons[f]["attack_percentage_active"] for f in flags]

    clean_names = [f.replace("_", " ").title() for f in flags]

    fig = go.Figure(
        data=[
            go.Bar(name="Benign", x=clean_names, y=b_rates, marker=dict(color=theme.accent_primary)),
            go.Bar(name="Attack", x=clean_names, y=a_rates, marker=dict(color=theme.accent_danger)),
        ]
    )

    layout = get_dark_layout(title)
    layout["barmode"] = "group"
    layout["yaxis"]["title"] = dict(text="% Flows with Flag Active", font=dict(color=theme.text_primary))
    fig.update_layout(layout)
    return fig
