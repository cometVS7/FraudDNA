"""FraudDNA Network Application Service.

Encapsulates persistent access, member analysis, and graph exploration of RiskNetworkModel
and fraud syndicate clusters.
"""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import NotFoundDomainError
from app.graph.models import make_node_id
from app.models.domain import RiskNetworkModel
from app.repositories.network_repository import NetworkRepository
from app.schemas.cluster import (
    ClusterDetail,
    ClusterRiskFactor,
    NetworkMembersResponse,
    NetworkTransactionsResponse,
)
from app.schemas.graph import GraphData

logger = logging.getLogger(__name__)


class NetworkService:
    """Coordinates risk network and fraud syndicate cluster persistence and lookups."""

    def __init__(self, repo: NetworkRepository | None = None) -> None:
        self.repo = repo or NetworkRepository()

    def get_network(
        self, session: Session, network_id: str, load_transactions: bool = False
    ) -> RiskNetworkModel:
        """Retrieve risk network by cluster/network ID."""
        network = self.repo.get_by_id(session, network_id, load_transactions=load_transactions)
        if not network:
            raise NotFoundDomainError(
                f"Risk network '{network_id}' not found.",
                details={"network_id": network_id},
            )
        return network

    def list_networks(
        self,
        session: Session,
        limit: int = 50,
        offset: int = 0,
        is_suspicious: bool | None = None,
        min_risk_score: float | None = None,
    ) -> tuple[list[RiskNetworkModel], int]:
        """Query bounded risk networks with filtering and pagination."""
        return self.repo.list_networks(
            session=session,
            limit=limit,
            offset=offset,
            is_suspicious=is_suspicious,
            min_risk_score=min_risk_score,
        )

    def get_network_members(self, session: Session, network_id: str) -> NetworkMembersResponse:
        """Retrieve all member entity IDs grouped by entity type."""
        # Ensure network exists
        self.get_network(session, network_id)
        members = self.repo.get_network_member_entities(session, network_id)
        total = (
            len(members["customers"])
            + len(members["devices"])
            + len(members["ips"])
            + len(members["cards"])
            + len(members["merchants"])
        )
        return NetworkMembersResponse(
            network_id=network_id,
            total_members=total,
            customer_ids=members["customers"],
            device_ids=members["devices"],
            ip_addresses=members["ips"],
            card_ids=members["cards"],
            merchant_ids=members["merchants"],
        )

    def get_network_transactions(
        self,
        session: Session,
        network_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> NetworkTransactionsResponse:
        """Retrieve paginated member transactions belonging to a risk network."""
        self.get_network(session, network_id)
        txs, total_count = self.repo.get_network_transactions(
            session=session,
            network_id=network_id,
            limit=limit,
            offset=offset,
        )
        serialized_txs: list[dict[str, Any]] = []
        for tx in txs:
            serialized_txs.append(
                {
                    "id": tx.id,
                    "timestamp": tx.timestamp.isoformat(),
                    "amount": float(tx.amount),
                    "currency": tx.currency,
                    "payment_method": tx.payment_method,
                    "city": tx.city,
                    "risk_score": tx.risk_score,
                    "risk_tier": tx.risk_tier,
                    "is_fraud": tx.is_fraud,
                    "customer_id": tx.customer_id,
                    "device_id": tx.device_id,
                    "ip_id": tx.ip_id,
                    "card_id": tx.card_id,
                    "merchant_id": tx.merchant_id,
                    "network_id": tx.network_id,
                }
            )

        return NetworkTransactionsResponse(
            network_id=network_id,
            total_transactions=total_count,
            limit=limit,
            offset=offset,
            transactions=serialized_txs,
        )

    def get_network_graph(
        self,
        session: Session,
        network_id: str,
        max_nodes: int = 100,
        max_transactions: int = 100,
    ) -> GraphData:
        """Synthesize a bounded, deterministic GraphData representation for a risk network."""
        self.get_network(session, network_id)
        return self.repo.get_network_graph(
            session=session,
            network_id=network_id,
            max_nodes=max_nodes,
            max_transactions=max_transactions,
        )

    def get_network_detail(self, session: Session, network_id: str) -> ClusterDetail:
        """Construct full ClusterDetail with bounded subgraph directly from PostgreSQL."""
        net = self.get_network(session, network_id)
        members = self.repo.get_network_member_entities(session, network_id)
        txs, total_tx = self.repo.get_network_transactions(
            session=session, network_id=network_id, limit=200
        )

        suspicious_txs = [t for t in txs if t.risk_score >= 0.37]
        suspicious_amount = sum(float(t.amount) for t in suspicious_txs)

        # Risk factors derivation
        risk_factors: list[ClusterRiskFactor] = []
        if len(members["devices"]) < len(members["customers"]) and len(members["devices"]) > 0:
            risk_factors.append(
                ClusterRiskFactor(
                    factor_type="SHARED_DEVICE_COLLUSION",
                    description=f"{len(members['customers'])} customers share {len(members['devices'])} physical devices.",
                    severity="HIGH" if net.is_suspicious else "MEDIUM",
                    weight=0.35,
                )
            )
        if len(members["ips"]) < len(members["customers"]) and len(members["ips"]) > 0:
            risk_factors.append(
                ClusterRiskFactor(
                    factor_type="SHARED_IP_INFRASTRUCTURE",
                    description=f"{len(members['customers'])} customers share {len(members['ips'])} IP addresses.",
                    severity="MEDIUM",
                    weight=0.25,
                )
            )
        if len(members["cards"]) < len(members["customers"]) and len(members["cards"]) > 0:
            risk_factors.append(
                ClusterRiskFactor(
                    factor_type="SHARED_CARD_COLLUSION",
                    description=f"{len(members['customers'])} customers transacted with {len(members['cards'])} payment cards.",
                    severity="HIGH",
                    weight=0.30,
                )
            )
        if net.is_suspicious:
            risk_factors.append(
                ClusterRiskFactor(
                    factor_type="COORDINATED_FRAUD_SYNDICATE",
                    description=net.primary_reason
                    or "Coordinated multi-party transaction abuse detected.",
                    severity="CRITICAL",
                    weight=0.40,
                )
            )

        graph_data = self.repo.get_network_graph(
            session=session, network_id=network_id, max_nodes=100, max_transactions=100
        )

        connected_entity_ids: list[str] = (
            [make_node_id("customer", c) for c in members["customers"]]
            + [make_node_id("device", d) for d in members["devices"]]
            + [make_node_id("ip", i) for i in members["ips"]]
            + [make_node_id("card", k) for k in members["cards"]]
            + [make_node_id("merchant", m) for m in members["merchants"]]
        )

        explanation = (
            net.primary_reason
            or f"Risk network '{network_id}' contains {total_tx} transactions totaling INR {float(net.total_amount):.2f} "
            f"across {len(members['customers'])} customers and {len(members['devices'])} devices."
        )

        return ClusterDetail(
            cluster_id=net.id,
            cluster_risk_score=float(net.risk_score),
            is_suspicious=net.is_suspicious,
            transaction_count=net.transaction_count,
            customer_count=net.customer_count,
            device_count=net.device_count,
            ip_count=net.ip_count,
            card_count=net.card_count,
            merchant_count=net.merchant_count,
            suspicious_transaction_count=len(suspicious_txs),
            total_transaction_amount=float(net.total_amount),
            suspicious_transaction_amount=round(suspicious_amount, 2),
            primary_reason=net.primary_reason or "Suspicious multi-entity cluster",
            member_transaction_ids=[t.id for t in txs],
            connected_entity_ids=connected_entity_ids,
            risk_factors=risk_factors,
            explanation=explanation,
            graph_data=graph_data,
            metadata={
                "first_seen": net.first_seen.isoformat() if net.first_seen else None,
                "last_seen": net.last_seen.isoformat() if net.last_seen else None,
                "status": net.status,
            },
        )


_network_service_instance: NetworkService | None = None


def get_network_service() -> NetworkService:
    """Dependency provider for NetworkService."""
    global _network_service_instance
    if _network_service_instance is None:
        _network_service_instance = NetworkService()
    return _network_service_instance
