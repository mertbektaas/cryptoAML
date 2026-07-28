"""
Graph Analytics & Topological Risk Engine (F3-K2-A).
Calculates Risk-Weighted PageRank, Betweenness Centrality, and Degree Connectivity metrics using NetworkX.
Emits graph risk signals for Risk Engine evaluation.
"""

import logging
from typing import List, Dict, Any, Optional
import networkx as nx

try:
    from .models import SignalModel, SeverityEnum
except ImportError:
    from models import SignalModel, SeverityEnum

logger = logging.getLogger("graph_analytics")


class GraphAnalyticsEngine:
    """Calculates NetworkX topological risk metrics (PageRank, Betweenness, Degree)."""

    def build_graph(self, edges: List[Dict[str, Any]]) -> nx.DiGraph:
        """Constructs a directed NetworkX graph from edge list."""
        G = nx.DiGraph()
        for edge in edges:
            src = str(edge.get("from") or edge.get("source")).lower()
            dst = str(edge.get("to") or edge.get("target")).lower()
            weight = float(edge.get("decimal_amount") or edge.get("valueEth") or edge.get("valueUsdt") or 1.0)
            G.add_edge(src, dst, weight=weight)
        return G

    def compute_pagerank(
        self, G: nx.DiGraph, alpha: float = 0.85, max_iter: int = 100, tol: float = 1e-6
    ) -> Dict[str, float]:
        """
        Pure Python Power Iteration PageRank algorithm.
        Guarantees zero-dependency execution across all Python environments.
        """
        N = len(G)
        if N == 0:
            return {}

        nodes = list(G.nodes())
        pr = {node: 1.0 / N for node in nodes}

        # Calculate out-weight or out-degree
        out_weights = {}
        for u in nodes:
            total_w = sum(G[u][v].get("weight", 1.0) for v in G[u])
            out_weights[u] = total_w

        # In-neighbors dictionary for fast lookup
        in_neighbors = {u: list(G.predecessors(u)) for u in nodes}

        for _ in range(max_iter):
            prev_pr = pr.copy()
            dangle_sum = sum(prev_pr[u] for u in nodes if out_weights[u] == 0)
            diff = 0.0

            for u in nodes:
                rank_sum = sum(
                    prev_pr[v] * (G[v][u].get("weight", 1.0) / out_weights[v])
                    for v in in_neighbors[u]
                    if out_weights[v] > 0
                )
                pr[u] = (1.0 - alpha) / N + alpha * (rank_sum + dangle_sum / N)
                diff += abs(pr[u] - prev_pr[u])

            if diff < tol:
                break

        return pr

    def compute_betweenness(self, G: nx.DiGraph) -> Dict[str, float]:
        """Calculates Betweenness Centrality (bridging importance) for nodes."""
        if len(G) == 0:
            return {}
        try:
            return nx.betweenness_centrality(G, weight="weight", normalized=True)
        except Exception as e:
            logger.warning(f"Error computing Betweenness Centrality: {e}")
            return {node: 0.0 for node in G.nodes()}

    def analyze_target_address(
        self,
        target_address: str,
        edges: List[Dict[str, Any]],
        pagerank_threshold: float = 0.20,
        betweenness_threshold: float = 0.20,
        degree_threshold: int = 4
    ) -> List[SignalModel]:
        """
        Builds graph from edges, calculates metrics for target_address, and emits SignalModel list.
        """
        target = target_address.lower()
        G = self.build_graph(edges)

        if target not in G:
            return []

        signals: List[SignalModel] = []
        pr_scores = self.compute_pagerank(G)
        bw_scores = self.compute_betweenness(G)

        in_degree = G.in_degree(target)
        out_degree = G.out_degree(target)
        total_degree = in_degree + out_degree

        target_pr = pr_scores.get(target, 0.0)
        target_bw = bw_scores.get(target, 0.0)

        # 1. PageRank High Risk Signal
        if target_pr >= pagerank_threshold:
            signals.append(
                SignalModel(
                    code="PAGERANK_HIGH_RISK",
                    name="High Graph PageRank Exposure",
                    category="GRAPH_ANALYTICS",
                    severity=SeverityEnum.HIGH if target_pr < 0.50 else SeverityEnum.CRITICAL,
                    observed_value={"pagerank_score": round(target_pr, 4)},
                    metadata={"threshold": pagerank_threshold}
                )
            )

        # 2. Betweenness Centrality Bridging Signal
        if target_bw >= betweenness_threshold:
            signals.append(
                SignalModel(
                    code="BETWEENNESS_BRIDGING_HUB",
                    name="High Betweenness Bridging Hub",
                    category="GRAPH_ANALYTICS",
                    severity=SeverityEnum.HIGH,
                    observed_value={"betweenness_centrality": round(target_bw, 4)},
                    metadata={"threshold": betweenness_threshold}
                )
            )

        # 3. High Degree Connectivity Signal
        if total_degree >= degree_threshold:
            signals.append(
                SignalModel(
                    code="HIGH_DEGREE_CONNECTIVITY",
                    name="High Degree Connectivity Cluster",
                    category="GRAPH_ANALYTICS",
                    severity=SeverityEnum.MEDIUM,
                    observed_value={"in_degree": in_degree, "out_degree": out_degree, "total_degree": total_degree},
                    metadata={"threshold": degree_threshold}
                )
            )

        return signals
