"""FraudDNA Cluster Detection and Deterministic Risk Scoring Module.

Identifies connected fraud clusters and coordinated abuse networks across shared
devices, IPs, cards, and customer entities.
"""

import hashlib

import networkx as nx

from app.graph.builder import GraphBuilder
from app.graph.models import EntityType, parse_node_id
from app.schemas.cluster import ClusterDetail, ClusterRiskFactor
from app.schemas.graph import GraphData


class ClusterDetector:
    """Detects and scores coordinated fraud clusters from a FraudDNA graph."""

    def __init__(self, risk_threshold: float = 0.37) -> None:
        self.risk_threshold = risk_threshold

    def detect_clusters(self, full_graph: nx.Graph) -> list[ClusterDetail]:
        """Extract and score all connected components / abuse clusters in the graph."""
        if full_graph.number_of_nodes() == 0:
            return []

        # Construct bipartite clustering graph excluding high-degree merchant nodes
        # Bridge entities: customer, device, ip, card
        clustering_subgraph: nx.Graph = nx.Graph()
        for u, v in full_graph.edges():
            u_type, _ = parse_node_id(str(u))
            v_type, _ = parse_node_id(str(v))
            # Omit merchant edges from cluster connectivity to prevent world collapse
            if u_type == EntityType.MERCHANT.value or v_type == EntityType.MERCHANT.value:
                continue
            clustering_subgraph.add_edge(u, v)

        # Extract connected components
        raw_components = list(nx.connected_components(clustering_subgraph))

        # Also add any isolated transactions that might only have merchant edges
        for node, attrs in full_graph.nodes(data=True):
            if attrs.get("entity_type") == EntityType.TRANSACTION.value:
                if node not in clustering_subgraph:
                    raw_components.append({node})

        detected_clusters: list[ClusterDetail] = []

        for comp_nodes in raw_components:
            # Gather all transactions in this component
            tx_nodes = [
                n
                for n in comp_nodes
                if full_graph.nodes[n].get("entity_type") == EntityType.TRANSACTION.value
            ]
            if not tx_nodes:
                continue

            # Build full cluster node set including associated merchants of member transactions
            full_cluster_nodes = set(comp_nodes)
            for tx_node in tx_nodes:
                for nbr in full_graph.neighbors(tx_node):
                    full_cluster_nodes.add(nbr)

            cluster_subgraph = full_graph.subgraph(full_cluster_nodes)
            cluster_detail = self._build_cluster_detail(cluster_subgraph, tx_nodes)
            detected_clusters.append(cluster_detail)

        # Deterministically sort clusters by risk_score desc, then transaction_count desc, then cluster_id
        detected_clusters.sort(
            key=lambda c: (-c.cluster_risk_score, -c.transaction_count, c.cluster_id)
        )

        return detected_clusters

    def _build_cluster_detail(
        self,
        cluster_subgraph: nx.Graph,
        tx_nodes: list[str],
    ) -> ClusterDetail:
        """Score and construct structured ClusterDetail from a cluster subgraph."""
        # 1. Deterministic Cluster ID from sorted raw transaction IDs
        raw_tx_ids = sorted([str(cluster_subgraph.nodes[tx]["raw_id"]) for tx in tx_nodes])
        hash_input = ",".join(raw_tx_ids).encode("utf-8")
        cluster_id = f"cluster_{hashlib.sha256(hash_input).hexdigest()[:12]}"

        # 2. Count distinct entities
        cust_nodes: set[str] = set()
        dev_nodes: set[str] = set()
        ip_nodes: set[str] = set()
        card_nodes: set[str] = set()
        merch_nodes: set[str] = set()

        for node, attrs in cluster_subgraph.nodes(data=True):
            etype = attrs.get("entity_type")
            if etype == EntityType.CUSTOMER.value:
                cust_nodes.add(node)
            elif etype == EntityType.DEVICE.value:
                dev_nodes.add(node)
            elif etype == EntityType.IP.value:
                ip_nodes.add(node)
            elif etype == EntityType.CARD.value:
                card_nodes.add(node)
            elif etype == EntityType.MERCHANT.value:
                merch_nodes.add(node)

        n_tx = len(tx_nodes)
        n_cust = len(cust_nodes)
        n_dev = len(dev_nodes)
        n_ip = len(ip_nodes)
        n_card = len(card_nodes)
        n_merch = len(merch_nodes)

        # 3. Transaction amounts and risk scores
        amounts = [float(cluster_subgraph.nodes[tx].get("amount", 0.0)) for tx in tx_nodes]
        risk_scores = [float(cluster_subgraph.nodes[tx].get("risk_score", 0.0)) for tx in tx_nodes]

        total_amount = round(sum(amounts), 2)
        suspicious_tx_mask = [r >= self.risk_threshold for r in risk_scores]
        suspicious_count = sum(1 for is_susp in suspicious_tx_mask if is_susp)
        suspicious_amount = round(
            sum(amt for amt, is_susp in zip(amounts, suspicious_tx_mask, strict=False) if is_susp),
            2,
        )

        mean_tx_risk = sum(risk_scores) / n_tx if n_tx > 0 else 0.0
        max_tx_risk = max(risk_scores) if risk_scores else 0.0
        suspicious_fraction = suspicious_count / n_tx if n_tx > 0 else 0.0

        # 4. Calculate Risk Factors and Composite Score
        risk_factors: list[ClusterRiskFactor] = []
        score_components: float = 0.0

        # Baseline ML risk contribution
        score_components += (0.35 * mean_tx_risk) + (0.25 * max_tx_risk)

        # Factor A: Shared Device Collusion
        if n_cust >= 2 and n_dev > 0 and (n_cust / n_dev) >= 1.5:
            ratio = n_cust / n_dev
            weight = min(0.30, (ratio - 1.0) * 0.08)
            score_components += weight
            risk_factors.append(
                ClusterRiskFactor(
                    factor_type="SHARED_DEVICE_COLLUSION",
                    description=f"{n_cust} customer accounts sharing {n_dev} device(s) (ratio: {ratio:.1f}x).",
                    severity="HIGH" if ratio >= 3.0 else "MEDIUM",
                    weight=round(weight, 4),
                )
            )

        # Factor B: IP Proxy Farm / Burst Velocity
        if n_cust >= 2 and n_ip > 0 and (n_cust / n_ip) >= 1.5:
            ratio = n_cust / n_ip
            weight = min(0.25, (ratio - 1.0) * 0.06)
            score_components += weight
            risk_factors.append(
                ClusterRiskFactor(
                    factor_type="IP_PROXY_FARM",
                    description=f"{n_cust} customer accounts operating via {n_ip} shared IP address(es).",
                    severity="HIGH" if ratio >= 3.0 else "MEDIUM",
                    weight=round(weight, 4),
                )
            )

        # Factor C: Shared Payment Card Cycling
        if n_cust >= 2 and n_card > 0 and (n_cust / n_card) >= 1.5:
            ratio = n_cust / n_card
            weight = min(0.25, (ratio - 1.0) * 0.08)
            score_components += weight
            risk_factors.append(
                ClusterRiskFactor(
                    factor_type="CARD_CYCLING",
                    description=f"{n_cust} customer accounts sharing {n_card} payment instrument(s).",
                    severity="CRITICAL" if ratio >= 3.0 else "HIGH",
                    weight=round(weight, 4),
                )
            )

        # Factor D: Suspicious Volume Concentration
        if suspicious_fraction >= 0.50 and n_tx >= 2:
            weight = 0.20 * suspicious_fraction
            score_components += weight
            risk_factors.append(
                ClusterRiskFactor(
                    factor_type="ELEVATED_TRANSACTION_RISK",
                    description=f"{suspicious_count}/{n_tx} ({suspicious_fraction:.0%}) member transactions exceed individual ML threshold.",
                    severity="HIGH",
                    weight=round(weight, 4),
                )
            )

        final_cluster_score = round(min(max(score_components, 0.0), 1.0), 4)

        # Relationship-level coordination evidence required for suspicious cluster classification
        has_coordination_evidence = any(
            f.factor_type in {"SHARED_DEVICE_COLLUSION", "IP_PROXY_FARM", "CARD_CYCLING"}
            for f in risk_factors
        )
        is_suspicious = bool(
            final_cluster_score >= 0.50
            and has_coordination_evidence
            and n_tx >= 2
            and suspicious_count >= 1
        )

        # 5. Generate Primary Reason & Explanation Text
        primary_reason = self._generate_primary_reason(risk_factors, is_suspicious, n_tx, n_cust)
        explanation = self._generate_explanation(
            cluster_id,
            n_tx,
            n_cust,
            n_dev,
            n_ip,
            n_card,
            total_amount,
            suspicious_count,
            final_cluster_score,
            risk_factors,
        )

        if is_suspicious or len(cluster_subgraph) <= 1000:
            graph_data = GraphBuilder.subgraph_to_graph_data(cluster_subgraph)
        else:
            graph_data = GraphData(
                nodes=[],
                edges=[],
                total_nodes=len(cluster_subgraph),
                total_edges=cluster_subgraph.number_of_edges(),
            )
        all_node_ids = sorted(cluster_subgraph.nodes())

        return ClusterDetail(
            cluster_id=cluster_id,
            cluster_risk_score=final_cluster_score,
            is_suspicious=is_suspicious,
            transaction_count=n_tx,
            customer_count=n_cust,
            device_count=n_dev,
            ip_count=n_ip,
            card_count=n_card,
            merchant_count=n_merch,
            suspicious_transaction_count=suspicious_count,
            total_transaction_amount=total_amount,
            suspicious_transaction_amount=suspicious_amount,
            primary_reason=primary_reason,
            member_transaction_ids=raw_tx_ids,
            connected_entity_ids=all_node_ids,
            risk_factors=risk_factors,
            explanation=explanation,
            graph_data=graph_data,
            metadata={
                "mean_transaction_risk": round(mean_tx_risk, 4),
                "max_transaction_risk": round(max_tx_risk, 4),
                "suspicious_volume_ratio": round(suspicious_fraction, 4),
            },
        )

    def _generate_primary_reason(
        self,
        risk_factors: list[ClusterRiskFactor],
        is_suspicious: bool,
        n_tx: int,
        n_cust: int,
    ) -> str:
        """Derive a single concise summary reason for the cluster."""
        if not is_suspicious:
            return (
                f"Standard activity across {n_tx} transaction(s) with no coordinated abuse signals."
            )
        if risk_factors:
            # Pick highest severity factor
            severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            sorted_factors = sorted(risk_factors, key=lambda f: severity_order.get(f.severity, 4))
            return sorted_factors[0].description
        return (
            f"Elevated network risk detected across {n_cust} account(s) and {n_tx} transaction(s)."
        )

    def _generate_explanation(
        self,
        cluster_id: str,
        n_tx: int,
        n_cust: int,
        n_dev: int,
        n_ip: int,
        n_card: int,
        total_amount: float,
        suspicious_count: int,
        score: float,
        risk_factors: list[ClusterRiskFactor],
    ) -> str:
        """Synthesize a complete deterministic explanation for risk analysts."""
        lines: list[str] = [
            f"Cluster {cluster_id} contains {n_tx} connected transaction(s) totaling INR {total_amount:,.2f} "
            f"spanning {n_cust} customer(s), {n_dev} device(s), {n_ip} IP(s), and {n_card} payment card(s).",
            f"Overall Cluster Risk Score: {score:.2f} ({'SUSPICIOUS' if score >= 0.50 else 'NORMAL'}).",
        ]

        if risk_factors:
            lines.append("Key Relationship Risk Signals:")
            for f in risk_factors:
                lines.append(f" - [{f.severity}] {f.description}")
        else:
            lines.append("No multi-account entity sharing or velocity anomalies were discovered.")

        if suspicious_count > 0:
            lines.append(
                f"Contains {suspicious_count} transaction(s) flagged with elevated individual risk."
            )

        return "\n".join(lines)
