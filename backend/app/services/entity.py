"""FraudDNA Entity Application Service.

Encapsulates persistent entity retrieval, profile synthesis, deterministic risk aggregation,
point-in-time behavioral velocity metrics, and database-backed graph neighborhood retrieval.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import NotFoundDomainError, ValidationDomainError
from app.repositories.entity_repository import EntityRepository
from app.schemas.entity import (
    AccountProfileResponse,
    AssociatedNetworkSummary,
    BehavioralMetrics,
    CardProfileResponse,
    CustomerProfileResponse,
    DeviceProfileResponse,
    EntityRelationshipItem,
    EntityRelationshipsResponse,
    EntityRiskAggregation,
    EntityTransactionsResponse,
    IPAddressProfileResponse,
    MerchantProfileResponse,
)
from app.schemas.graph import GraphData

logger = logging.getLogger(__name__)


def compute_deterministic_entity_risk(
    max_tx_risk: float,
    avg_top3_tx_risk: float,
    network_exposure: float,
    sharing_anomaly: float,
    entity_name: str,
) -> EntityRiskAggregation:
    """Compute transparent deterministic entity-level risk aggregation.

    Formula:
        entity_risk_score = min(1.0, max(0.0,
            0.40 * max_tx_risk +
            0.20 * avg_top3_tx_risk +
            0.25 * network_exposure +
            0.15 * sharing_anomaly
        ))
    """
    raw_score = (
        0.40 * max_tx_risk
        + 0.20 * avg_top3_tx_risk
        + 0.25 * network_exposure
        + 0.15 * sharing_anomaly
    )
    score = round(min(1.0, max(0.0, raw_score)), 4)

    if score >= 0.90:
        tier = "CRITICAL"
    elif score >= 0.70:
        tier = "HIGH"
    elif score >= 0.30:
        tier = "MEDIUM"
    else:
        tier = "LOW"

    explanation = (
        f"{entity_name} risk evaluated at {score:.4f} ({tier}) from max tx risk ({max_tx_risk:.2f}), "
        f"top-3 mean tx risk ({avg_top3_tx_risk:.2f}), network exposure ({network_exposure:.2f}), "
        f"and sharing anomaly ({sharing_anomaly:.2f})."
    )

    return EntityRiskAggregation(
        risk_score=score,
        risk_tier=tier,
        max_tx_risk=max_tx_risk,
        avg_top3_tx_risk=avg_top3_tx_risk,
        network_exposure=network_exposure,
        sharing_anomaly=sharing_anomaly,
        explanation=explanation,
    )


class EntityService:
    """Coordinates retrieval, risk aggregation, and graph exploration for financial entities."""

    def __init__(self, entity_repo: EntityRepository | None = None) -> None:
        self.repo = entity_repo or EntityRepository()

    def _format_tx(self, tx: Any) -> dict[str, Any]:
        """Serialize a TransactionModel into bounded dictionary."""
        return {
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

    def _to_network_summaries(self, networks: list[Any]) -> list[AssociatedNetworkSummary]:
        """Convert RiskNetworkModel instances into lightweight summaries."""
        return [
            AssociatedNetworkSummary(
                network_id=net.id,
                network_name=net.network_name,
                is_suspicious=net.is_suspicious,
                risk_score=float(net.risk_score),
                transaction_count=net.transaction_count,
            )
            for net in networks
        ]

    def get_customer_profile(
        self, session: Session, customer_id: str, as_of: datetime | None = None
    ) -> CustomerProfileResponse:
        """Retrieve customer entity profile with behavioral intelligence and risk aggregation."""
        cust = self.repo.get_customer(session, customer_id)
        if not cust:
            raise NotFoundDomainError(
                f"Customer '{customer_id}' not found.",
                details={"customer_id": customer_id},
            )

        # Risk signals & deterministic aggregation
        signals = self.repo.get_entity_risk_signals(
            session=session,
            entity_type="customer",
            entity_id=customer_id,
            as_of=as_of,
        )
        risk_agg = compute_deterministic_entity_risk(
            max_tx_risk=signals["max_tx_risk"],
            avg_top3_tx_risk=signals["avg_top3_tx_risk"],
            network_exposure=signals["network_exposure"],
            sharing_anomaly=signals["sharing_anomaly"],
            entity_name=f"Customer '{customer_id}'",
        )

        # Behavioral velocity metrics
        behavior_data = self.repo.get_behavioral_metrics(
            session=session,
            entity_type="customer",
            entity_id=customer_id,
            as_of=as_of,
        )
        behavioral_metrics = BehavioralMetrics(**behavior_data)

        # Recent transactions (up to 5)
        txs, _ = self.repo.get_entity_transactions(
            session=session,
            entity_type="customer",
            entity_id=customer_id,
            limit=5,
            offset=0,
            as_of=as_of,
        )
        recent_txs = [self._format_tx(t) for t in txs]

        # Connected entities summary
        accounts = self.repo.get_customer_accounts(session, customer_id)
        connected_summary = {
            "accounts_count": len(accounts),
            "recent_merchants_count": behavior_data["unique_merchants_24h"],
            "recent_devices_count": behavior_data["unique_devices_24h"],
            "recent_ips_count": behavior_data["unique_ips_24h"],
            "cross_customer_sharing_count": behavior_data["cross_customer_sharing_count"],
        }

        return CustomerProfileResponse(
            id=cust.id,
            created_at=cust.created_at,
            account_age_days=cust.account_age_days,
            city=cust.city,
            status=cust.status,
            risk_tier=risk_agg.risk_tier,
            risk_score=risk_agg.risk_score,
            total_transactions=signals["total_tx_count"],
            total_amount=signals["total_tx_amount"],
            recent_transactions=recent_txs,
            risk_aggregation=risk_agg,
            behavioral_metrics=behavioral_metrics,
            associated_networks=self._to_network_summaries(signals["associated_networks"]),
            connected_entities_summary=connected_summary,
        )

    def get_device_profile(
        self, session: Session, device_id: str, as_of: datetime | None = None
    ) -> DeviceProfileResponse:
        """Retrieve device entity profile with behavioral metrics and risk aggregation."""
        dev = self.repo.get_device(session, device_id)
        if not dev:
            raise NotFoundDomainError(
                f"Device '{device_id}' not found.",
                details={"device_id": device_id},
            )

        signals = self.repo.get_entity_risk_signals(
            session=session,
            entity_type="device",
            entity_id=device_id,
            as_of=as_of,
        )
        risk_agg = compute_deterministic_entity_risk(
            max_tx_risk=signals["max_tx_risk"],
            avg_top3_tx_risk=signals["avg_top3_tx_risk"],
            network_exposure=signals["network_exposure"],
            sharing_anomaly=signals["sharing_anomaly"],
            entity_name=f"Device '{device_id}'",
        )

        behavior_data = self.repo.get_behavioral_metrics(
            session=session,
            entity_type="device",
            entity_id=device_id,
            as_of=as_of,
        )
        behavioral_metrics = BehavioralMetrics(**behavior_data)

        txs, _ = self.repo.get_entity_transactions(
            session=session,
            entity_type="device",
            entity_id=device_id,
            limit=5,
            offset=0,
            as_of=as_of,
        )
        recent_txs = [self._format_tx(t) for t in txs]

        return DeviceProfileResponse(
            id=dev.id,
            device_fingerprint=dev.device_fingerprint,
            status=dev.status,
            risk_score=risk_agg.risk_score,
            risk_tier=risk_agg.risk_tier,
            first_seen=dev.first_seen,
            last_seen=dev.last_seen,
            associated_transactions_count=signals["total_tx_count"],
            total_amount=signals["total_tx_amount"],
            recent_transactions=recent_txs,
            risk_aggregation=risk_agg,
            behavioral_metrics=behavioral_metrics,
            associated_networks=self._to_network_summaries(signals["associated_networks"]),
            connected_customers_count=signals["cross_customer_sharing_count"]
            + (1 if signals["total_tx_count"] > 0 else 0),
        )

    def get_ip_profile(
        self, session: Session, ip_address: str, as_of: datetime | None = None
    ) -> IPAddressProfileResponse:
        """Retrieve IP address intelligence profile."""
        ip = self.repo.get_ip_address(session, ip_address)
        if not ip:
            raise NotFoundDomainError(
                f"IP address '{ip_address}' not found.",
                details={"ip_address": ip_address},
            )

        signals = self.repo.get_entity_risk_signals(
            session=session,
            entity_type="ip",
            entity_id=ip_address,
            as_of=as_of,
        )
        risk_agg = compute_deterministic_entity_risk(
            max_tx_risk=signals["max_tx_risk"],
            avg_top3_tx_risk=signals["avg_top3_tx_risk"],
            network_exposure=signals["network_exposure"],
            sharing_anomaly=signals["sharing_anomaly"],
            entity_name=f"IP '{ip_address}'",
        )

        behavior_data = self.repo.get_behavioral_metrics(
            session=session,
            entity_type="ip",
            entity_id=ip_address,
            as_of=as_of,
        )
        behavioral_metrics = BehavioralMetrics(**behavior_data)

        txs, _ = self.repo.get_entity_transactions(
            session=session,
            entity_type="ip",
            entity_id=ip_address,
            limit=5,
            offset=0,
            as_of=as_of,
        )
        recent_txs = [self._format_tx(t) for t in txs]

        return IPAddressProfileResponse(
            id=ip.id,
            ip_address=ip.ip_address,
            status=ip.status,
            risk_score=risk_agg.risk_score,
            risk_tier=risk_agg.risk_tier,
            first_seen=ip.first_seen,
            last_seen=ip.last_seen,
            associated_transactions_count=signals["total_tx_count"],
            total_amount=signals["total_tx_amount"],
            recent_transactions=recent_txs,
            risk_aggregation=risk_agg,
            behavioral_metrics=behavioral_metrics,
            associated_networks=self._to_network_summaries(signals["associated_networks"]),
            connected_customers_count=signals["cross_customer_sharing_count"]
            + (1 if signals["total_tx_count"] > 0 else 0),
        )

    def get_card_profile(
        self, session: Session, card_id: str, as_of: datetime | None = None
    ) -> CardProfileResponse:
        """Retrieve card payment instrument profile."""
        card = self.repo.get_card(session, card_id)
        if not card:
            raise NotFoundDomainError(
                f"Card '{card_id}' not found.",
                details={"card_id": card_id},
            )

        signals = self.repo.get_entity_risk_signals(
            session=session,
            entity_type="card",
            entity_id=card_id,
            as_of=as_of,
        )
        risk_agg = compute_deterministic_entity_risk(
            max_tx_risk=signals["max_tx_risk"],
            avg_top3_tx_risk=signals["avg_top3_tx_risk"],
            network_exposure=signals["network_exposure"],
            sharing_anomaly=signals["sharing_anomaly"],
            entity_name=f"Card '{card_id}'",
        )

        behavior_data = self.repo.get_behavioral_metrics(
            session=session,
            entity_type="card",
            entity_id=card_id,
            as_of=as_of,
        )
        behavioral_metrics = BehavioralMetrics(**behavior_data)

        txs, _ = self.repo.get_entity_transactions(
            session=session,
            entity_type="card",
            entity_id=card_id,
            limit=5,
            offset=0,
            as_of=as_of,
        )
        recent_txs = [self._format_tx(t) for t in txs]

        return CardProfileResponse(
            id=card.id,
            card_type=card.card_type,
            status=card.status,
            risk_score=risk_agg.risk_score,
            risk_tier=risk_agg.risk_tier,
            first_seen=card.first_seen,
            last_seen=card.last_seen,
            associated_transactions_count=signals["total_tx_count"],
            total_amount=signals["total_tx_amount"],
            recent_transactions=recent_txs,
            risk_aggregation=risk_agg,
            behavioral_metrics=behavioral_metrics,
            associated_networks=self._to_network_summaries(signals["associated_networks"]),
            connected_customers_count=signals["cross_customer_sharing_count"]
            + (1 if signals["total_tx_count"] > 0 else 0),
        )

    def get_merchant_profile(
        self, session: Session, merchant_id: str, as_of: datetime | None = None
    ) -> MerchantProfileResponse:
        """Retrieve merchant business profile."""
        m = self.repo.get_merchant(session, merchant_id)
        if not m:
            raise NotFoundDomainError(
                f"Merchant '{merchant_id}' not found.",
                details={"merchant_id": merchant_id},
            )

        signals = self.repo.get_entity_risk_signals(
            session=session,
            entity_type="merchant",
            entity_id=merchant_id,
            as_of=as_of,
        )
        risk_agg = compute_deterministic_entity_risk(
            max_tx_risk=signals["max_tx_risk"],
            avg_top3_tx_risk=signals["avg_top3_tx_risk"],
            network_exposure=signals["network_exposure"],
            sharing_anomaly=signals["sharing_anomaly"],
            entity_name=f"Merchant '{merchant_id}'",
        )

        behavior_data = self.repo.get_behavioral_metrics(
            session=session,
            entity_type="merchant",
            entity_id=merchant_id,
            as_of=as_of,
        )
        behavioral_metrics = BehavioralMetrics(**behavior_data)

        txs, _ = self.repo.get_entity_transactions(
            session=session,
            entity_type="merchant",
            entity_id=merchant_id,
            limit=5,
            offset=0,
            as_of=as_of,
        )
        recent_txs = [self._format_tx(t) for t in txs]

        return MerchantProfileResponse(
            id=m.id,
            merchant_category=m.merchant_category,
            status=m.status,
            risk_score=risk_agg.risk_score,
            risk_tier=risk_agg.risk_tier,
            created_at=m.created_at,
            associated_transactions_count=signals["total_tx_count"],
            total_amount=signals["total_tx_amount"],
            recent_transactions=recent_txs,
            risk_aggregation=risk_agg,
            behavioral_metrics=behavioral_metrics,
            associated_networks=self._to_network_summaries(signals["associated_networks"]),
        )

    def get_account_profile(
        self, session: Session, account_id: str, as_of: datetime | None = None
    ) -> AccountProfileResponse:
        """Retrieve financial account profile."""
        acc = self.repo.get_account(session, account_id)
        if not acc:
            raise NotFoundDomainError(
                f"Account '{account_id}' not found.",
                details={"account_id": account_id},
            )

        signals = self.repo.get_entity_risk_signals(
            session=session,
            entity_type="account",
            entity_id=account_id,
            as_of=as_of,
        )
        risk_agg = compute_deterministic_entity_risk(
            max_tx_risk=signals["max_tx_risk"],
            avg_top3_tx_risk=signals["avg_top3_tx_risk"],
            network_exposure=signals["network_exposure"],
            sharing_anomaly=signals["sharing_anomaly"],
            entity_name=f"Account '{account_id}'",
        )

        behavior_data = self.repo.get_behavioral_metrics(
            session=session,
            entity_type="account",
            entity_id=account_id,
            as_of=as_of,
        )
        behavioral_metrics = BehavioralMetrics(**behavior_data)

        txs, _ = self.repo.get_entity_transactions(
            session=session,
            entity_type="account",
            entity_id=account_id,
            limit=5,
            offset=0,
            as_of=as_of,
        )
        recent_txs = [self._format_tx(t) for t in txs]

        return AccountProfileResponse(
            id=acc.id,
            customer_id=acc.customer_id,
            account_type=acc.account_type,
            status=acc.status,
            risk_score=risk_agg.risk_score,
            risk_tier=risk_agg.risk_tier,
            created_at=acc.created_at,
            total_transactions=signals["total_tx_count"],
            total_amount=signals["total_tx_amount"],
            recent_transactions=recent_txs,
            risk_aggregation=risk_agg,
            behavioral_metrics=behavioral_metrics,
            associated_networks=self._to_network_summaries(signals["associated_networks"]),
        )

    # --------------------------------------------------------------------------
    # Generic Entity Query APIs
    # --------------------------------------------------------------------------

    def _verify_entity_exists(self, session: Session, entity_type: str, entity_id: str) -> None:
        """Verify that the requested entity exists in PostgreSQL or raise NotFoundDomainError."""
        etype = entity_type.lower()
        exists = False
        if etype == "customer":
            exists = self.repo.get_customer(session, entity_id) is not None
        elif etype == "account":
            exists = self.repo.get_account(session, entity_id) is not None
        elif etype == "device":
            exists = self.repo.get_device(session, entity_id) is not None
        elif etype == "ip":
            exists = self.repo.get_ip_address(session, entity_id) is not None
        elif etype == "card":
            exists = self.repo.get_card(session, entity_id) is not None
        elif etype == "merchant":
            exists = self.repo.get_merchant(session, entity_id) is not None
        elif etype == "network":
            exists = self.repo.get_risk_network(session, entity_id) is not None
        elif etype == "transaction":
            txs, _ = self.repo.get_entity_transactions(session, "transaction", entity_id, limit=1)
            exists = len(txs) > 0
        else:
            raise ValidationDomainError(
                f"Unsupported entity type: '{entity_type}'",
                details={"entity_type": entity_type},
            )

        if not exists:
            raise NotFoundDomainError(
                f"{entity_type.capitalize()} '{entity_id}' not found.",
                details={"entity_type": entity_type, "entity_id": entity_id},
            )

    def get_entity_transactions(
        self,
        session: Session,
        entity_type: str,
        entity_id: str,
        limit: int = 50,
        offset: int = 0,
        as_of: datetime | None = None,
    ) -> EntityTransactionsResponse:
        """Retrieve bounded, paginated transactions for an entity."""
        self._verify_entity_exists(session, entity_type, entity_id)
        txs, total_count = self.repo.get_entity_transactions(
            session=session,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=offset,
            as_of=as_of,
        )
        return EntityTransactionsResponse(
            entity_type=entity_type.lower(),
            entity_id=entity_id,
            total_transactions=total_count,
            limit=limit,
            offset=offset,
            transactions=[self._format_tx(t) for t in txs],
        )

    def get_entity_relationships(
        self,
        session: Session,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
    ) -> EntityRelationshipsResponse:
        """Retrieve direct typed semantic relationships connected to an entity."""
        self._verify_entity_exists(session, entity_type, entity_id)
        raw_rels = self.repo.get_direct_relationships(
            session=session,
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
        )
        items = [EntityRelationshipItem(**r) for r in raw_rels]
        return EntityRelationshipsResponse(
            entity_type=entity_type.lower(),
            entity_id=entity_id,
            total_relationships=len(items),
            relationships=items,
        )

    def get_entity_neighborhood_graph(
        self,
        session: Session,
        entity_type: str,
        entity_id: str,
        depth: int = 1,
        max_nodes: int = 100,
        max_transactions: int = 100,
    ) -> GraphData:
        """Retrieve bounded, deterministic GraphData surrounding an entity or transaction."""
        self._verify_entity_exists(session, entity_type, entity_id)
        return self.repo.get_bounded_neighborhood(
            session=session,
            entity_type=entity_type,
            entity_id=entity_id,
            depth=depth,
            max_nodes=max_nodes,
            max_transactions=max_transactions,
        )


_entity_service_instance: EntityService | None = None


def get_entity_service() -> EntityService:
    """Dependency provider for EntityService."""
    global _entity_service_instance
    if _entity_service_instance is None:
        _entity_service_instance = EntityService()
    return _entity_service_instance
