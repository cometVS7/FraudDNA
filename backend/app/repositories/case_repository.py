"""FraudDNA Case Repository.

Provides persistent access, bounded filtering, and updates for CaseModel.
"""

from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.domain import CaseModel

MAX_PAGE_LIMIT = 200
DEFAULT_PAGE_LIMIT = 50


class CaseRepository:
    """Encapsulates persistent querying and mutation for CaseModel."""

    def get_by_id(
        self, session: Session, case_id: str, load_relations: bool = True
    ) -> CaseModel | None:
        """Retrieve a case by ID, optionally eager-loading linked investigations."""
        stmt = select(CaseModel).where(CaseModel.id == case_id)
        if load_relations:
            stmt = stmt.options(selectinload(CaseModel.investigations))
        return session.execute(stmt).scalar_one_or_none()

    def create(self, session: Session, case: CaseModel) -> CaseModel:
        """Persist a new case record."""
        session.add(case)
        session.flush()
        return case

    def update(self, session: Session, case: CaseModel) -> CaseModel:
        """Save updates to an existing case."""
        case.updated_at = datetime.utcnow()
        session.flush()
        return case

    def list_cases(
        self,
        session: Session,
        limit: int = DEFAULT_PAGE_LIMIT,
        offset: int = 0,
        status: str | None = None,
        priority: str | None = None,
        owner: str | None = None,
    ) -> tuple[list[CaseModel], int]:
        """Retrieve bounded, filtered cases with total count."""
        safe_limit = max(1, min(limit, MAX_PAGE_LIMIT))
        safe_offset = max(0, offset)

        stmt = select(CaseModel).options(selectinload(CaseModel.investigations))
        count_stmt = select(func.count()).select_from(CaseModel)

        conditions = []
        if status:
            conditions.append(CaseModel.status == status)
        if priority:
            conditions.append(CaseModel.priority == priority)
        if owner:
            conditions.append(CaseModel.owner == owner)

        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        stmt = stmt.order_by(desc(CaseModel.created_at)).limit(safe_limit).offset(safe_offset)

        total_count = session.execute(count_stmt).scalar_one()
        items = list(session.execute(stmt).scalars().all())

        return items, total_count
