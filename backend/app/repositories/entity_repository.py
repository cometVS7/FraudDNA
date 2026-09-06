"""FraudDNA Entity Repository.

Provides persistent database-backed access for core financial entities:
Customer, Account, Card, Device, IPAddress, Merchant, and RiskNetwork.
Implements bounded transaction querying, point-in-time behavioral velocity metrics,
and bounded graph neighborhood traversals.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.core.errors import ValidationDomainError
from app.graph.models import EdgeRelation, make_node_id
from app.models.domain import (
    AccountModel,
    CardModel,
    CustomerModel,
    DeviceModel,
    IPAddressModel,
    MerchantModel,
    RiskNetworkModel,
    TransactionModel,
)
from app.schemas.graph import GraphData, GraphEdge, GraphNode


class EntityRepository:
    """Encapsulates entity queries and bounded graph neighborhood retrieval."""

    # --------------------------------------------------------------------------
    # 1. Direct Entity Retrieval
    # --------------------------------------------------------------------------

    def get_customer(self, session: Session, customer_id: str) -> CustomerModel | None:
        """Retrieve customer entity by ID."""
        stmt = select(CustomerModel).where(CustomerModel.id == customer_id)
        return session.execute(stmt).scalar_one_or_none()

    def get_account(self, session: Session, account_id: str) -> AccountModel | None:
        """Retrieve account entity by ID."""
        stmt = select(AccountModel).where(AccountModel.id == account_id)
        return session.execute(stmt).scalar_one_or_none()

    def get_card(self, session: Session, card_id: str) -> CardModel | None:
        """Retrieve card payment instrument by ID."""
        stmt = select(CardModel).where(CardModel.id == card_id)
        return session.execute(stmt).scalar_one_or_none()

    def get_device(self, session: Session, device_id: str) -> DeviceModel | None:
        """Retrieve device entity by ID."""
        stmt = select(DeviceModel).where(DeviceModel.id == device_id)
        return session.execute(stmt).scalar_one_or_none()

    def get_ip_address(self, session: Session, ip_address: str) -> IPAddressModel | None:
        """Retrieve IP address entity by ID."""
        stmt = select(IPAddressModel).where(IPAddressModel.id == ip_address)
        return session.execute(stmt).scalar_one_or_none()

    def get_merchant(self, session: Session, merchant_id: str) -> MerchantModel | None:
        """Retrieve merchant entity by ID."""
        stmt = select(MerchantModel).where(MerchantModel.id == merchant_id)
        return session.execute(stmt).scalar_one_or_none()

    def get_risk_network(self, session: Session, network_id: str) -> RiskNetworkModel | None:
        """Retrieve risk network entity by ID."""
        stmt = select(RiskNetworkModel).where(RiskNetworkModel.id == network_id)
        return session.execute(stmt).scalar_one_or_none()

    def get_customer_accounts(self, session: Session, customer_id: str) -> list[AccountModel]:
        """Retrieve accounts owned by a customer."""
        stmt = select(AccountModel).where(AccountModel.customer_id == customer_id)
        return list(session.execute(stmt).scalars().all())

    # --------------------------------------------------------------------------
    # 2. Bounded Entity Transactions & Metrics
    # --------------------------------------------------------------------------

    def _get_entity_tx_filter(self, entity_type: str, entity_id: str) -> Any:
        """Construct SQLAlchemy filter condition matching transaction foreign keys."""
        etype = entity_type.lower()
        if etype == "customer":
            return TransactionModel.customer_id == entity_id
        elif etype == "account":
            return TransactionModel.account_id == entity_id
        elif etype == "card":
            return TransactionModel.card_id == entity_id
        elif etype == "device":
            return TransactionModel.device_id == entity_id
        elif etype == "ip":
            return TransactionModel.ip_id == entity_id
        elif etype == "merchant":
            return TransactionModel.merchant_id == entity_id
        elif etype == "network":
            return TransactionModel.network_id == entity_id
        elif etype == "transaction":
            return TransactionModel.id == entity_id
        else:
            raise ValidationDomainError(
                f"Unsupported entity type for transaction filtering: '{entity_type}'"
            )

    def get_entity_transactions(
        self,
        session: Session,
        entity_type: str,
        entity_id: str,
        limit: int = 50,
        offset: int = 0,
        as_of: datetime | None = None,
    ) -> tuple[list[TransactionModel], int]:
        """Retrieve bounded, paginated transactions for an entity with optional point-in-time filtering."""
        clamped_limit = max(1, min(limit, 250))
        cond = self._get_entity_tx_filter(entity_type, entity_id)

        conditions = [cond]
        if as_of is not None:
            conditions.append(TransactionModel.timestamp <= as_of)

        count_stmt = select(func.count(TransactionModel.id)).where(*conditions)
        total_count = session.execute(count_stmt).scalar() or 0

        stmt = (
            select(TransactionModel)
            .where(*conditions)
            .order_by(desc(TransactionModel.timestamp), TransactionModel.id.asc())
            .limit(clamped_limit)
            .offset(offset)
        )
        transactions = list(session.execute(stmt).scalars().all())
        return transactions, total_count

    def get_behavioral_metrics(
        self,
        session: Session,
        entity_type: str,
        entity_id: str,
        as_of: datetime | None = None,
    ) -> dict[str, Any]:
        """Compute point-in-time deterministic behavioral indicators."""
        cond = self._get_entity_tx_filter(entity_type, entity_id)

        if as_of is None:
            latest_tx_stmt = select(func.max(TransactionModel.timestamp)).where(cond)
            latest_ts = session.execute(latest_tx_stmt).scalar()
            ref_time = latest_ts if latest_ts is not None else datetime.now(UTC)
        else:
            ref_time = as_of

        t_5m = ref_time - timedelta(minutes=5)
        t_1h = ref_time - timedelta(hours=1)
        t_24h = ref_time - timedelta(hours=24)

        # Query all transactions within last 24 hours up to ref_time
        stmt_24h = (
            select(TransactionModel)
            .where(
                cond,
                TransactionModel.timestamp <= ref_time,
                TransactionModel.timestamp >= t_24h,
            )
            .order_by(desc(TransactionModel.timestamp))
        )
        recent_24h_txs = list(session.execute(stmt_24h).scalars().all())

        tx_count_5m = 0
        tx_count_1h = 0
        tx_count_24h = len(recent_24h_txs)
        amount_1h = Decimal("0.00")
        amount_24h = Decimal("0.00")
        merchants_24h: set[str] = set()
        devices_24h: set[str] = set()
        ips_24h: set[str] = set()

        for tx in recent_24h_txs:
            amount_24h += tx.amount
            if tx.merchant_id:
                merchants_24h.add(tx.merchant_id)
            if tx.device_id:
                devices_24h.add(tx.device_id)
            if tx.ip_id:
                ips_24h.add(tx.ip_id)

            if tx.timestamp >= t_1h:
                tx_count_1h += 1
                amount_1h += tx.amount
            if tx.timestamp >= t_5m:
                tx_count_5m += 1

        # Cross-customer sharing count
        cross_sharing_count = self._get_cross_customer_sharing_count(
            session=session,
            entity_type=entity_type,
            entity_id=entity_id,
            ref_time=ref_time,
        )

        return {
            "as_of": ref_time,
            "tx_count_5m": tx_count_5m,
            "tx_count_1h": tx_count_1h,
            "tx_count_24h": tx_count_24h,
            "amount_1h": float(amount_1h),
            "amount_24h": float(amount_24h),
            "unique_merchants_24h": len(merchants_24h),
            "unique_devices_24h": len(devices_24h),
            "unique_ips_24h": len(ips_24h),
            "cross_customer_sharing_count": cross_sharing_count,
        }

    def _get_cross_customer_sharing_count(
        self,
        session: Session,
        entity_type: str,
        entity_id: str,
        ref_time: datetime,
    ) -> int:
        """Compute the count of other distinct customers sharing connected infrastructure."""
        etype = entity_type.lower()
        if etype in ("device", "card", "ip"):
            col = (
                TransactionModel.device_id
                if etype == "device"
                else (TransactionModel.card_id if etype == "card" else TransactionModel.ip_id)
            )
            cust_stmt = select(func.count(func.distinct(TransactionModel.customer_id))).where(
                col == entity_id, TransactionModel.timestamp <= ref_time
            )
            total_custs = session.execute(cust_stmt).scalar() or 0
            return max(0, total_custs - 1)
        elif etype == "customer":
            # Distinct devices used by customer up to ref_time
            dev_stmt = select(func.distinct(TransactionModel.device_id)).where(
                TransactionModel.customer_id == entity_id,
                TransactionModel.device_id.is_not(None),
                TransactionModel.timestamp <= ref_time,
            )
            device_ids = [d for d in session.execute(dev_stmt).scalars().all() if d]
            if not device_ids:
                return 0

            # Distinct other customers using any of these devices
            shared_cust_stmt = select(
                func.count(func.distinct(TransactionModel.customer_id))
            ).where(
                TransactionModel.device_id.in_(device_ids),
                TransactionModel.customer_id != entity_id,
                TransactionModel.timestamp <= ref_time,
            )
            return session.execute(shared_cust_stmt).scalar() or 0
        return 0

    def get_entity_risk_signals(
        self,
        session: Session,
        entity_type: str,
        entity_id: str,
        as_of: datetime | None = None,
    ) -> dict[str, Any]:
        """Aggregate deterministic risk indicators from transactions and risk networks."""
        cond = self._get_entity_tx_filter(entity_type, entity_id)
        conditions = [cond]
        if as_of is not None:
            conditions.append(TransactionModel.timestamp <= as_of)

        tx_stmt = (
            select(
                TransactionModel.id,
                TransactionModel.amount,
                TransactionModel.risk_score,
                TransactionModel.risk_tier,
                TransactionModel.network_id,
                TransactionModel.timestamp,
            )
            .where(*conditions)
            .order_by(desc(TransactionModel.risk_score), desc(TransactionModel.timestamp))
        )
        tx_rows = list(session.execute(tx_stmt).all())

        total_tx_count = len(tx_rows)
        total_tx_amount = sum(float(r[1]) for r in tx_rows)
        max_tx_risk = float(tx_rows[0][2]) if tx_rows else 0.0

        top3 = [float(r[2]) for r in tx_rows[:3]]
        avg_top3_tx_risk = float(sum(top3) / len(top3)) if top3 else 0.0

        # Network membership
        network_ids = list({r[4] for r in tx_rows if r[4] is not None})
        associated_networks: list[RiskNetworkModel] = []
        network_exposure = 0.0
        if network_ids:
            net_stmt = select(RiskNetworkModel).where(RiskNetworkModel.id.in_(network_ids))
            associated_networks = list(session.execute(net_stmt).scalars().all())
            has_suspicious_network = any(n.is_suspicious for n in associated_networks)
            if has_suspicious_network:
                network_exposure = 1.0
            elif associated_networks:
                network_exposure = max(float(n.risk_score) for n in associated_networks)

        # Cross-customer sharing anomaly
        ref_time = as_of or (tx_rows[0][5] if tx_rows else datetime.now(UTC))
        sharing_count = self._get_cross_customer_sharing_count(
            session=session,
            entity_type=entity_type,
            entity_id=entity_id,
            ref_time=ref_time,
        )
        sharing_anomaly = min(1.0, float(sharing_count) * 0.5)

        return {
            "total_tx_count": total_tx_count,
            "total_tx_amount": round(total_tx_amount, 2),
            "max_tx_risk": round(max_tx_risk, 4),
            "avg_top3_tx_risk": round(avg_top3_tx_risk, 4),
            "network_exposure": round(network_exposure, 4),
            "sharing_anomaly": round(sharing_anomaly, 4),
            "associated_networks": associated_networks,
            "cross_customer_sharing_count": sharing_count,
        }

    # --------------------------------------------------------------------------
    # 3. Direct Relationships
    # --------------------------------------------------------------------------

    def get_direct_relationships(
        self,
        session: Session,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Retrieve direct typed semantic relationships connected to an entity."""
        etype = entity_type.lower()
        relationships: list[dict[str, Any]] = []
        clamped_limit = max(1, min(limit, 200))

        if etype == "customer":
            # 1. Accounts owned (OWNS)
            accounts = self.get_customer_accounts(session, entity_id)
            for acc in accounts:
                relationships.append(
                    {
                        "source_id": make_node_id("customer", entity_id),
                        "target_id": make_node_id("account", acc.id),
                        "target_raw_id": acc.id,
                        "target_type": "account",
                        "relationship_type": EdgeRelation.EXECUTED.value if False else "OWNS",
                        "target_label": f"Account: {acc.id}",
                        "target_risk_score": acc.risk_score,
                        "metadata": {"account_type": acc.account_type, "status": acc.status},
                    }
                )

            # 2. Associated Devices, IPs, Cards, Merchants via transactions
            tx_stmt = (
                select(TransactionModel)
                .where(TransactionModel.customer_id == entity_id)
                .order_by(desc(TransactionModel.timestamp))
                .limit(clamped_limit)
            )
            txs = list(session.execute(tx_stmt).scalars().all())

            seen_targets: set[str] = set()
            for tx in txs:
                if tx.device_id and f"device:{tx.device_id}" not in seen_targets:
                    seen_targets.add(f"device:{tx.device_id}")
                    relationships.append(
                        {
                            "source_id": make_node_id("customer", entity_id),
                            "target_id": make_node_id("device", tx.device_id),
                            "target_raw_id": tx.device_id,
                            "target_type": "device",
                            "relationship_type": EdgeRelation.ON_DEVICE.value,
                            "target_label": f"Device: {tx.device_id}",
                            "target_risk_score": 0.0,
                            "metadata": {},
                        }
                    )
                if tx.ip_id and f"ip:{tx.ip_id}" not in seen_targets:
                    seen_targets.add(f"ip:{tx.ip_id}")
                    relationships.append(
                        {
                            "source_id": make_node_id("customer", entity_id),
                            "target_id": make_node_id("ip", tx.ip_id),
                            "target_raw_id": tx.ip_id,
                            "target_type": "ip",
                            "relationship_type": EdgeRelation.FROM_IP.value,
                            "target_label": f"IP: {tx.ip_id}",
                            "target_risk_score": 0.0,
                            "metadata": {},
                        }
                    )
                if tx.card_id and f"card:{tx.card_id}" not in seen_targets:
                    seen_targets.add(f"card:{tx.card_id}")
                    relationships.append(
                        {
                            "source_id": make_node_id("customer", entity_id),
                            "target_id": make_node_id("card", tx.card_id),
                            "target_raw_id": tx.card_id,
                            "target_type": "card",
                            "relationship_type": EdgeRelation.USING_CARD.value,
                            "target_label": f"Card: {tx.card_id}",
                            "target_risk_score": 0.0,
                            "metadata": {},
                        }
                    )
                if tx.merchant_id and f"merchant:{tx.merchant_id}" not in seen_targets:
                    seen_targets.add(f"merchant:{tx.merchant_id}")
                    relationships.append(
                        {
                            "source_id": make_node_id("customer", entity_id),
                            "target_id": make_node_id("merchant", tx.merchant_id),
                            "target_raw_id": tx.merchant_id,
                            "target_type": "merchant",
                            "relationship_type": EdgeRelation.AT_MERCHANT.value,
                            "target_label": f"Merchant: {tx.merchant_id}",
                            "target_risk_score": 0.0,
                            "metadata": {},
                        }
                    )
                if tx.network_id and f"network:{tx.network_id}" not in seen_targets:
                    seen_targets.add(f"network:{tx.network_id}")
                    relationships.append(
                        {
                            "source_id": make_node_id("customer", entity_id),
                            "target_id": make_node_id("network", tx.network_id),
                            "target_raw_id": tx.network_id,
                            "target_type": "network",
                            "relationship_type": "MEMBER_OF_NETWORK",
                            "target_label": f"Network: {tx.network_id}",
                            "target_risk_score": 0.0,
                            "metadata": {},
                        }
                    )

            # 3. Cross-customer sharing relationships (collusion edges)
            shared_devs = [
                r["target_raw_id"] for r in relationships if r["target_type"] == "device"
            ]
            if shared_devs:
                collusion_stmt = (
                    select(
                        TransactionModel.customer_id,
                        TransactionModel.device_id,
                    )
                    .where(
                        TransactionModel.device_id.in_(shared_devs),
                        TransactionModel.customer_id != entity_id,
                    )
                    .distinct()
                    .limit(20)
                )
                for other_cust_id, dev_id in session.execute(collusion_stmt).all():
                    rel_id = f"customer:{other_cust_id}"
                    if rel_id not in seen_targets:
                        seen_targets.add(rel_id)
                        relationships.append(
                            {
                                "source_id": make_node_id("customer", entity_id),
                                "target_id": rel_id,
                                "target_raw_id": other_cust_id,
                                "target_type": "customer",
                                "relationship_type": "SHARES_DEVICE",
                                "target_label": f"Customer: {other_cust_id}",
                                "target_risk_score": 0.0,
                                "metadata": {"via_device": dev_id},
                            }
                        )

        elif etype in ("device", "ip", "card", "merchant"):
            cond = self._get_entity_tx_filter(etype, entity_id)
            tx_stmt = (
                select(TransactionModel)
                .where(cond)
                .order_by(desc(TransactionModel.timestamp))
                .limit(clamped_limit)
            )
            txs = list(session.execute(tx_stmt).scalars().all())
            seen_custs: set[str] = set()

            rel_type = (
                EdgeRelation.ON_DEVICE.value
                if etype == "device"
                else (
                    EdgeRelation.FROM_IP.value
                    if etype == "ip"
                    else (
                        EdgeRelation.USING_CARD.value
                        if etype == "card"
                        else EdgeRelation.AT_MERCHANT.value
                    )
                )
            )

            for tx in txs:
                if tx.customer_id and tx.customer_id not in seen_custs:
                    seen_custs.add(tx.customer_id)
                    relationships.append(
                        {
                            "source_id": make_node_id(etype, entity_id),
                            "target_id": make_node_id("customer", tx.customer_id),
                            "target_raw_id": tx.customer_id,
                            "target_type": "customer",
                            "relationship_type": rel_type,
                            "target_label": f"Customer: {tx.customer_id}",
                            "target_risk_score": 0.0,
                            "metadata": {},
                        }
                    )
                if tx.network_id and f"network:{tx.network_id}" not in seen_custs:
                    seen_custs.add(f"network:{tx.network_id}")
                    relationships.append(
                        {
                            "source_id": make_node_id(etype, entity_id),
                            "target_id": make_node_id("network", tx.network_id),
                            "target_raw_id": tx.network_id,
                            "target_type": "network",
                            "relationship_type": "MEMBER_OF_NETWORK",
                            "target_label": f"Network: {tx.network_id}",
                            "target_risk_score": 0.0,
                            "metadata": {},
                        }
                    )

        return relationships[:clamped_limit]

    # --------------------------------------------------------------------------
    # 4. Bounded Neighborhood Subgraph Retrieval (React Flow GraphData)
    # --------------------------------------------------------------------------

    def get_bounded_neighborhood(
        self,
        session: Session,
        entity_type: str,
        entity_id: str,
        depth: int = 1,
        max_nodes: int = 100,
        max_transactions: int = 100,
    ) -> GraphData:
        """Construct a bounded, deterministic GraphData representation directly from PostgreSQL."""
        if depth < 1 or depth > 3:
            raise ValidationDomainError(
                f"Neighborhood traversal depth must be between 1 and 3. Requested: {depth}",
                details={"depth": depth},
            )

        if max_nodes < 5 or max_nodes > 250:
            raise ValidationDomainError(
                f"max_nodes must be between 5 and 250. Requested: {max_nodes}",
                details={"max_nodes": max_nodes},
            )

        if max_transactions < 5 or max_transactions > 250:
            raise ValidationDomainError(
                f"max_transactions must be between 5 and 250. Requested: {max_transactions}",
                details={"max_transactions": max_transactions},
            )

        clamped_max_nodes = max_nodes
        clamped_max_tx = max_transactions

        nodes_map: dict[str, GraphNode] = {}
        edges_map: dict[str, GraphEdge] = {}
        etype = entity_type.lower()

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

        # 1. Add root node
        root_node_id = make_node_id(etype, entity_id)
        root_label = f"{etype.capitalize()}: {entity_id}"
        add_node(root_node_id, entity_id, etype, root_label)

        # 2. Hop 1: Load transactions connecting to root
        cond = self._get_entity_tx_filter(etype, entity_id)
        tx_stmt = (
            select(TransactionModel)
            .where(cond)
            .order_by(desc(TransactionModel.timestamp), TransactionModel.id.asc())
            .limit(clamped_max_tx)
        )
        hop1_txs = list(session.execute(tx_stmt).scalars().all())

        for tx in hop1_txs:
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

            # Connect root to transaction
            if etype == "customer":
                add_edge(root_node_id, tx_nid, EdgeRelation.EXECUTED.value)
            elif etype == "device":
                add_edge(tx_nid, root_node_id, EdgeRelation.ON_DEVICE.value)
            elif etype == "ip":
                add_edge(tx_nid, root_node_id, EdgeRelation.FROM_IP.value)
            elif etype == "card":
                add_edge(tx_nid, root_node_id, EdgeRelation.USING_CARD.value)
            elif etype == "merchant":
                add_edge(tx_nid, root_node_id, EdgeRelation.AT_MERCHANT.value)
            elif etype == "account":
                add_edge(tx_nid, root_node_id, "DEBITS")
            elif etype == "network":
                add_edge(tx_nid, root_node_id, "MEMBER_OF_NETWORK")
            elif etype == "transaction":
                pass

            # If depth == 1 and root is transaction, expand transaction entities
            if etype == "transaction":
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
                if tx.network_id:
                    n_nid = make_node_id("network", tx.network_id)
                    if add_node(n_nid, tx.network_id, "network", f"Network: {tx.network_id}"):
                        add_edge(tx_nid, n_nid, "MEMBER_OF_NETWORK")

        # Customer accounts if customer root
        if etype == "customer":
            accounts = self.get_customer_accounts(session, entity_id)
            for acc in accounts:
                acc_nid = make_node_id("account", acc.id)
                if add_node(
                    acc_nid,
                    acc.id,
                    "account",
                    f"Account: {acc.id}",
                    risk_score=acc.risk_score,
                ):
                    add_edge(root_node_id, acc_nid, "OWNS")

        # 3. Hop 2 expansion (if depth == 2)
        if depth == 2:
            # From all hop1 transactions, connect their entities
            for tx in hop1_txs:
                tx_nid = make_node_id("transaction", tx.id)
                if tx_nid not in nodes_map:
                    continue

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

                if tx.network_id:
                    n_nid = make_node_id("network", tx.network_id)
                    if add_node(n_nid, tx.network_id, "network", f"Network: {tx.network_id}"):
                        add_edge(tx_nid, n_nid, "MEMBER_OF_NETWORK")

            # Shared infrastructure collusion edges (Customer <-> Customer)
            customer_nids = [n.raw_id for n in nodes_map.values() if n.entity_type == "customer"]
            device_nids = [n.raw_id for n in nodes_map.values() if n.entity_type == "device"]
            if len(customer_nids) > 1 and device_nids:
                collusion_stmt = (
                    select(
                        TransactionModel.customer_id,
                        TransactionModel.device_id,
                    )
                    .where(
                        TransactionModel.customer_id.in_(customer_nids),
                        TransactionModel.device_id.in_(device_nids),
                    )
                    .distinct()
                )
                pairs = session.execute(collusion_stmt).all()
                # Map device -> set of customers
                dev_to_custs: dict[str, set[str]] = {}
                for c_id, d_id in pairs:
                    if d_id and c_id:
                        dev_to_custs.setdefault(d_id, set()).add(c_id)

                for dev_id, custs in dev_to_custs.items():
                    cust_list = sorted(custs)
                    for i in range(len(cust_list)):
                        for j in range(i + 1, len(cust_list)):
                            c1_nid = make_node_id("customer", cust_list[i])
                            c2_nid = make_node_id("customer", cust_list[j])
                            add_edge(
                                c1_nid,
                                c2_nid,
                                "SHARES_DEVICE",
                                weight=1.5,
                                metadata={"shared_device": dev_id},
                            )

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
