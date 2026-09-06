"""FraudDNA Risk Network Repository.

Encapsulates database operations for RiskNetworkModel entities, member entity aggregation,
bounded transaction retrieval, and bounded network graph extraction.
"""

from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.graph.models import EdgeRelation, make_node_id
from app.models.domain import RiskNetworkModel, TransactionModel
from app.schemas.graph import GraphData, GraphEdge, GraphNode


class NetworkRepository:
    """Encapsulates persistent querying and graph generation for RiskNetworkModel."""

    def get_by_id(
        self, session: Session, network_id: str, load_transactions: bool = False
    ) -> RiskNetworkModel | None:
        """Retrieve network by cluster identifier with optional transaction loading."""
        stmt = select(RiskNetworkModel).where(RiskNetworkModel.id == network_id)
        if load_transactions:
            stmt = stmt.options(selectinload(RiskNetworkModel.transactions))
        return session.execute(stmt).scalar_one_or_none()

    def list_networks(
        self,
        session: Session,
        limit: int = 50,
        offset: int = 0,
        is_suspicious: bool | None = None,
        min_risk_score: float | None = None,
    ) -> tuple[list[RiskNetworkModel], int]:
        """Query bounded risk networks with filtering and pagination."""
        clamped_limit = max(1, min(limit, 200))
        stmt = select(RiskNetworkModel)
        count_stmt = select(func.count()).select_from(RiskNetworkModel)

        conditions: list[Any] = []
        if is_suspicious is not None:
            conditions.append(RiskNetworkModel.is_suspicious == is_suspicious)
        if min_risk_score is not None:
            conditions.append(RiskNetworkModel.risk_score >= min_risk_score)

        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        total_count = session.execute(count_stmt).scalar() or 0
        stmt = (
            stmt.order_by(desc(RiskNetworkModel.risk_score), RiskNetworkModel.id.asc())
            .limit(clamped_limit)
            .offset(offset)
        )
        items = list(session.execute(stmt).scalars().all())
        return items, total_count

    def get_network_member_entities(
        self, session: Session, network_id: str
    ) -> dict[str, list[str]]:
        """Retrieve distinct entity IDs belonging to the given risk network."""
        # Query distinct entities from member transactions
        cust_stmt = (
            select(func.distinct(TransactionModel.customer_id))
            .where(TransactionModel.network_id == network_id)
            .order_by(TransactionModel.customer_id.asc())
        )
        customers = [c for c in session.execute(cust_stmt).scalars().all() if c]

        dev_stmt = (
            select(func.distinct(TransactionModel.device_id))
            .where(
                TransactionModel.network_id == network_id,
                TransactionModel.device_id.is_not(None),
            )
            .order_by(TransactionModel.device_id.asc())
        )
        devices = [d for d in session.execute(dev_stmt).scalars().all() if d]

        ip_stmt = (
            select(func.distinct(TransactionModel.ip_id))
            .where(
                TransactionModel.network_id == network_id,
                TransactionModel.ip_id.is_not(None),
            )
            .order_by(TransactionModel.ip_id.asc())
        )
        ips = [i for i in session.execute(ip_stmt).scalars().all() if i]

        card_stmt = (
            select(func.distinct(TransactionModel.card_id))
            .where(
                TransactionModel.network_id == network_id,
                TransactionModel.card_id.is_not(None),
            )
            .order_by(TransactionModel.card_id.asc())
        )
        cards = [k for k in session.execute(card_stmt).scalars().all() if k]

        merch_stmt = (
            select(func.distinct(TransactionModel.merchant_id))
            .where(
                TransactionModel.network_id == network_id,
                TransactionModel.merchant_id.is_not(None),
            )
            .order_by(TransactionModel.merchant_id.asc())
        )
        merchants = [m for m in session.execute(merch_stmt).scalars().all() if m]

        return {
            "customers": customers,
            "devices": devices,
            "ips": ips,
            "cards": cards,
            "merchants": merchants,
        }

    def get_network_transactions(
        self,
        session: Session,
        network_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TransactionModel], int]:
        """Retrieve paginated member transactions belonging to a risk network."""
        clamped_limit = max(1, min(limit, 250))
        cond = TransactionModel.network_id == network_id

        count_stmt = select(func.count(TransactionModel.id)).where(cond)
        total_count = session.execute(count_stmt).scalar() or 0

        stmt = (
            select(TransactionModel)
            .where(cond)
            .order_by(desc(TransactionModel.timestamp), TransactionModel.id.asc())
            .limit(clamped_limit)
            .offset(offset)
        )
        txs = list(session.execute(stmt).scalars().all())
        return txs, total_count

    def get_network_graph(
        self,
        session: Session,
        network_id: str,
        max_nodes: int = 100,
        max_transactions: int = 100,
    ) -> GraphData:
        """Synthesize a bounded, deterministic GraphData representation for a risk network."""
        clamped_max_nodes = max(5, min(max_nodes, 250))
        clamped_max_tx = max(5, min(max_transactions, 250))

        net = self.get_by_id(session, network_id)
        net_score = float(net.risk_score) if net else 0.0

        nodes_map: dict[str, GraphNode] = {}
        edges_map: dict[str, GraphEdge] = {}

        def add_node(
            nid: str,
            raw_id: str,
            entity_category: str,
            label: str,
            risk_score: float = 0.0,
            amount: float | None = None,
            timestamp: str | None = None,
            metadata: dict[str, Any] | None = None,
        ) -> bool:
            if nid in nodes_map:
                return True
            if len(nodes_map) >= clamped_max_nodes:
                return False
            nodes_map[nid] = GraphNode(
                id=nid,
                raw_id=raw_id,
                entity_type=entity_category,
                label=label,
                risk_score=risk_score,
                amount=amount,
                timestamp=timestamp,
                metadata=metadata or {},
            )
            return True

        def add_edge(
            src: str,
            tgt: str,
            relation: str,
            weight: float = 1.0,
            metadata: dict[str, Any] | None = None,
        ) -> None:
            if src not in nodes_map or tgt not in nodes_map:
                return
            edge_id = f"{src}->{tgt}:{relation}"
            if edge_id not in edges_map:
                edges_map[edge_id] = GraphEdge(
                    id=edge_id,
                    source=src,
                    target=tgt,
                    relation=relation,
                    weight=weight,
                    metadata=metadata or {},
                )

        # Add network node
        net_nid = make_node_id("network", network_id)
        add_node(
            net_nid,
            network_id,
            "network",
            f"Network: {network_id}",
            risk_score=net_score,
            metadata={"primary_reason": net.primary_reason if net else ""},
        )

        # Load member transactions
        tx_stmt = (
            select(TransactionModel)
            .where(TransactionModel.network_id == network_id)
            .order_by(desc(TransactionModel.risk_score), desc(TransactionModel.timestamp))
            .limit(clamped_max_tx)
        )
        txs = list(session.execute(tx_stmt).scalars().all())

        for tx in txs:
            tx_nid = make_node_id("transaction", tx.id)
            if not add_node(
                tx_nid,
                tx.id,
                "transaction",
                f"Tx: {tx.id}",
                risk_score=tx.risk_score,
                amount=float(tx.amount),
                timestamp=tx.timestamp.isoformat(),
                metadata={"risk_tier": tx.risk_tier, "is_fraud": tx.is_fraud},
            ):
                break

            # Connect transaction to network
            add_edge(tx_nid, net_nid, "MEMBER_OF_NETWORK")

            # Connect transaction entities
            if tx.customer_id:
                c_nid = make_node_id("customer", tx.customer_id)
                if add_node(c_nid, tx.customer_id, "customer", f"Customer: {tx.customer_id}"):
                    add_edge(c_nid, tx_nid, EdgeRelation.EXECUTED.value)

            if tx.device_id:
                d_nid = make_node_id("device", tx.device_id)
                if add_node(d_nid, tx.device_id, "device", f"Device: {tx.device_id}"):
                    add_edge(tx_nid, d_nid, EdgeRelation.ON_DEVICE.value)

            if tx.ip_id:
                i_nid = make_node_id("ip", tx.ip_id)
                if add_node(i_nid, tx.ip_id, "ip", f"IP: {tx.ip_id}"):
                    add_edge(tx_nid, i_nid, EdgeRelation.FROM_IP.value)

            if tx.card_id:
                k_nid = make_node_id("card", tx.card_id)
                if add_node(k_nid, tx.card_id, "card", f"Card: {tx.card_id}"):
                    add_edge(tx_nid, k_nid, EdgeRelation.USING_CARD.value)

            if tx.merchant_id:
                m_nid = make_node_id("merchant", tx.merchant_id)
                if add_node(m_nid, tx.merchant_id, "merchant", f"Merchant: {tx.merchant_id}"):
                    add_edge(tx_nid, m_nid, EdgeRelation.AT_MERCHANT.value)

        # Deterministic sorting
        sorted_nodes = sorted(
            nodes_map.values(),
            key=lambda n: (-n.risk_score, n.id),
        )
        sorted_edges = sorted(
            edges_map.values(),
            key=lambda e: (e.source, e.target, e.relation, e.id),
        )

        return GraphData(
            nodes=sorted_nodes,
            edges=sorted_edges,
            total_nodes=len(sorted_nodes),
            total_edges=len(sorted_edges),
        )

    def create(self, session: Session, network: RiskNetworkModel) -> RiskNetworkModel:
        """Persist a new risk network."""
        session.add(network)
        session.flush()
        return network

    def upsert(self, session: Session, network: RiskNetworkModel) -> RiskNetworkModel:
        """Insert or update a risk network."""
        existing = self.get_by_id(session, network.id)
        if existing is None:
            return self.create(session, network)

        existing.network_name = network.network_name
        existing.status = network.status
        existing.risk_score = network.risk_score
        existing.is_suspicious = network.is_suspicious
        existing.primary_reason = network.primary_reason
        existing.transaction_count = network.transaction_count
        existing.customer_count = network.customer_count
        existing.device_count = network.device_count
        existing.card_count = network.card_count
        existing.ip_count = network.ip_count
        existing.merchant_count = network.merchant_count
        existing.total_amount = network.total_amount
        if network.first_seen is not None:
            existing.first_seen = network.first_seen
        if network.last_seen is not None:
            existing.last_seen = network.last_seen
        session.flush()
        return existing
