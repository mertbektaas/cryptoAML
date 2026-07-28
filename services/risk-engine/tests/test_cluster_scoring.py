"""
Unit Tests for Community & Cluster Risk Scoring Engine (F3-K2-B).
Verifies Louvain partition, cluster risk density calculation, and cluster exposure signals.
"""

import os
import sys
import unittest
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from cluster_scoring import ClusterScoringEngine
from models import SeverityEnum

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
TOPOLOGY_DATASET_PATH = os.path.join(ROOT_DIR, "tests", "golden-datasets", "graph-topologies.yaml")


class TestClusterScoringEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(TOPOLOGY_DATASET_PATH, "r", encoding="utf-8") as f:
            cls.topologies = yaml.safe_load(f)["topologies"]

    def setUp(self):
        self.engine = ClusterScoringEngine()

    def test_detect_communities(self):
        """Validates community partition detection on Fan-In topology."""
        topo = self.topologies["fan_in"]
        edges = topo["edges"]

        G = self.engine.build_graph(edges)
        communities = self.engine.detect_communities(G)

        self.assertGreater(len(communities), 0)
        target = topo["collectorNode"].lower()
        target_comm = self.engine.find_target_community(target, communities)
        self.assertIsNotNone(target_comm)
        self.assertIn(target, target_comm)

    def test_calculate_cluster_risk_density(self):
        """Validates cluster risk density calculation with high risk sanction node."""
        cluster_nodes = {"0xa1", "0xa2", "0xa3", "0xb_target"}
        address_risk_scores = {"0xa1": 80.0, "0xa2": 20.0, "0xa3": 10.0, "0xb_target": 95.0}
        address_labels = {"0xb_target": ["OFAC_SANCTIONED"]}

        metrics = self.engine.calculate_cluster_risk(
            cluster_nodes=cluster_nodes,
            address_risk_scores=address_risk_scores,
            address_labels=address_labels
        )

        self.assertEqual(metrics["cluster_size"], 4)
        self.assertEqual(metrics["max_risk_score"], 100.0)  # Sanctioned override
        self.assertGreater(metrics["high_risk_node_ratio"], 0.40)
        self.assertGreater(metrics["cluster_risk_density"], 50.0)

    def test_analyze_target_cluster_signals(self):
        """Validates emission of CLUSTER_HIGH_RISK_EXPOSURE signal for a high risk cluster member."""
        topo = self.topologies["label_exposure"]
        edges = topo["edges"]
        target = topo["nodes"][0]["id"]  # Sanctioned node

        labels_map = {target.lower(): ["SANCTIONS"]}
        scores_map = {target.lower(): 100.0}

        signals = self.engine.analyze_target_cluster(
            target_address=target,
            edges=edges,
            address_risk_scores=scores_map,
            address_labels=labels_map,
            density_threshold=30.0
        )

        codes = [s.code for s in signals]
        self.assertIn("CLUSTER_HIGH_RISK_EXPOSURE", codes)


if __name__ == "__main__":
    unittest.main()
