"""FraudDNA Investigation Repository.

Provides persistent access and mutation for InvestigationModel, EvidenceModel, and AIFindingModel.
"""

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.domain import InvestigationModel

MAX_PAGE_LIMIT = 200
DEFAULT_PAGE_LIMIT = 50


class InvestigationRepository:
    """Encapsulates persistent queries and storage for investigation records."""

    def get_by_id(
        self, session: Session, investigation_id: str, load_relations: bool = True
    ) -> InvestigationModel | None:
        """Retrieve investigation record by ID."""
        stmt = select(InvestigationModel).where(InvestigationModel.id == investigation_id)
        if load_relations:
            stmt = stmt.options(
                selectinload(InvestigationModel.evidence_items),
                selectinload(InvestigationModel.ai_findings),
            )
        return session.execute(stmt).scalar_one_or_none()

    def get_by_transaction_id(
        self, session: Session, transaction_id: str, load_relations: bool = True
    ) -> InvestigationModel | None:
        """Retrieve investigation associated with a specific primary transaction."""
        stmt = select(InvestigationModel).where(
            InvestigationModel.primary_transaction_id == transaction_id
        )
        if load_relations:
            stmt = stmt.options(
                selectinload(InvestigationModel.evidence_items),
                selectinload(InvestigationModel.ai_findings),
            )
        return session.execute(stmt).scalar_one_or_none()

    def create(self, session: Session, investigation: InvestigationModel) -> InvestigationModel:
        """Persist a new investigation record."""
        session.add(investigation)
        session.flush()
        return investigation

    def list_investigations(
        self,
        session: Session,
        limit: int = DEFAULT_PAGE_LIMIT,
        offset: int = 0,
        status: str | None = None,
        priority: str | None = None,
        risk_level: str | None = None,
    ) -> tuple[list[InvestigationModel], int]:
        """Retrieve bounded, filtered investigations with total count."""
        safe_limit = max(1, min(limit, MAX_PAGE_LIMIT))
        safe_offset = max(0, offset)

        stmt = select(InvestigationModel).options(
            selectinload(InvestigationModel.evidence_items),
            selectinload(InvestigationModel.ai_findings),
        )
        count_stmt = select(func.count()).select_from(InvestigationModel)

        conditions = []
        if status:
            conditions.append(InvestigationModel.status == status)
        if priority:
            conditions.append(InvestigationModel.priority == priority)
        if risk_level:
            conditions.append(InvestigationModel.risk_level == risk_level)

        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        stmt = (
            stmt.order_by(desc(InvestigationModel.created_at)).limit(safe_limit).offset(safe_offset)
        )

        total_count = session.execute(count_stmt).scalar_one()
        items = list(session.execute(stmt).scalars().all())

        return items, total_count
