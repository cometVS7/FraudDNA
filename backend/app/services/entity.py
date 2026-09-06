"""FraudDNA Entity Application Service.

Encapsulates persistent entity retrieval, profile synthesis, and risk posture.
"""

import logging

from sqlalchemy.orm import Session

from app.core.errors import NotFoundDomainError
from app.repositories.entity_repository import EntityRepository
from app.schemas.entity import (
    CardProfileResponse,
    CustomerProfileResponse,
    DeviceProfileResponse,
    IPAddressProfileResponse,
    MerchantProfileResponse,
)

logger = logging.getLogger(__name__)


class EntityService:
    """Coordinates retrieval of financial graph and relational entities."""

    def __init__(self, entity_repo: EntityRepository | None = None) -> None:
        self.repo = entity_repo or EntityRepository()

    def get_customer_profile(self, session: Session, customer_id: str) -> CustomerProfileResponse:
        """Retrieve customer entity profile with recent transactions."""
        cust = self.repo.get_customer(session, customer_id)
        if not cust:
            raise NotFoundDomainError(
                f"Customer '{customer_id}' not found.",
                details={"customer_id": customer_id},
            )

        recent_txs = []
        if cust.transactions:
            for tx in sorted(cust.transactions, key=lambda t: t.timestamp, reverse=True)[:5]:
                recent_txs.append(
                    {
                        "id": tx.id,
                        "amount": float(tx.amount),
                        "timestamp": tx.timestamp.isoformat(),
                        "risk_score": tx.risk_score,
                        "risk_tier": tx.risk_tier,
                    }
                )

        total_tx = len(cust.transactions) if cust.transactions else 0
        return CustomerProfileResponse(
            id=cust.id,
            created_at=cust.created_at,
            account_age_days=cust.account_age_days,
            city=cust.city,
            status=cust.status,
            risk_tier=cust.risk_tier,
            risk_score=cust.risk_score,
            total_transactions=total_tx,
            recent_transactions=recent_txs,
        )

    def get_device_profile(self, session: Session, device_id: str) -> DeviceProfileResponse:
        """Retrieve device entity profile."""
        dev = self.repo.get_device(session, device_id)
        if not dev:
            raise NotFoundDomainError(
                f"Device '{device_id}' not found.",
                details={"device_id": device_id},
            )
        tx_count = len(dev.transactions) if dev.transactions else 0
        return DeviceProfileResponse(
            id=dev.id,
            device_fingerprint=dev.device_fingerprint,
            status=dev.status,
            risk_score=dev.risk_score,
            risk_tier=dev.risk_tier,
            first_seen=dev.first_seen,
            last_seen=dev.last_seen,
            associated_transactions_count=tx_count,
        )

    def get_ip_profile(self, session: Session, ip_address: str) -> IPAddressProfileResponse:
        """Retrieve IP address intelligence profile."""
        ip = self.repo.get_ip_address(session, ip_address)
        if not ip:
            raise NotFoundDomainError(
                f"IP address '{ip_address}' not found.",
                details={"ip_address": ip_address},
            )
        tx_count = len(ip.transactions) if ip.transactions else 0
        return IPAddressProfileResponse(
            id=ip.id,
            ip_address=ip.ip_address,
            status=ip.status,
            risk_score=ip.risk_score,
            risk_tier=ip.risk_tier,
            first_seen=ip.first_seen,
            last_seen=ip.last_seen,
            associated_transactions_count=tx_count,
        )

    def get_card_profile(self, session: Session, card_id: str) -> CardProfileResponse:
        """Retrieve card payment instrument profile."""
        card = self.repo.get_card(session, card_id)
        if not card:
            raise NotFoundDomainError(
                f"Card '{card_id}' not found.",
                details={"card_id": card_id},
            )
        return CardProfileResponse.model_validate(card)

    def get_merchant_profile(self, session: Session, merchant_id: str) -> MerchantProfileResponse:
        """Retrieve merchant business profile."""
        m = self.repo.get_merchant(session, merchant_id)
        if not m:
            raise NotFoundDomainError(
                f"Merchant '{merchant_id}' not found.",
                details={"merchant_id": merchant_id},
            )
        return MerchantProfileResponse.model_validate(m)


_entity_service_instance: EntityService | None = None


def get_entity_service() -> EntityService:
    """Dependency provider for EntityService."""
    global _entity_service_instance
    if _entity_service_instance is None:
        _entity_service_instance = EntityService()
    return _entity_service_instance
