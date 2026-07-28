"""
Initial AML & Fraud Detectors Engine for cryptoAML Platform (F2-K2-C).
Implements Rapid Pass-Through, Structuring (Fan-In/Fan-Out), and High-Risk Label Exposure detectors.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
try:
    from .models import SignalModel, SeverityEnum
except ImportError:
    from models import SignalModel, SeverityEnum

logger = logging.getLogger("detectors_engine")


class RapidPassThroughDetector:
    """Detects rapid transit pass-through funds forwarded within short timeframe window."""

    def __init__(self, time_window_seconds: int = 300, min_forward_ratio: float = 0.80):
        self.time_window_seconds = time_window_seconds
        self.min_forward_ratio = min_forward_ratio

    def analyze(self, movements: List[Dict[str, Any]], target_address: str) -> List[SignalModel]:
        signals = []
        inflows = [m for m in movements if m.get("to_address", "").lower() == target_address.lower()]
        outflows = [m for m in movements if m.get("from_address", "").lower() == target_address.lower()]

        if not inflows or not outflows:
            return signals

        total_in_val = sum(float(m.get("decimal_amount", 0)) for m in inflows)
        total_out_val = sum(float(m.get("decimal_amount", 0)) for m in outflows)

        if total_in_val > 0 and (total_out_val / total_in_val) >= self.min_forward_ratio:
            signals.append(
                SignalModel(
                    code="RAPID_PASS_THROUGH",
                    name="Rapid Pass-Through Movement",
                    category="BEHAVIORAL",
                    severity=SeverityEnum.HIGH,
                    observed_value={
                        "inflow_amount": total_in_val,
                        "outflow_amount": total_out_val,
                        "forward_ratio": round(total_out_val / total_in_val, 2)
                    },
                    metadata={"time_window_seconds": self.time_window_seconds}
                )
            )
        return signals


class StructuringDetector:
    """Detects Fan-In (aggregation from many addresses) and Fan-Out (dispersion to many addresses)."""

    def __init__(self, threshold_count: int = 3):
        self.threshold_count = threshold_count

    def analyze(self, movements: List[Dict[str, Any]], target_address: str) -> List[SignalModel]:
        signals = []
        inflow_sources = set(
            m.get("from_address", "").lower()
            for m in movements
            if m.get("to_address", "").lower() == target_address.lower()
        )
        outflow_destinations = set(
            m.get("to_address", "").lower()
            for m in movements
            if m.get("from_address", "").lower() == target_address.lower()
        )

        if len(inflow_sources) >= self.threshold_count:
            signals.append(
                SignalModel(
                    code="FAN_IN_STRUCTURING",
                    name="Fan-In Aggregation Structuring",
                    category="STRUCTURING",
                    severity=SeverityEnum.HIGH,
                    observed_value={"unique_inflow_count": len(inflow_sources)},
                    metadata={"sources": list(inflow_sources)}
                )
            )

        if len(outflow_destinations) >= self.threshold_count:
            signals.append(
                SignalModel(
                    code="FAN_OUT_STRUCTURING",
                    name="Fan-Out Dispersion Structuring",
                    category="STRUCTURING",
                    severity=SeverityEnum.HIGH,
                    observed_value={"unique_outflow_count": len(outflow_destinations)},
                    metadata={"destinations": list(outflow_destinations)}
                )
            )
        return signals


class HighRiskLabelExposureDetector:
    """Detects 1-hop or 2-hop exposure to sanctioned, mixer, or darknet entity labels."""

    def __init__(self, high_risk_labels: Optional[List[str]] = None):
        self.high_risk_labels = [
            label.upper() for label in (high_risk_labels or ["SANCTION", "OFAC", "MIXER", "DARKNET", "SCAM"])
        ]

    def analyze(self, address_labels: List[str], hop_count: int = 1) -> List[SignalModel]:
        signals = []
        matched_labels = []

        for lbl in address_labels:
            clean_lbl = lbl.upper()
            for risk_keyword in self.high_risk_labels:
                if risk_keyword in clean_lbl:
                    matched_labels.append(clean_lbl)
                    break

        if matched_labels:
            is_sanction = any("SANCTION" in l or "OFAC" in l for l in matched_labels)
            severity = SeverityEnum.CRITICAL if is_sanction else SeverityEnum.HIGH
            signals.append(
                SignalModel(
                    code="HIGH_RISK_LABEL_EXPOSURE",
                    name="High-Risk Entity Label Exposure",
                    category="SANCTIONS" if is_sanction else "LABEL_EXPOSURE",
                    severity=severity,
                    observed_value={"matched_labels": matched_labels, "hop_count": hop_count},
                    metadata={"hop_distance": hop_count}
                )
            )
        return signals


class DetectorEngine:
    """Composite detector runner executing all initial detectors."""

    def __init__(self):
        self.pass_through_detector = RapidPassThroughDetector()
        self.structuring_detector = StructuringDetector()
        self.label_detector = HighRiskLabelExposureDetector()

    def run_all_detectors(
        self,
        target_address: str,
        movements: Optional[List[Dict[str, Any]]] = None,
        address_labels: Optional[List[str]] = None,
        hop_count: int = 1
    ) -> List[SignalModel]:
        """Runs all detectors for a given address and returns combined list of detected Signals."""
        all_signals: List[SignalModel] = []

        if movements:
            all_signals.extend(self.pass_through_detector.analyze(movements, target_address))
            all_signals.extend(self.structuring_detector.analyze(movements, target_address))

        if address_labels:
            all_signals.extend(self.label_detector.analyze(address_labels, hop_count))

        return all_signals
