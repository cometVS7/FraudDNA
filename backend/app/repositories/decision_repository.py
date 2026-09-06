"""FraudDNA Decision Repository.

Provides persistent access and storage for authoritative DecisionModel records.
"""

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.domain import DecisionModel

MAX_PAGE_LIMIT = 200
DEFAULT_PAGE_LIMIT = 50


class DecisionRepository:
    """Encapsulates persistent queries and storage for deterministic decisions."""

    def get_by_id(self, session: Session, decision_id: str) -> DecisionModel | None:
        """Retrieve decision record by ID."""
        stmt = select(DecisionModel).where(DecisionModel.id == decision_id)
        return session.execute(stmt).scalar_one_or_none()

    def get_by_transaction_id(self, session: Session, transaction_id: str) -> DecisionModel | None:
        """Retrieve most recent decision for a given transaction."""
        stmt = (
            select(DecisionModel)
            .where(DecisionModel.transaction_id == transaction_id)
            .order_by(desc(DecisionModel.generated_at))
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()

    def create(self, session: Session, decision: DecisionModel) -> DecisionModel:
        """Persist a new deterministic decision."""
        session.add(decision)
        session.flush()
        return decision

    def list_decisions(
        self,
        session: Session,
        limit: int = DEFAULT_PAGE_LIMIT,
        offset: int = 0,
        action: str | None = None,
        policy_id: str | None = None,
    ) -> tuple[list[DecisionModel], int]:
        """Retrieve bounded, filtered decisions with total count."""
        safe_limit = max(1, min(limit, MAX_PAGE_LIMIT))
        safe_offset = max(0, offset)

        stmt = select(DecisionModel)
        count_stmt = select(func.count()).select_from(DecisionModel)

        conditions = []
        if action:
            conditions.append(DecisionModel.action == action)
        if policy_id:
            conditions.append(DecisionModel.policy_id == policy_id)

        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        stmt = stmt.order_by(desc(DecisionModel.generated_at)).limit(safe_limit).offset(safe_offset)

        total_count = session.execute(count_stmt).scalar_one()
        items = list(session.execute(stmt).scalars().all())

        return items, total_count
