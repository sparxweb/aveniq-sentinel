"""EDA Center: Advanced Exploratory Data Analysis, attack behavior comparisons, and distributions."""

import streamlit as st
import pandas as pd
from pathlib import Path
from config.settings import SAMPLE_DATA_DIR, RAW_DATA_DIR, UIThemeConfig
from neuralshield.analysis.comparisons import compare_benign_vs_attack
from neuralshield.analysis.correlations import compute_correlation_matrix, find_high_correlation_pairs
from neuralshield.analysis.distributions import analyze_class_balance
from neuralshield.visualization.charts import (
    plot_class_distribution,
    plot_correlation_heatmap,
    plot_attack_comparison_bars,
    plot_tcp_flags_breakdown,
    plot_feature_distribution,
)

theme = UIThemeConfig()


def render_eda_center():
    """Renders the Advanced Exploratory Data Analysis center."""
    st.markdown(
        """
        <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 18px 20px; margin-bottom: 20px;">
            <h2 style="color: #E8F0EB; margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.3px;">
                EXPLORATORY DATA ANALYSIS // STATISTICAL TELEMETRY
            </h2>
            <p style="color: #8B9A91; margin: 4px 0 0 0; font-size: 13px;">
                Behavioral contrast between benign and attack traffic, packet asymmetry, feature distributions, and collinearity.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Load dataset
    sample_path = SAMPLE_DATA_DIR / "cic_ids2017_sample.parquet"
    if not sample_path.is_file():
        sample_path = SAMPLE_DATA_DIR / "cic_ids2017_sample.csv"

    if not sample_path.is_file():
        st.warning("No sample dataset available in `data/sample/`.")
        return

    df = pd.read_parquet(sample_path) if sample_path.suffix == ".parquet" else pd.read_csv(sample_path)
    label_col = next((c for c in df.columns if c.strip().lower() == "label"), None)

    # 4 Comprehensive Analytical Tabs
    tab_balance, tab_behavior, tab_distributions, tab_correlation = st.tabs([
        "Class Balance & Threat Distribution",
        "Benign vs Attack Behavioral Contrast",
        "Feature Distributions & Skewness",
        "Multicollinearity & Correlations",
    ])

    with tab_balance:
        st.subheader("1. Label Distribution & Extreme Class Imbalance")
        st.markdown(
            "In real-world networks and the CIC-IDS2017 benchmark, normal background traffic vastly outnumbers malicious flows. "
            "Predicting the majority class yields deceptively high accuracy (~80%) while detecting zero intrusions. "
            "Phase 3 must prioritize **PR-AUC** and **Macro F1-Score**."
        )
        if label_col:
            counts = df[label_col].value_counts().to_dict()
            fig_class = plot_class_distribution(counts, title="Traffic Distribution by Attack Class")
            st.plotly_chart(fig_class, use_container_width=True)

            # Tabular breakdown
            pcts = (df[label_col].value_counts(normalize=True) * 100).round(2).to_dict()
            dist_df = pd.DataFrame([
                {
                    "Traffic Class": k,
                    "Flow Count": f"{v:,}",
                    "Percentage": f"{pcts[k]}%",
                    "Category": "Normal" if "benign" in str(k).lower() else "Attack",
                }
                for k, v in counts.items()
            ])
            st.dataframe(dist_df, use_container_width=True, hide_index=True)

    with tab_behavior:
        st.subheader("2. Empirical Behavioral Signatures")
        st.markdown(
            "Non-parametric robust statistics (medians and interquartile ranges) isolate behavioral divergences between normal traffic and attacks."
        )
        if label_col:
            comp_result = compare_benign_vs_attack(df, label_col=label_col)

            c_b1, c_b2 = st.columns(2)
            with c_b1:
                st.markdown("##### Flow Metrics Divergence (Log Scale)")
                fig_bars = plot_attack_comparison_bars(comp_result)
                st.plotly_chart(fig_bars, use_container_width=True)

            with c_b2:
                st.markdown("##### TCP Control Flag Activity Rates (%)")
                flag_data = comp_result.get("tcp_flag_comparisons", {})
                fig_flags = plot_tcp_flags_breakdown(flag_data)
                st.plotly_chart(fig_flags, use_container_width=True)

            # Divergence Table
            feat_comps = comp_result.get("feature_comparisons", {})
            if feat_comps:
                st.markdown("##### Detailed Metric Divergence Ratio Table")
                rows = []
                for feat, stats in feat_comps.items():
                    rows.append({
                        "Feature": feat,
                        "Benign Median": f"{stats['benign_median']:.2f}",
                        "Attack Median": f"{stats['attack_median']:.2f}",
                        "Benign IQR": f"{stats['benign_iqr']:.2f}",
                        "Attack IQR": f"{stats['attack_iqr']:.2f}",
                        "Divergence Ratio": f"{stats['divergence_ratio']:.2f}x",
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with tab_distributions:
        st.subheader("3. Feature Histograms & Density Profiles")
        st.markdown("Select any numeric feature to inspect its empirical distribution, skewness, and outliers.")
        numeric_cols = list(df.select_dtypes(include=["number"]).columns)
        if numeric_cols:
            col_sel, col_log = st.columns([3, 1])
            with col_sel:
                selected_feat = st.selectbox("Feature to Profile", numeric_cols, index=0)
            with col_log:
                use_log = st.checkbox("Logarithmic Y-Axis", value=True)

            fig_hist = plot_feature_distribution(df, selected_feat, log_y=use_log)
            st.plotly_chart(fig_hist, use_container_width=True)

            # Feature statistics summary
            s = df[selected_feat]
            st.markdown(
                f"""
                <div style="background-color: #101614; border: 1px solid #1D2824; border-radius: 6px; padding: 12px 16px; display: flex; gap: 24px; font-size: 12px; color: #8B9A91;">
                    <span>Min: <b style="color: #E8F0EB;">{s.min():.2f}</b></span>
                    <span>Q25: <b style="color: #E8F0EB;">{s.quantile(0.25):.2f}</b></span>
                    <span>Median: <b style="color: #16C784;">{s.median():.2f}</b></span>
                    <span>Mean: <b style="color: #E8F0EB;">{s.mean():.2f}</b></span>
                    <span>Q75: <b style="color: #E8F0EB;">{s.quantile(0.75):.2f}</b></span>
                    <span>Max: <b style="color: #E8F0EB;">{s.max():.2f}</b></span>
                    <span>Std: <b style="color: #E8F0EB;">{s.std():.2f}</b></span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tab_correlation:
        st.subheader("4. Multicollinearity & Correlation Matrix")
        st.markdown(
            r"Features with Pearson $|r| \ge 0.90$ introduce linear redundancy, inflate memory, and dilute feature importance. "
            "Phase 3 feature selection will prune these collinear pairs."
        )
        corr_matrix = compute_correlation_matrix(df)
        fig_corr = plot_correlation_heatmap(corr_matrix)
        st.plotly_chart(fig_corr, use_container_width=True)

        pairs = find_high_correlation_pairs(corr_matrix, threshold=0.90)
        if pairs:
            st.markdown("##### Highly Collinear Feature Pairs ($|r| \\ge 0.90$)")
            pairs_df = pd.DataFrame(pairs).rename(columns={
                "feature_1": "Feature 1",
                "feature_2": "Feature 2",
                "correlation": "Pearson r",
            })
            st.dataframe(pairs_df, use_container_width=True, hide_index=True)
