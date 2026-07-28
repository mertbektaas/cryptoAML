"""
Unit Tests for Graph Analytics Risk Engine (F3-K2-A).
Verifies PageRank, Betweenness Centrality, and Degree Connectivity metrics using graph-topologies.yaml.
"""

import os
import sys
import unittest
import yaml

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from graph_analytics import GraphAnalyticsEngine
from models import SeverityEnum

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
TOPOLOGY_DATASET_PATH = os.path.join(ROOT_DIR, "tests", "golden-datasets", "graph-topologies.yaml")


class TestGraphAnalyticsEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(TOPOLOGY_DATASET_PATH, "r", encoding="utf-8") as f:
            cls.topologies = yaml.safe_load(f)["topologies"]

    def setUp(self):
        self.engine = GraphAnalyticsEngine()

    def test_betweenness_centrality_on_pass_through(self):
        """Validates that intermediary transit node in pass-through has highest betweenness centrality."""
        topo = self.topologies["rapid_pass_through"]
        edges = topo["edges"]

        G = self.engine.build_graph(edges)
        bw_scores = self.engine.compute_betweenness(G)

        intermediary = "0xB222222222222222222222222222222222222222".lower()
        sender = "0xA111111111111111111111111111111111111111".lower()

        self.assertIn(intermediary, bw_scores)
        self.assertGreater(bw_scores[intermediary], bw_scores[sender])

    def test_pagerank_on_fan_in(self):
        """Validates that collector node in Fan-In topology absorbs highest PageRank score."""
        topo = self.topologies["fan_in"]
        edges = topo["edges"]

        G = self.engine.build_graph(edges)
        pr_scores = self.engine.compute_pagerank(G)

        collector = topo["collectorNode"].lower()
        self.assertIn(collector, pr_scores)
        self.assertGreater(pr_scores[collector], 0.30)

    def test_graph_risk_signals_emission(self):
        """Validates analyze_target_address signals for a bridging intermediary node."""
        topo = self.topologies["rapid_pass_through"]
        edges = topo["edges"]
        target = "0xB222222222222222222222222222222222222222"

        signals = self.engine.analyze_target_address(
            target_address=target,
            edges=edges,
            pagerank_threshold=0.20,
            betweenness_threshold=0.20,
            degree_threshold=2
        )

        codes = [s.code for s in signals]
        self.assertIn("BETWEENNESS_BRIDGING_HUB", codes)
        self.assertIn("HIGH_DEGREE_CONNECTIVITY", codes)


if __name__ == "__main__":
    unittest.main()
