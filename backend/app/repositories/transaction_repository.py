"""FraudDNA Transaction Repository.

Provides bounded, filtered, and sorted data access for transactions.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.domain import TransactionModel

MAX_PAGE_LIMIT = 200
DEFAULT_PAGE_LIMIT = 50


class TransactionRepository:
    """Encapsulates persistent querying for TransactionModel."""

    def get_by_id(self, session: Session, transaction_id: str) -> TransactionModel | None:
        """Retrieve a single transaction by its primary key."""
        stmt = select(TransactionModel).where(TransactionModel.id == transaction_id)
        return session.execute(stmt).scalar_one_or_none()

    def list_transactions(
        self,
        session: Session,
        limit: int = DEFAULT_PAGE_LIMIT,
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
    ) -> tuple[list[TransactionModel], int]:
        """Retrieve bounded, filtered, and sorted transactions along with total count."""
        safe_limit = max(1, min(limit, MAX_PAGE_LIMIT))
        safe_offset = max(0, offset)

        stmt = select(TransactionModel)
        count_stmt = select(func.count()).select_from(TransactionModel)

        # Filters
        conditions = []
        if customer_id:
            conditions.append(TransactionModel.customer_id == customer_id)
        if merchant_id:
            conditions.append(TransactionModel.merchant_id == merchant_id)
        if card_id:
            conditions.append(TransactionModel.card_id == card_id)
        if device_id:
            conditions.append(TransactionModel.device_id == device_id)
        if ip_id:
            conditions.append(TransactionModel.ip_id == ip_id)
        if network_id:
            conditions.append(TransactionModel.network_id == network_id)
        if risk_tier:
            conditions.append(TransactionModel.risk_tier == risk_tier)
        if min_risk_score is not None:
            conditions.append(TransactionModel.risk_score >= min_risk_score)
        if max_risk_score is not None:
            conditions.append(TransactionModel.risk_score <= max_risk_score)
        if min_amount is not None:
            conditions.append(TransactionModel.amount >= min_amount)
        if max_amount is not None:
            conditions.append(TransactionModel.amount <= max_amount)
        if start_time:
            conditions.append(TransactionModel.timestamp >= start_time)
        if end_time:
            conditions.append(TransactionModel.timestamp <= end_time)
        if decision_action:
            conditions.append(TransactionModel.decision_action == decision_action)
        if is_fraud is not None:
            conditions.append(TransactionModel.is_fraud == is_fraud)

        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        # Sorting
        sort_col = getattr(TransactionModel, sort_by, TransactionModel.timestamp)
        if sort_order.lower() == "asc":
            stmt = stmt.order_by(sort_col.asc(), TransactionModel.id.asc())
        else:
            stmt = stmt.order_by(desc(sort_col), TransactionModel.id.desc())

        stmt = stmt.limit(safe_limit).offset(safe_offset)

        total_count = session.execute(count_stmt).scalar_one()
        items = list(session.execute(stmt).scalars().all())

        return items, total_count
