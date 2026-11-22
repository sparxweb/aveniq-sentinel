"""Test fixtures and synthetic datasets for NeuralShield automated tests."""

import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def clean_synthetic_df() -> pd.DataFrame:
    """Fixture providing a well-formed network flow dataframe."""
    return pd.DataFrame({
        "Destination Port": [80, 443, 8080, 22, 53],
        "Flow Duration": [1000.0, 25000.0, 500.0, 12000.0, 300.0],
        "Total Fwd Packets": [10, 25, 5, 12, 2],
        "Total Backward Packets": [8, 30, 4, 15, 2],
        "Total Length of Fwd Packets": [1500.0, 5000.0, 600.0, 2400.0, 120.0],
        "Total Length of Bwd Packets": [4000.0, 12000.0, 1200.0, 6000.0, 200.0],
        "Flow Bytes/s": [5500.0, 680.0, 3600.0, 700.0, 1066.0],
        "Flow Packets/s": [18.0, 2.2, 18.0, 2.25, 13.3],
        "Fwd Header Length": [200, 500, 100, 240, 40],
        "SYN Flag Count": [0, 1, 0, 0, 0],
        "ACK Flag Count": [1, 1, 1, 1, 0],
        "Label": ["BENIGN", "BENIGN", "DDoS", "BENIGN", "PortScan"],
    })


@pytest.fixture
def dirty_synthetic_df() -> pd.DataFrame:
    """Fixture providing raw data with whitespace, redundant columns, infinities, duplicates, and missing values."""
    return pd.DataFrame({
        " Destination Port ": [80, 443, 80, 80, 22],
        " Flow Duration": [1000.0, 0.0, 1000.0, 1000.0, np.nan],
        "Total Fwd Packets": [10, 25, 10, 10, 12],
        "Total Backward Packets": [8, 0, 8, 8, 15],
        "Total Length of Fwd Packets": [1500.0, 5000.0, 1500.0, 1500.0, 2400.0],
        "Total Length of Bwd Packets": [4000.0, 0.0, 4000.0, 4000.0, 6000.0],
        " Flow Bytes/s": [5500.0, np.inf, 5500.0, 5500.0, -np.inf],
        " Flow Packets/s": [18.0, np.inf, 18.0, 18.0, 2.25],
        "Fwd Header Length": [200, 500, 200, 200, 240],
        "Fwd Header Length.1": [200, 500, 200, 200, 240],  # Redundant duplicate
        "SYN Flag Count": [0, 1, 0, 0, 0],
        "ACK Flag Count": [1, 0, 1, 1, 1],
        " Label ": ["BENIGN", "DDoS", "BENIGN", "BENIGN", "DoS Hulk"],
    })


@pytest.fixture
def empty_df() -> pd.DataFrame:
    """Fixture providing an empty dataframe."""
    return pd.DataFrame()
