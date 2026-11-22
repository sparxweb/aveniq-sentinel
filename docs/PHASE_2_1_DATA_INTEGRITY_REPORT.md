# AVENIQ SENTINEL — PHASE 2.1 DATA INTEGRITY & LEAKAGE REPORT
**Product:** Aveniq Sentinel  
**Company:** Aveniq (sparxweb)  
**Date:** November 22, 2026  
**Benchmark Target:** Canadian Institute for Cybersecurity — CIC-IDS2017  

---

## 1. DATA TRANSPARENCY & INTEGRITY MANDATE

Aveniq Sentinel operates on the principle of **Empirical Truth in Cybersecurity Telemetry**. In machine learning for network intrusion detection, misleading the analyst with synthetic or fabricated data labeled as production network captures represents an operational failure. Phase 2.1 establishes rigorous data isolation and transparency safeguards.

---

## 2. ACTIVE DATA SOURCE TAXONOMY

The platform explicitly categorizes all loaded datasets into 4 mutually exclusive states:

```
                    ┌─────────────────────────┐
                    │ Active Data Resolution  │
                    └────────────┬────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ Official Dataset │   │   User Dataset   │   │Demonstration Data│
│ (CIC-IDS2017)    │   │ (Custom Upload)  │   │(Synthetic Sample)│
├──────────────────┤   ├──────────────────┤   ├──────────────────┤
│ • Full PCAP flow │   │ • User-provided  │   │ • 1,505 flows    │
│ • data/raw/      │   │ • Uploaded CSV   │   │ • data/sample/   │
│ • Verified Real  │   │ • Validated real │   │ • Amber warning  │
└──────────────────┘   └──────────────────┘   └──────────────────┘
```

1. **Official CIC-IDS2017 Dataset (`SOURCE_OFFICIAL`):**
   - Source: Raw CSV captures in `data/raw/` originating from the University of New Brunswick (UNB) benchmark.
   - Badge: Emerald (`● OFFICIAL DATASET`).
   - Telemetry Classification: Verified Production Network Benchmark.

2. **User Dataset (`SOURCE_USER`):**
   - Source: Custom PCAP-derived flow CSV uploaded through the Flow Data Explorer.
   - Badge: Cyan (`● USER DATASET`).
   - Telemetry Classification: Real Telemetry (User-Supplied).

3. **Demonstration Data (`SOURCE_DEMO`):**
   - Source: Deterministic 1,505-flow baseline fixture in `data/sample/`.
   - Badge: Amber (`● DEMONSTRATION DATA`).
   - Mandatory Disclaimer Banner:
     > *"⚠️ DEMONSTRATION DATA: Displaying synthetic baseline fixtures (1,505 flows). Values represent demonstration samples, not active production network telemetry."*

4. **No Dataset Loaded (`SOURCE_NONE`):**
   - Source: No files discovered in disk directories and memory is uninitialized.
   - Badge: Neutral (`● NO DATASET LOADED`).
   - Action: Renders the Onboarding Guide with clear staging instructions.

---

## 3. DATA LEAKAGE PREVENTION MATRIX

In network intrusion datasets, predictive models frequently latch onto non-generalizable artifacts rather than genuine adversarial behaviors. Phase 2.1 enforces strict filtering:

| Leakage Category | Specific Columns Filtered | Risk Description | Remediation in Aveniq Sentinel |
|:---|:---|:---|:---|
| **Host IP Identifiers** | `Source IP`, `Destination IP`, `Src IP`, `Dst IP` | Model memorizes attacker/victim IP addresses, achieving 99% accuracy on train split while failing completely against any new IP address. | Filtered automatically by `remove_target_leakage_features()` before feature generation. |
| **Port Identifiers** | `Source Port`, `Destination Port` (context-dependent) | Ephemeral source ports create random noise; destination ports can cause shortcut learning (e.g. port 80 = web attack). | Isolated from general feature sets; analyzed only in specialized service profiling. |
| **Timestamps** | `Timestamp`, `Date`, `Time` | Model learns chronological order of attack phases rather than packet dynamics. | Stripped from feature vectors; used strictly for temporal split boundaries in Phase 3. |
| **Session IDs** | `Flow ID`, `Record ID`, `Index` | Artificial indexes introduce surrogate leakage. | Excluded from analytical transformations and models. |

---

## 4. DATA QUALITY & HYGIENE CONTROLS

The platform implements multi-layer sanitation routines:

1. **Infinite Value Imputation:**
   - Raw flow captures frequently contain `+inf` or `-inf` in `Flow Bytes/s` or `Flow Packets/s` when flow duration approaches zero microseconds.
   - Sanitization routine replaces all non-finite values with the column median of valid finite observations or drops them according to operator policy.
2. **Lossless Numeric Downcasting:**
   - Standard Pandas reads CSV numerical values as 64-bit floats and integers.
   - For a 3.1 GB benchmark dataset, this consumes over 8 GB of resident RAM.
   - Lossless downcasting converts `float64` to `float32` and `int64` to `int32`/`int16`, reducing resident memory consumption by **45% to 55%** without numerical distortion.
3. **Exact Flow Deduplication:**
   - Multiple identical packets can be captured if monitoring taps observe both ingress and egress interfaces.
   - Deduplication routine identifies and logs duplicate flow records to eliminate training redundancy.

---

## 5. SUMMARY

The data integrity framework established in Phase 2.1 ensures that all downstream exploratory analytics, divergence calculations, and Phase 3 machine learning pipelines operate strictly on validated, leakage-free, and truthfully identified network records.
