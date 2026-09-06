"""FraudDNA Risk Network Repository.

Encapsulates database operations for RiskNetworkModel entities.
"""

from typing import Any

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.domain import RiskNetworkModel


class NetworkRepository:
    """Encapsulates persistent querying for RiskNetworkModel."""

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
        session.flush()
        return existing
