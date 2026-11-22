# NeuralShield AI — Feature Engineering & Semantic Semantics Report
**Document:** `docs/FEATURE_ENGINEERING_REPORT.md`  
**Dataset:** CIC-IDS2017 Feature Mapping  

---

## 1. Five Core Semantic Feature Groups

NeuralShield AI maps network flow telemetry into 5 distinct analytical categories based on domain cybersecurity behavior:

### Group 1: Network Traffic Volume
- **Underlying Mechanism:** Measures bidirectional transmission bulk and payload asymmetries.
- **Engineered Features:**
  - `packet_symmetry_ratio`: $\frac{\text{Total Fwd Packets}}{\max(\text{Total Bwd Packets}, 1.0)}$. Heavy divergence signals unilateral flooding or unacknowledged scanning.
  - `byte_symmetry_ratio`: $\frac{\text{Total Length Fwd Packets}}{\max(\text{Total Length Bwd Packets}, 1.0)}$. Highlights data exfiltration or amplification response.
  - `total_volume_bytes`: Cumulative bytes across both transmission directions.

### Group 2: Network Flow Timing & Inter-Arrival Dynamics
- **Underlying Mechanism:** Captures temporal intervals between packet arrivals and total connection lifespan.
- **Engineered Features:**
  - `log_flow_duration`: $\ln(1 + \text{Flow Duration})$. Stabilizes severe right-skewness spanning 5+ orders of magnitude in microsecond duration.
  - `flow_iat_mean`, `flow_iat_std`, `flow_iat_max`, `flow_iat_min`: Inter-arrival timing variance used to distinguish automated bot scripts from human-driven web browsing.

### Group 3: TCP Connection Behavior & Control Flags
- **Underlying Mechanism:** Tracks transport layer state transitions during three-way handshakes and terminations.
- **Engineered Features:**
  - `syn_packet_density`: $\frac{\text{SYN Flag Count}}{\max(\text{Total Fwd Packets}, 1.0)}$. Elevated during half-open SYN port scanning.
  - `syn_to_ack_ratio`: $\frac{\text{SYN Flag Count}}{\max(\text{ACK Flag Count}, 1.0)}$. Indicates uncompleted connection attempts.
  - `fin_flag_count`, `rst_flag_count`, `psh_flag_count`, `urg_flag_count`: Explicit teardown and urgent push telemetry.

### Group 4: Traffic Rates & Throughput Dynamics
- **Underlying Mechanism:** Normalizes packet and byte counts against duration to determine volumetric velocity.
- **Engineered Features:**
  - `flow_bytes_per_sec`: Byte transfer rate. Sanitized from $\pm\infty$ occurrences caused by zero-duration flows.
  - `flow_packets_per_sec`: Packet arrival velocity.
  - `average_packet_size`: $\frac{\text{Total Volume Bytes}}{\text{Total Packet Count}}$. Distinguishes jumbo payload transfers from lightweight control pings.

### Group 5: Packet Length Characteristics
- **Underlying Mechanism:** Evaluates statistical variation in payload buffer sizes.
- **Engineered Features:**
  - `packet_length_spread`: $\text{Max Packet Length} - \text{Min Packet Length}$.
  - `packet_length_mean`, `packet_length_std`, `packet_length_variance`: Discovers fixed-size packet generation (typical of DDoS stress testing tools).

---

## 2. Target Leakage Prevention

NeuralShield strictly strips the following features prior to model preparation:
1. `Flow ID`: Unique string concatenation of 5-tuple socket information.
2. `Source IP`: Synthetic testbed attacker nodes originate from fixed IP addresses (e.g. `192.168.10.50`), causing models to memorize host identities rather than traffic mechanics.
3. `Destination IP`: Identifies targeted victim servers in the testbed.
4. `Timestamp`: Attack tools were executed at predetermined times; temporal order can introduce chronological shortcut learning.
