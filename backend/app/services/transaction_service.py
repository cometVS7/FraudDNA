"""FraudDNA Transaction Application Service.

Provides bounded, filtered transaction access and detail enrichment.
"""

import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import NotFoundDomainError
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import (
    TransactionDetail,
    TransactionListResponse,
    TransactionSummary,
)

logger = logging.getLogger(__name__)


class TransactionService:
    """Coordinates business operations for transaction retrieval and filtering."""

    def __init__(self, tx_repo: TransactionRepository | None = None) -> None:
        self.repo = tx_repo or TransactionRepository()

    def get_transaction(self, session: Session, transaction_id: str) -> TransactionDetail:
        """Retrieve a single transaction with enrichment or raise NotFoundDomainError."""
        tx = self.repo.get_by_id(session, transaction_id)
        if not tx:
            raise NotFoundDomainError(
                f"Transaction '{transaction_id}' not found.",
                details={"transaction_id": transaction_id},
            )

        # Map signals if present
        signals = []
        if tx.risk_assessments:
            latest_assessment = tx.risk_assessments[-1]
            for s in latest_assessment.risk_signals:
                signals.append(
                    {
                        "feature_name": s.feature_name,
                        "feature_value": s.feature_value,
                        "impact": s.impact,
                        "direction": s.direction,
                    }
                )

        return TransactionDetail(
            id=tx.id,
            timestamp=tx.timestamp,
            amount=tx.amount,
            currency=tx.currency,
            payment_method=tx.payment_method,
            city=tx.city,
            customer_id=tx.customer_id,
            merchant_id=tx.merchant_id,
            card_id=tx.card_id,
            device_id=tx.device_id,
            ip_id=tx.ip_id,
            network_id=tx.network_id,
            risk_score=tx.risk_score,
            risk_tier=tx.risk_tier,
            decision_action=tx.decision_action,
            is_fraud=tx.is_fraud,
            fraud_scenario=tx.fraud_scenario,
            risk_signals=signals,
            customer_city=tx.customer.city if tx.customer else None,
            merchant_category=tx.merchant.merchant_category if tx.merchant else None,
        )

    def list_transactions(
        self,
        session: Session,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "timestamp",
        sort_order: str = "desc",
        customer_id: str | None = None,
        merchant_id: str | None = None,
        card_id: str | None = None,
        device_id: str | None = None,
        ip_id: str | None = None,
        network_id: str | None = None,
        risk_tier: str | None = None,
        min_risk_score: float | None = None,
        max_risk_score: float | None = None,
        min_amount: Decimal | None = None,
        max_amount: Decimal | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        decision_action: str | None = None,
        is_fraud: bool | None = None,
    ) -> TransactionListResponse:
        """Query bounded transactions matching search filters."""
        items, total = self.repo.list_transactions(
            session=session,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            customer_id=customer_id,
            merchant_id=merchant_id,
            card_id=card_id,
            device_id=device_id,
            ip_id=ip_id,
            network_id=network_id,
            risk_tier=risk_tier,
            min_risk_score=min_risk_score,
            max_risk_score=max_risk_score,
            min_amount=min_amount,
            max_amount=max_amount,
            start_time=start_time,
            end_time=end_time,
            decision_action=decision_action,
            is_fraud=is_fraud,
        )
        summaries = [TransactionSummary.model_validate(it) for it in items]
        return TransactionListResponse(
            items=summaries,
            total_count=total,
            limit=limit,
            offset=offset,
        )


_transaction_service_instance: TransactionService | None = None


def get_transaction_service() -> TransactionService:
    """Dependency provider for TransactionService."""
    global _transaction_service_instance
    if _transaction_service_instance is None:
        _transaction_service_instance = TransactionService()
    return _transaction_service_instance
