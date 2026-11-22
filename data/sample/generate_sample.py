"""Generates a clearly labeled synthetic demonstration dataset matching the CIC-IDS2017 schema."""

from pathlib import Path
import numpy as np
import pandas as pd


def generate_cic_sample(num_rows: int = 1500, output_dir: Path = None) -> pd.DataFrame:
    """Creates a deterministic synthetic dataset with real CIC-IDS2017 column names and attack patterns."""
    if output_dir is None:
        output_dir = Path(__file__).resolve().parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    np.random.seed(42)
    
    # Class labels with class imbalance: 80% Benign, 10% DDoS, 7% PortScan, 3% Bot
    labels = np.random.choice(
        ["BENIGN", "DDoS", "PortScan", "Bot"],
        size=num_rows,
        p=[0.80, 0.10, 0.07, 0.03],
    )
    
    # Destination ports based on class
    dest_ports = []
    for lbl in labels:
        if lbl == "BENIGN":
            dest_ports.append(np.random.choice([80, 443, 8080, 53, 22]))
        elif lbl == "DDoS":
            dest_ports.append(np.random.choice([80, 443]))
        elif lbl == "PortScan":
            dest_ports.append(int(np.random.randint(1024, 65535)))
        else:
            dest_ports.append(np.random.choice([6667, 8080, 4444]))
            
    # Flow durations (microseconds)
    flow_duration = np.where(
        labels == "DDoS",
        np.random.exponential(scale=1000, size=num_rows),
        np.random.exponential(scale=50000, size=num_rows),
    )
    
    # Forward & Backward packets
    total_fwd_packets = np.where(
        labels == "DDoS",
        np.random.randint(50, 500, size=num_rows),
        np.random.randint(1, 40, size=num_rows),
    )
    total_bwd_packets = np.where(
        labels == "PortScan",
        np.zeros(num_rows, dtype=int),
        np.random.randint(0, 30, size=num_rows),
    )
    
    fwd_len_mean = np.random.uniform(20.0, 500.0, size=num_rows)
    bwd_len_mean = np.where(labels == "PortScan", 0.0, np.random.uniform(40.0, 1400.0, size=num_rows))
    
    fwd_bytes = total_fwd_packets * fwd_len_mean
    bwd_bytes = total_bwd_packets * bwd_len_mean
    
    # Flow rates (bytes/s and packets/s)
    safe_duration = np.maximum(flow_duration / 1e6, 1e-6)
    flow_bytes_per_sec = (fwd_bytes + bwd_bytes) / safe_duration
    flow_packets_per_sec = (total_fwd_packets + total_bwd_packets) / safe_duration
    
    # Forward header length
    fwd_header_len = total_fwd_packets * 20
    bwd_header_len = total_bwd_packets * 20
    
    # Flags
    syn_flag = np.where(labels == "PortScan", 1, np.random.choice([0, 1], size=num_rows, p=[0.9, 0.1]))
    ack_flag = np.where(labels == "PortScan", 0, np.random.choice([0, 1], size=num_rows, p=[0.3, 0.7]))
    fin_flag = np.random.choice([0, 1], size=num_rows, p=[0.85, 0.15])
    
    df = pd.DataFrame({
        "Destination Port": dest_ports,
        "Flow Duration": flow_duration.round(2),
        "Total Fwd Packets": total_fwd_packets,
        "Total Backward Packets": total_bwd_packets,
        "Total Length of Fwd Packets": fwd_bytes.round(2),
        "Total Length of Bwd Packets": bwd_bytes.round(2),
        "Fwd Packet Length Max": (fwd_len_mean * 1.5).round(2),
        "Fwd Packet Length Min": (fwd_len_mean * 0.5).round(2),
        "Fwd Packet Length Mean": fwd_len_mean.round(2),
        "Fwd Packet Length Std": (fwd_len_mean * 0.2).round(2),
        "Bwd Packet Length Max": (bwd_len_mean * 1.5).round(2),
        "Bwd Packet Length Min": (bwd_len_mean * 0.5).round(2),
        "Bwd Packet Length Mean": bwd_len_mean.round(2),
        "Bwd Packet Length Std": (bwd_len_mean * 0.2).round(2),
        "Flow Bytes/s": flow_bytes_per_sec.round(2),
        "Flow Packets/s": flow_packets_per_sec.round(2),
        "Flow IAT Mean": np.random.uniform(10.0, 1000.0, size=num_rows).round(2),
        "Flow IAT Std": np.random.uniform(5.0, 500.0, size=num_rows).round(2),
        "Flow IAT Max": np.random.uniform(50.0, 5000.0, size=num_rows).round(2),
        "Flow IAT Min": np.random.uniform(1.0, 50.0, size=num_rows).round(2),
        "Fwd Header Length": fwd_header_len,
        "Fwd Header Length.1": fwd_header_len,  # Intentionally duplicate redundant column
        "Bwd Header Length": bwd_header_len,
        "Fwd Packets/s": (total_fwd_packets / safe_duration).round(2),
        "Bwd Packets/s": (total_bwd_packets / safe_duration).round(2),
        "Min Packet Length": np.random.uniform(0, 20, size=num_rows).round(2),
        "Max Packet Length": np.random.uniform(500, 1500, size=num_rows).round(2),
        "Packet Length Mean": ((fwd_len_mean + bwd_len_mean) / 2).round(2),
        "FIN Flag Count": fin_flag,
        "SYN Flag Count": syn_flag,
        "RST Flag Count": np.zeros(num_rows, dtype=int),
        "PSH Flag Count": np.random.choice([0, 1], size=num_rows, p=[0.7, 0.3]),
        "ACK Flag Count": ack_flag,
        "URG Flag Count": np.zeros(num_rows, dtype=int),
        "Down/Up Ratio": (total_bwd_packets / np.maximum(1, total_fwd_packets)).round(2),
        "Average Packet Size": ((fwd_bytes + bwd_bytes) / np.maximum(1, total_fwd_packets + total_bwd_packets)).round(2),
        "Init_Win_bytes_forward": np.random.choice([29200, 8192, -1], size=num_rows),
        "Init_Win_bytes_backward": np.random.choice([29200, 8192, -1], size=num_rows),
        "Label": labels,
    })
    
    # Intentionally insert a few infinite and missing values to verify cleaning pipeline
    df.loc[5, "Flow Bytes/s"] = np.inf
    df.loc[12, "Flow Packets/s"] = np.inf
    df.loc[25, "Flow Bytes/s"] = -np.inf
    df.loc[30, "Flow IAT Mean"] = np.nan
    
    # Intentionally append exact duplicate rows to test duplicate handling
    duplicates = df.iloc[[10, 15, 20, 25, 50]].copy()
    df = pd.concat([df, duplicates], ignore_index=True)
    
    # Export synthetic demo files
    csv_path = output_dir / "cic_ids2017_sample.csv"
    parquet_path = output_dir / "cic_ids2017_sample.parquet"
    
    df.to_csv(csv_path, index=False)
    df.to_parquet(parquet_path, index=False, engine="pyarrow")
    print(f"Generated sample dataset: {len(df)} rows -> {csv_path.name} & {parquet_path.name}")
    return df


if __name__ == "__main__":
    generate_cic_sample()
