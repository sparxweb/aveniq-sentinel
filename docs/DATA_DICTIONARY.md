# NeuralShield AI — Data Dictionary & Attack Taxonomy
**Document:** `docs/DATA_DICTIONARY.md`  
**Dataset:** CIC-IDS2017 (MachineLearningCSV release)  
**Version:** Phase 2 Updated  

---

## 1. Feature Groups Overview

The CIC-IDS2017 dataset extracted via CICFlowMeter consists of bidirectional network flow features grouped into 5 core semantic categories:

| Feature Group | Description | Representative Features |
|---|---|---|
| **Traffic Volume** | Bulk byte volume and directional symmetry metrics | `total_fwd_packets`, `total_backward_packets`, `packet_symmetry_ratio`, `byte_symmetry_ratio` |
| **Flow Timing** | Temporal flow intervals and duration statistics | `flow_duration`, `log_flow_duration`, `flow_iat_mean`, `flow_iat_std`, `flow_iat_max` |
| **TCP Behavior** | Transport layer state and control flag flags | `syn_flag_count`, `ack_flag_count`, `syn_packet_density`, `syn_to_ack_ratio` |
| **Traffic Rates** | Throughput velocity per second | `flow_bytes_per_sec`, `flow_packets_per_sec`, `average_packet_size` |
| **Packet Characteristics** | Statistical variation in payload frame lengths | `min_packet_length`, `max_packet_length`, `packet_length_mean`, `packet_length_spread` |

---

## 2. Engineered Phase 2 Features

| Derived Column Name | Semantic Group | Formula / Definition | Security Purpose |
|---|---|---|---|
| `packet_symmetry_ratio` | Volume | $\frac{\text{Total Fwd Packets}}{\max(\text{Total Bwd Packets}, 1.0)}$ | Flags unacknowledged scans and asymmetric floods |
| `byte_symmetry_ratio` | Volume | $\frac{\text{Total Length Fwd}}{\max(\text{Total Length Bwd}, 1.0)}$ | Detects data exfiltration or amplification responses |
| `total_volume_bytes` | Volume | $\text{Total Length Fwd} + \text{Total Length Bwd}$ | Cumulative connection byte footprint |
| `log_flow_duration` | Timing | $\ln(1 + \text{Flow Duration})$ | Stabilizes heavy-tailed microsecond metrics |
| `syn_packet_density` | TCP Behavior | $\frac{\text{SYN Flag Count}}{\max(\text{Total Fwd Packets}, 1.0)}$ | Flags high-density SYN port scanning |
| `syn_to_ack_ratio` | TCP Behavior | $\frac{\text{SYN Flag Count}}{\max(\text{ACK Flag Count}, 1.0)}$ | Identifies half-open connection attempts |
| `packet_length_spread` | Characteristics | $\text{Max Packet Length} - \text{Min Packet Length}$ | Flags fixed-size automated packet floods |

---

## 3. Attack Label Taxonomy & Normalization

NeuralShield normalizes raw dataset labels into standardized cybersecurity categories:

| Raw Label in CIC-IDS2017 | Normalized Taxonomy Category | Threat Classification |
|---|---|---|
| `BENIGN` | `Benign` | Normal Traffic |
| `DDoS` | `DDoS` | Volumetric Attack |
| `PortScan` | `PortScan` | Reconnaissance Attack |
| `Bot` | `Botnet` | Compromised Node C2 |
| `Infiltration` | `Infiltration` | Internal Lateral Movement |
| `Web Attack  Brute Force` | `Web Attack - Brute Force` | Application Attack |
| `Web Attack  XSS` | `Web Attack - XSS` | Web Exploit |
| `Web Attack  Sql Injection` | `Web Attack - SQL Injection` | Database Exploit |
| `FTP-Patator` | `Brute Force - FTP` | Credential Guessing |
| `SSH-Patator` | `Brute Force - SSH` | Credential Guessing |
| `DoS slowloris` | `DoS - Slowloris` | Resource Exhaustion |
| `DoS Slowhttptest` | `DoS - SlowHTTPTest` | Resource Exhaustion |
| `DoS Hulk` | `DoS - Hulk` | Volumetric DoS |
| `DoS GoldenEye` | `DoS - GoldenEye` | Application DoS |
| `Heartbleed` | `Heartbleed` | Memory Disclosure Exploit |
