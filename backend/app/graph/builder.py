"""FraudDNA Graph Builder Module.

Constructs an in-memory NetworkX relationship graph connecting Transactions,
Customers, Devices, IP addresses, Cards, and Merchants.
"""

import networkx as nx
import pandas as pd

from app.graph.models import EdgeRelation, EntityType, make_node_id
from app.schemas.graph import GraphData, GraphEdge, GraphNode


class GraphBuilder:
    """Deterministic builder for the FraudDNA entity relationship graph."""

    def __init__(self) -> None:
        self.graph: nx.Graph = nx.Graph()

    def build_from_dataframe(
        self,
        df: pd.DataFrame,
        risk_scores: dict[str, float] | None = None,
    ) -> nx.Graph:
        """Construct full NetworkX relationship graph from a transaction DataFrame."""
        self.graph.clear()
        if df.empty or "transaction_id" not in df.columns:
            return self.graph

        scores = risk_scores or {}

        # Ensure deterministic iteration by sorting by timestamp and transaction_id
        df_sorted = df.copy()
        if "timestamp" in df_sorted.columns:
            if not pd.api.types.is_datetime64_any_dtype(df_sorted["timestamp"]):
                df_sorted["timestamp"] = pd.to_datetime(df_sorted["timestamp"])
            df_sorted = df_sorted.sort_values(by=["timestamp", "transaction_id"]).reset_index(
                drop=True
            )
        else:
            df_sorted = df_sorted.sort_values(by="transaction_id").reset_index(drop=True)

        for _, row in df_sorted.iterrows():
            tx_raw_id = str(row["transaction_id"])
            cust_raw_id = str(row.get("customer_id", "unknown_cust"))
            dev_raw_id = str(row.get("device_id", "unknown_device"))
            ip_raw_id = str(row.get("ip_address", "unknown_ip"))
            card_raw_id = str(row.get("card_id", "unknown_card"))
            merch_raw_id = str(row.get("merchant_id", "unknown_merch"))

            amt = float(row.get("amount", 0.0))
            ts_str = str(row["timestamp"]) if "timestamp" in row else None
            mcat = str(row.get("merchant_category", "general"))
            pmethod = str(row.get("payment_method", "card"))
            city = str(row.get("city", "Unknown"))
            tx_risk = float(scores.get(tx_raw_id, 0.0))

            # 1. Create Namespaced Node IDs
            tx_node = make_node_id(EntityType.TRANSACTION, tx_raw_id)
            cust_node = make_node_id(EntityType.CUSTOMER, cust_raw_id)
            dev_node = make_node_id(EntityType.DEVICE, dev_raw_id)
            ip_node = make_node_id(EntityType.IP, ip_raw_id)
            card_node = make_node_id(EntityType.CARD, card_raw_id)
            merch_node = make_node_id(EntityType.MERCHANT, merch_raw_id)

            # 2. Add Transaction Node
            self.graph.add_node(
                tx_node,
                raw_id=tx_raw_id,
                entity_type=EntityType.TRANSACTION.value,
                label=f"TX: {tx_raw_id}",
                risk_score=tx_risk,
                amount=amt,
                timestamp=ts_str,
                metadata={
                    "merchant_category": mcat,
                    "payment_method": pmethod,
                    "city": city,
                },
            )

            # 3. Add Entity Nodes (if not already present)
            if cust_node not in self.graph:
                self.graph.add_node(
                    cust_node,
                    raw_id=cust_raw_id,
                    entity_type=EntityType.CUSTOMER.value,
                    label=f"Customer: {cust_raw_id}",
                    risk_score=0.0,
                    metadata={"city": city},
                )

            if dev_node not in self.graph:
                self.graph.add_node(
                    dev_node,
                    raw_id=dev_raw_id,
                    entity_type=EntityType.DEVICE.value,
                    label=f"Device: {dev_raw_id}",
                    risk_score=0.0,
                    metadata={},
                )

            if ip_node not in self.graph:
                self.graph.add_node(
                    ip_node,
                    raw_id=ip_raw_id,
                    entity_type=EntityType.IP.value,
                    label=f"IP: {ip_raw_id}",
                    risk_score=0.0,
                    metadata={},
                )

            if card_node not in self.graph:
                self.graph.add_node(
                    card_node,
                    raw_id=card_raw_id,
                    entity_type=EntityType.CARD.value,
                    label=f"Card: {card_raw_id}",
                    risk_score=0.0,
                    metadata={"payment_method": pmethod},
                )

            if merch_node not in self.graph:
                self.graph.add_node(
                    merch_node,
                    raw_id=merch_raw_id,
                    entity_type=EntityType.MERCHANT.value,
                    label=f"Merchant: {merch_raw_id}",
                    risk_score=0.0,
                    metadata={"category": mcat},
                )

            # 4. Add Edges connecting Transaction to Entities
            self._add_edge(cust_node, tx_node, EdgeRelation.EXECUTED, amt, ts_str)
            self._add_edge(tx_node, dev_node, EdgeRelation.ON_DEVICE, amt, ts_str)
            self._add_edge(tx_node, ip_node, EdgeRelation.FROM_IP, amt, ts_str)
            self._add_edge(tx_node, card_node, EdgeRelation.USING_CARD, amt, ts_str)
            self._add_edge(tx_node, merch_node, EdgeRelation.AT_MERCHANT, amt, ts_str)

        # Propagate max and mean risk scores from transactions to adjacent entity nodes
        self._update_entity_risk_aggregates()

        return self.graph

    def _add_edge(
        self,
        u: str,
        v: str,
        relation: EdgeRelation,
        amount: float,
        timestamp: str | None,
    ) -> None:
        """Add or update an edge between two nodes with semantic attributes."""
        edge_id = f"{u}->{v}:{relation.value}"
        self.graph.add_edge(
            u,
            v,
            id=edge_id,
            relation=relation.value,
            weight=1.0,
            amount=amount,
            timestamp=timestamp,
            metadata={},
        )

    def _update_entity_risk_aggregates(self) -> None:
        """Compute aggregated risk scores for entity nodes based on connected transactions."""
        for node, attrs in self.graph.nodes(data=True):
            if attrs.get("entity_type") != EntityType.TRANSACTION.value:
                tx_neighbors = [
                    self.graph.nodes[nbr]
                    for nbr in self.graph.neighbors(node)
                    if self.graph.nodes[nbr].get("entity_type") == EntityType.TRANSACTION.value
                ]
                if tx_neighbors:
                    tx_risks = [nbr.get("risk_score", 0.0) for nbr in tx_neighbors]
                    attrs["max_risk_score"] = float(max(tx_risks))
                    attrs["mean_risk_score"] = float(sum(tx_risks) / len(tx_risks))
                    attrs["risk_score"] = attrs["max_risk_score"]
                    attrs["connected_transaction_count"] = len(tx_neighbors)
                else:
                    attrs["risk_score"] = 0.0
                    attrs["connected_transaction_count"] = 0

    @staticmethod
    def subgraph_to_graph_data(subgraph: nx.Graph) -> GraphData:
        """Convert a NetworkX subgraph into structured GraphData for React Flow consumption."""
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []

        sorted_nodes = sorted(subgraph.nodes(data=True), key=lambda x: str(x[0]))
        for node_id, attrs in sorted_nodes:
            nodes.append(
                GraphNode(
                    id=str(node_id),
                    raw_id=str(attrs.get("raw_id", node_id)),
                    entity_type=str(attrs.get("entity_type", "unknown")),
                    label=str(attrs.get("label", node_id)),
                    risk_score=float(attrs.get("risk_score", 0.0)),
                    amount=attrs.get("amount"),
                    timestamp=attrs.get("timestamp"),
                    metadata=attrs.get("metadata", {}),
                )
            )

        sorted_edges = sorted(
            subgraph.edges(data=True),
            key=lambda e: (str(e[0]), str(e[1]), str(e[2].get("relation", ""))),
        )
        for u, v, attrs in sorted_edges:
            edge_id = str(attrs.get("id", f"{u}->{v}"))
            edges.append(
                GraphEdge(
                    id=edge_id,
                    source=str(u),
                    target=str(v),
                    relation=str(attrs.get("relation", "CONNECTED")),
                    weight=float(attrs.get("weight", 1.0)),
                    metadata=attrs.get("metadata", {}),
                )
            )

        return GraphData(
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges),
        )
