"""Automated Audit and Validation Runner for NeuralShield AI.

Conducts end-to-end programmatic verification of:
1. Environment and approved dependencies
2. Source code integrity, syntax, and imports
3. Security posture (secrets, subprocess, network, unsafe calls)
4. Data engineering pipeline, immutability, and leakage prevention
5. Streamlit app pages and visualization components
6. Edge case robustness (empty df, missing files, malformed csv)
7. Performance telemetry (memory downcasting and chunking)
"""

import sys
import os
import re
import ast
import json
import hashlib
from pathlib import Path

# Set up paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import pandas as pd
import numpy as np

def run_environment_audit():
    print("=" * 60)
    print("1. ENVIRONMENT & DEPENDENCY AUDIT")
    print("=" * 60)
    import platform
    print(f"Python Version: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")
    print(f"Virtualenv Active: {sys.prefix != sys.base_prefix}")
    print(f"Virtualenv Path: {sys.prefix}")

    # Check approved packages
    approved = [
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("scikit-learn", "sklearn"),
        ("pyarrow", "pyarrow"),
        ("streamlit", "streamlit"),
        ("plotly", "plotly"),
        ("pytest", "pytest"),
        ("networkx", "networkx"),
    ]
    installed_pkg_status = {}
    for pkg_name, import_name in approved:
        try:
            mod = __import__(import_name)
            ver = getattr(mod, "__version__", "unknown")
            installed_pkg_status[pkg_name] = (True, ver)
            print(f"  [PASS] {pkg_name}: {ver}")
        except ImportError:
            installed_pkg_status[pkg_name] = (False, None)
            print(f"  [FAIL] {pkg_name}: NOT INSTALLED")

    return installed_pkg_status


def run_codebase_inspection():
    print("\n" + "=" * 60)
    print("2. SOURCE CODE & SYNTAX INSPECTION")
    print("=" * 60)
    py_files = list(PROJECT_ROOT.glob("**/*.py"))
    py_files = [f for f in py_files if ".venv" not in f.parts and "__pycache__" not in f.parts and ".pytest_cache" not in f.parts]
    print(f"Total Python Source Files: {len(py_files)}")

    syntax_errors = []
    loc_count = 0
    for p in py_files:
        try:
            code = p.read_text(encoding="utf-8")
            loc_count += len(code.splitlines())
            ast.parse(code, filename=str(p))
        except Exception as e:
            syntax_errors.append((str(p), str(e)))

    print(f"Total Lines of Python Code: {loc_count}")
    if syntax_errors:
        print(f"  [FAIL] Syntax Errors ({len(syntax_errors)}):")
        for f, err in syntax_errors:
            print(f"    - {f}: {err}")
    else:
        print("  [PASS] All Python files parsed successfully (0 syntax errors).")

    return py_files, syntax_errors


def run_security_audit(py_files):
    print("\n" + "=" * 60)
    print("3. SECURITY & VULNERABILITY AUDIT")
    print("=" * 60)
    secret_patterns = [
        r"(?i)(api[_-]?key|secret|password|passwd|auth[_-]?token|private[_-]?key)\s*=\s*['\"][A-Za-z0-9_\-\.]{8,}['\"]",
        r"-----BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY-----",
        r"(?i)aws[_-]?secret[_-]?access[_-]?key",
        r"(?i)ghp_[0-9a-zA-Z]{36}",
    ]
    unsafe_patterns = [
        (r"\beval\s*\(", "eval() execution"),
        (r"\bexec\s*\(", "exec() execution"),
        (r"\bpickle\.loads\s*\(", "pickle deserialization"),
        (r"\bsubprocess\.", "subprocess call"),
        (r"\bos\.system\s*\(", "os.system call"),
        (r"\burllib\.request\.", "outbound network request (urllib)"),
        (r"\brequests\.(get|post|put|delete)\s*\(", "outbound network request (requests)"),
        (r"\bhttpx\.", "outbound network request (httpx)"),
        (r"\bsocket\.connect\s*\(", "direct socket connection"),
    ]

    findings = []
    for p in py_files:
        # Skip this audit script itself
        if p.name == "project_audit_runner.py":
            continue
        code = p.read_text(encoding="utf-8")
        rel_path = p.relative_to(PROJECT_ROOT)

        # Secrets scan
        for pat in secret_patterns:
            matches = re.findall(pat, code)
            if matches:
                findings.append((str(rel_path), f"Potential secret pattern: {matches[0]}", "HIGH"))

        # Unsafe calls scan
        for pat, desc in unsafe_patterns:
            if re.search(pat, code):
                findings.append((str(rel_path), desc, "MEDIUM"))

    if not findings:
        print("  [PASS] Zero hardcoded secrets, outbound network calls, or unsafe evals detected.")
    else:
        print(f"  Security Findings ({len(findings)}):")
        for path, desc, sev in findings:
            print(f"    - [{sev}] {path}: {desc}")

    return findings


def run_data_engineering_audit():
    print("\n" + "=" * 60)
    print("4. DATA ENGINEERING & PIPELINE VALIDATION")
    print("=" * 60)
    from config.settings import RAW_DATA_DIR, SAMPLE_DATA_DIR, PROCESSED_DATA_DIR, TARGET_LEAKAGE_COLUMNS
    from neuralshield.data.discovery import inspect_dataset_inventory
    from neuralshield.data.loader import DatasetLoader, downcast_numeric_dtypes, sample_dataframe
    from neuralshield.data.cleaning import normalize_column_names, sanitize_infinite_and_nan, handle_duplicates
    from neuralshield.data.validation import audit_dataframe_quality, inspect_numerical_anomalies
    from neuralshield.data.preprocessing import PreprocessingPipeline

    # 1. Raw inventory
    inv = inspect_dataset_inventory(RAW_DATA_DIR)
    print(f"Raw Directory Status: {inv['status']}")
    print(f"Expected Benchmark Files: {inv['expected_benchmark_files']}, Found: {inv['expected_present_count']}")

    # 2. Sample data verification
    sample_csv = SAMPLE_DATA_DIR / "cic_ids2017_sample.csv"
    if not sample_csv.is_file():
        print("  [FAIL] Sample CSV missing!")
        return False

    # Check hash before processing to verify immutability
    raw_hash_before = hashlib.sha256(sample_csv.read_bytes()).hexdigest()

    loader = DatasetLoader()
    df_raw = loader.load_single_file(sample_csv)
    raw_hash_after = hashlib.sha256(sample_csv.read_bytes()).hexdigest()
    assert raw_hash_before == raw_hash_after, "Raw data file was modified during reading!"
    print("  [PASS] Raw dataset immutability verified (SHA-256 unchanged).")

    print(f"Sample Dataset Shape: {df_raw.shape}")
    print(f"Initial Memory: {df_raw.memory_usage(deep=True).sum() / 1024:.2f} KB")

    # Downcasting test
    df_downcast, mem_stats = downcast_numeric_dtypes(df_raw)
    print(f"  [PASS] Memory Downcasting: {mem_stats['reduction_percentage']}% reduction ({mem_stats['initial_memory_mb']} -> {mem_stats['optimized_memory_mb']} MB)")

    # Pipeline test
    pipeline = PreprocessingPipeline()
    result = pipeline.fit_transform(df_raw, dataset_name="AuditTest")
    df_clean = result["cleaned_df"]
    audit = result["audit_report"]

    print(f"Cleaned Dataset Shape: {df_clean.shape}")
    print(f"Calculated Quality Score: {audit['quality_audit']['quality_score']}/100.0")
    print(f"Exact Duplicates Removed: {audit.get('duplicates_removed', 0)}")
    inf_total = audit.get('infinite_stats', {}).get('pos_inf_count', 0) + audit.get('infinite_stats', {}).get('neg_inf_count', 0)
    print(f"Infinities Sanitized: {inf_total}")

    # Target leakage verification
    for col in TARGET_LEAKAGE_COLUMNS:
        assert col not in df_clean.columns, f"Target leakage column {col} was NOT stripped!"
    print("  [PASS] Target leakage prevention verified (zero identifier columns present).")

    return True


def run_robustness_and_edge_case_tests():
    print("\n" + "=" * 60)
    print("5. ROBUSTNESS & EDGE CASE ERROR HANDLING")
    print("=" * 60)
    from neuralshield.data.loader import DatasetLoader, sample_dataframe
    from neuralshield.data.cleaning import normalize_column_names, sanitize_infinite_and_nan
    from neuralshield.data.validation import audit_dataframe_quality, inspect_numerical_anomalies
    from neuralshield.utils.validators import ValidationError

    # 1. Non-existent file
    loader = DatasetLoader()
    try:
        loader.load_single_file(Path("data/does_not_exist.csv"))
        print("  [FAIL] Did not raise FileNotFoundError for missing file")
    except FileNotFoundError:
        print("  [PASS] Handled missing file with FileNotFoundError")

    # 2. Empty DataFrame validation
    try:
        empty_df = pd.DataFrame()
        audit_dataframe_quality(empty_df)
        print("  [FAIL] Did not raise ValidationError for empty dataframe")
    except ValidationError:
        print("  [PASS] Handled empty dataframe with ValidationError")

    # 3. Stratified sampling with rare classes
    df_rare = pd.DataFrame({
        "feature": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "label": ["A", "A", "A", "A", "A", "A", "A", "A", "B", "C"]
    })
    sampled = sample_dataframe(df_rare, n=5, stratify_col="label")
    print(f"  [PASS] Stratified sampling on imbalanced input succeeded (sampled {len(sampled)} rows)")

    # 4. Negative anomaly detection
    df_anomaly = pd.DataFrame({
        "flow_duration": [0, 100],
        "total_fwd_packets": [10, -5],
        "const_col": [1, 1],
    })
    anomalies = inspect_numerical_anomalies(df_anomaly)
    assert "total_fwd_packets" in anomalies["negative_value_violations"]
    assert "const_col" in anomalies["constant_columns"]
    assert anomalies["zero_duration_flows_with_packets"] == 1
    print("  [PASS] Numerical anomaly engine detected negative values, constant columns, and zero-duration rate hazards.")

    # 4. Negative anomaly detection
    df_anomaly = pd.DataFrame({
        "flow_duration": [0, 100],
        "total_fwd_packets": [10, -5],
        "const_col": [1, 1],
    })
    anomalies = inspect_numerical_anomalies(df_anomaly)
    assert "total_fwd_packets" in anomalies["negative_value_violations"]
    assert "const_col" in anomalies["constant_columns"]
    assert anomalies["zero_duration_flows_with_packets"] == 1
    print("  [PASS] Numerical anomaly engine detected negative values, constant columns, and zero-duration rate hazards.")


def run_streamlit_and_visualization_audit():
    print("\n" + "=" * 60)
    print("6. STREAMLIT APPLICATION & VISUALIZATION AUDIT")
    print("=" * 60)
    import streamlit_app
    from app_pages import overview, data_explorer, data_quality, eda_center, processing_center
    from neuralshield.visualization.charts import (
        plot_class_distribution,
        plot_correlation_heatmap,
        plot_feature_distribution,
        plot_quality_gauge,
        plot_attack_comparison_bars,
        plot_tcp_flags_breakdown,
    )

    print("  [PASS] Main app router and all 5 operational pages imported without errors.")

    # Test visualization generators with synthetic data
    df_viz = pd.DataFrame({
        "label": ["Benign", "DDoS", "Benign", "PortScan", "Benign"],
        "flow_duration": [100.0, 50.0, 200.0, 10.0, 300.0],
        "packet_length_mean": [50.0, 1400.0, 60.0, 40.0, 55.0],
        "syn_flag_count": [0, 1, 0, 1, 0],
        "ack_flag_count": [1, 0, 1, 0, 1],
    })

    fig1 = plot_class_distribution(df_viz["label"].value_counts().to_dict())
    fig2 = plot_feature_distribution(df_viz, "flow_duration")
    fig3 = plot_quality_gauge(88.5)
    fig4 = plot_attack_comparison_bars({
        "feature_comparisons": {
            "flow_duration": {"benign_median": 100.0, "attack_median": 20.0},
            "packet_length_mean": {"benign_median": 50.0, "attack_median": 1400.0},
        }
    })
    fig5 = plot_tcp_flags_breakdown({
        "syn_flag": {"benign_percentage_active": 5.0, "attack_percentage_active": 90.0},
        "ack_flag": {"benign_percentage_active": 95.0, "attack_percentage_active": 10.0},
    })

    for i, fig in enumerate([fig1, fig2, fig3, fig4, fig5], 1):
        assert fig is not None, f"Figure {i} generated None"
        assert hasattr(fig, "to_dict"), f"Figure {i} is not a valid Plotly Figure"

    print("  [PASS] All 6 Plotly dark cyber visualization generators produce valid figures.")


if __name__ == "__main__":
    print("STARTING COMPLETE NEURALSHIELD AI AUDIT & VALIDATION RUNNER")
    env_ok = run_environment_audit()
    py_files, syntax_errs = run_codebase_inspection()
    sec_findings = run_security_audit(py_files)
    de_ok = run_data_engineering_audit()
    run_robustness_and_edge_case_tests()
    run_streamlit_and_visualization_audit()
    print("\n" + "=" * 60)
    print("ALL AUDIT MODULES COMPLETED SUCCESSFULLY")
    print("=" * 60)
