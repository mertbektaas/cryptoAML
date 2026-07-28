"""
Community & Cluster Risk Scoring Engine (F3-K3-B).
Detects graph communities/clusters using Connected Components & Louvain partition algorithms.
Calculates Cluster Risk Density, High-Risk Node Ratio, and emits Cluster Exposure Signals.
"""

import logging
from typing import List, Dict, Any, Optional, Set
import networkx as nx

try:
    from .models import SignalModel, SeverityEnum
except ImportError:
    from models import SignalModel, SeverityEnum

logger = logging.getLogger("cluster_scoring")


class ClusterScoringEngine:
    """Detects graph communities and scores cluster-level AML risk density."""

    def build_graph(self, edges: List[Dict[str, Any]]) -> nx.Graph:
        """Constructs an undirected Graph for community detection."""
        G = nx.Graph()
        for edge in edges:
            src = str(edge.get("from") or edge.get("source")).lower()
            dst = str(edge.get("to") or edge.get("target")).lower()
            weight = float(edge.get("decimal_amount") or edge.get("valueEth") or edge.get("valueUsdt") or 1.0)
            G.add_edge(src, dst, weight=weight)
        return G

    def detect_communities(self, G: nx.Graph) -> List[Set[str]]:
        """
        Detects graph communities using Louvain algorithm or Connected Components fallback.
        """
        if len(G) == 0:
            return []

        try:
            communities = list(nx.community.louvain_communities(G, weight="weight"))
            return [set(c) for c in communities]
        except Exception as e:
            logger.info(f"Louvain partitioning fallback to connected components: {e}")
            components = list(nx.connected_components(G))
            return [set(c) for c in components]

    def find_target_community(self, target_address: str, communities: List[Set[str]]) -> Optional[Set[str]]:
        """Finds the community cluster containing target_address."""
        target = target_address.lower()
        for comm in communities:
            if target in comm:
                return comm
        return None

    def calculate_cluster_risk(
        self,
        cluster_nodes: Set[str],
        address_risk_scores: Optional[Dict[str, float]] = None,
        address_labels: Optional[Dict[str, List[str]]] = None
    ) -> Dict[str, Any]:
        """
        Calculates cluster risk density, max score, and high-risk ratio.
        """
        risk_scores = address_risk_scores or {}
        labels_map = address_labels or {}

        total_nodes = len(cluster_nodes)
        if total_nodes == 0:
            return {"cluster_risk_density": 0.0, "max_risk_score": 0.0, "high_risk_node_ratio": 0.0}

        high_risk_count = 0
        score_sum = 0.0
        max_score = 0.0

        for node in cluster_nodes:
            score = risk_scores.get(node, 0.0)
            labels = labels_map.get(node, [])
            is_sanctioned = any("SANCTION" in l.upper() or "OFAC" in l.upper() or "MIXER" in l.upper() for l in labels)

            if score >= 70.0 or is_sanctioned:
                high_risk_count += 1
                if is_sanctioned:
                    score = 100.0

            score_sum += score
            if score > max_score:
                max_score = score

        avg_score = score_sum / total_nodes
        high_risk_ratio = high_risk_count / total_nodes

        # Cluster risk density combines average score, max score weight, and high risk ratio
        cluster_risk_density = (avg_score * 0.40) + (max_score * 0.30) + (high_risk_ratio * 100.0 * 0.30)
        cluster_risk_density = min(100.0, max(0.0, cluster_risk_density))

        return {
            "cluster_size": total_nodes,
            "average_risk_score": round(avg_score, 2),
            "max_risk_score": round(max_score, 2),
            "high_risk_node_count": high_risk_count,
            "high_risk_node_ratio": round(high_risk_ratio, 2),
            "cluster_risk_density": round(cluster_risk_density, 2)
        }

    def analyze_target_cluster(
        self,
        target_address: str,
        edges: List[Dict[str, Any]],
        address_risk_scores: Optional[Dict[str, float]] = None,
        address_labels: Optional[Dict[str, List[str]]] = None,
        density_threshold: float = 50.0,
        high_risk_ratio_threshold: float = 0.25
    ) -> List[SignalModel]:
        """
        Detects communities, calculates risk density for target's cluster, and emits SignalModel list.
        """
        target = target_address.lower()
        G = self.build_graph(edges)

        if target not in G:
            return []

        communities = self.detect_communities(G)
        target_comm = self.find_target_community(target, communities)

        if not target_comm:
            return []

        metrics = self.calculate_cluster_risk(
            target_comm, address_risk_scores=address_risk_scores, address_labels=address_labels
        )

        signals: List[SignalModel] = []
        density = metrics["cluster_risk_density"]
        ratio = metrics["high_risk_node_ratio"]

        if density >= density_threshold or ratio >= high_risk_ratio_threshold:
            severity = SeverityEnum.CRITICAL if density >= 80.0 else SeverityEnum.HIGH
            signals.append(
                SignalModel(
                    code="CLUSTER_HIGH_RISK_EXPOSURE",
                    name="High-Risk Community Cluster Exposure",
                    category="CLUSTER_ANALYTICS",
                    severity=severity,
                    observed_value=metrics,
                    metadata={"density_threshold": density_threshold, "ratio_threshold": high_risk_ratio_threshold}
                )
            )

        if len(target_comm) >= 4 and density >= 40.0:
            signals.append(
                SignalModel(
                    code="CLUSTER_COMMUNITY_HUB",
                    name="High-Density Community Cluster Hub",
                    category="CLUSTER_ANALYTICS",
                    severity=SeverityEnum.MEDIUM,
                    observed_value={"cluster_size": len(target_comm), "cluster_risk_density": density},
                    metadata={"cluster_size": len(target_comm)}
                )
            )

        return signals
