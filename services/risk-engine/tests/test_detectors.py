"""
Unit Tests for Initial AML Detectors Engine (F2-K2-C).
Uses tests/golden-datasets/graph-topologies.yaml to verify Rapid Pass-Through,
Fan-In/Fan-Out Structuring, and High-Risk Label Exposure detectors.
"""

import os
import sys
import unittest
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from detectors import (
    RapidPassThroughDetector,
    StructuringDetector,
    HighRiskLabelExposureDetector,
    DetectorEngine
)
from models import SeverityEnum

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
TOPOLOGY_DATASET_PATH = os.path.join(ROOT_DIR, "tests", "golden-datasets", "graph-topologies.yaml")


class TestInitialDetectors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(TOPOLOGY_DATASET_PATH, "r", encoding="utf-8") as f:
            cls.topologies = yaml.safe_load(f)["topologies"]

    def setUp(self):
        self.engine = DetectorEngine()

    def test_rapid_pass_through_detector(self):
        """Validates Rapid Pass-Through detector against golden graph topology."""
        topo = self.topologies["rapid_pass_through"]
        target = "0xB222222222222222222222222222222222222222"

        movements = [
            {
                "from_address": edge["source"],
                "to_address": edge["target"],
                "decimal_amount": float(edge.get("valueEth", 0))
            }
            for edge in topo["edges"]
        ]

        signals = self.engine.pass_through_detector.analyze(movements, target)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].code, "RAPID_PASS_THROUGH")
        self.assertEqual(signals[0].severity, SeverityEnum.HIGH)

    def test_fan_in_structuring_detector(self):
        """Validates Fan-In Structuring aggregation detector against golden graph topology."""
        topo = self.topologies["fan_in"]
        target = topo["collectorNode"]

        movements = [
            {
                "from_address": edge["source"],
                "to_address": edge["target"],
                "decimal_amount": float(edge.get("valueUsdt", 0))
            }
            for edge in topo["edges"]
        ]

        signals = self.engine.structuring_detector.analyze(movements, target)
        fan_in_signals = [s for s in signals if s.code == "FAN_IN_STRUCTURING"]
        self.assertEqual(len(fan_in_signals), 1)
        self.assertEqual(fan_in_signals[0].severity, SeverityEnum.HIGH)

    def test_fan_out_structuring_detector(self):
        """Validates Fan-Out Structuring dispersion detector against golden graph topology."""
        topo = self.topologies["fan_out"]
        target = topo["distributorNode"]

        movements = [
            {
                "from_address": edge["source"],
                "to_address": edge["target"],
                "decimal_amount": float(edge.get("valueEth", 0))
            }
            for edge in topo["edges"]
        ]

        signals = self.engine.structuring_detector.analyze(movements, target)
        fan_out_signals = [s for s in signals if s.code == "FAN_OUT_STRUCTURING"]
        self.assertEqual(len(fan_out_signals), 1)
        self.assertEqual(fan_out_signals[0].severity, SeverityEnum.HIGH)

    def test_high_risk_label_exposure_detector(self):
        """Validates High-Risk Label Exposure detector against golden label dataset."""
        topo = self.topologies["label_exposure"]
        labels = [topo["nodes"][0]["label"]]

        signals = self.engine.label_detector.analyze(labels, hop_count=1)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].code, "HIGH_RISK_LABEL_EXPOSURE")
        self.assertEqual(signals[0].severity, SeverityEnum.CRITICAL)

    def test_composite_detector_engine(self):
        """Validates DetectorEngine running all detectors concurrently for a target address."""
        target = "0x71C7656EC7ab88b098defB751B7401B5f6d8976F"
        movements = [
            {"from_address": "0x1111", "to_address": target, "decimal_amount": 10.0},
            {"from_address": "0x2222", "to_address": target, "decimal_amount": 10.0},
            {"from_address": "0x3333", "to_address": target, "decimal_amount": 10.0},
            {"from_address": target, "to_address": "0x4444", "decimal_amount": 28.0}
        ]
        labels = ["SANCTIONS", "OFAC"]

        signals = self.engine.run_all_detectors(target, movements=movements, address_labels=labels)
        self.assertGreaterEqual(len(signals), 2)
        codes = [s.code for s in signals]
        self.assertIn("HIGH_RISK_LABEL_EXPOSURE", codes)
        self.assertIn("FAN_IN_STRUCTURING", codes)


if __name__ == "__main__":
    unittest.main()
