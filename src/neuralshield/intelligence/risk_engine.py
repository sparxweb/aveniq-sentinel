"""Heuristic network anomaly and cybersecurity threat scoring engine (pre-ML)."""

from typing import Dict, Any, List
import pandas as pd
import numpy as np


class NetworkRiskEngine:
    """Calculates defensible cybersecurity risk scores based on network traffic dynamics.
    Used for Phase 1 baseline assessment prior to Phase 2 ML model deployment.
    """
    
    @staticmethod
    def calculate_flow_risk_score(row: pd.Series) -> Dict[str, Any]:
        """Evaluates a single network flow against documented behavioral heuristics:
        1. SYN scan pattern (high SYN flag, 0 backward packets).
        2. High-volume volumetric flood (extreme packet rate, short duration).
        3. Asymmetric payload distribution.
        
        Returns:
            Dict containing risk_score (0-100), risk_level, and triggered indicators.
        """
        score = 0.0
        indicators = []
        
        # Heuristic 1: SYN Scan signature
        syn_flags = float(row.get("syn_flag_count", row.get("SYN Flag Count", 0)))
        bwd_pkts = float(row.get("total_backward_packets", row.get("Total Backward Packets", 0)))
        if syn_flags >= 1.0 and bwd_pkts == 0:
            score += 35.0
            indicators.append("Unanswered SYN handshake (PortScan pattern)")
            
        # Heuristic 2: Extreme packet rate (Volumetric DoS/DDoS pattern)
        pkt_rate = float(row.get("flow_packets_per_sec", row.get("Flow Packets/s", 0)))
        if pkt_rate > 50_000:
            score += 40.0
            indicators.append("High flow packet rate (>50k pkts/sec)")
        elif pkt_rate > 10_000:
            score += 20.0
            indicators.append("Elevated packet rate (>10k pkts/sec)")
            
        # Heuristic 3: Zero or near-zero flow duration with high packet count
        duration = float(row.get("flow_duration", row.get("Flow Duration", 1)))
        fwd_pkts = float(row.get("total_fwd_packets", row.get("Total Fwd Packets", 1)))
        if duration <= 10.0 and fwd_pkts > 5.0:
            score += 25.0
            indicators.append("Micro-burst flow with anomalous packet density")
            
        score = min(100.0, max(0.0, score))
        
        if score >= 70.0:
            level = "Critical"
        elif score >= 40.0:
            level = "High"
        elif score >= 20.0:
            level = "Moderate"
        else:
            level = "Low"
            
        return {
            "risk_score": round(score, 1),
            "risk_level": level,
            "indicators": indicators,
        }

    @classmethod
    def evaluate_dataset_risks(cls, df: pd.DataFrame, sample_size: int = 500) -> pd.DataFrame:
        """Evaluates a batch of flows, attaching risk scores and levels."""
        sub = df.head(sample_size).copy()
        results = [cls.calculate_flow_risk_score(row) for _, row in sub.iterrows()]
        
        sub["risk_score"] = [r["risk_score"] for r in results]
        sub["risk_level"] = [r["risk_level"] for r in results]
        return sub
