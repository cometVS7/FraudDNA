"""FraudDNA Audit Repository.

Provides append-only persistence and query capabilities for AuditEventModel.
"""

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.domain import AuditEventModel

MAX_PAGE_LIMIT = 200
DEFAULT_PAGE_LIMIT = 50


class AuditRepository:
    """Encapsulates append-only queries and storage for audit trail events."""

    def get_latest_event(self, session: Session) -> AuditEventModel | None:
        """Retrieve the most recent audit event to obtain the current hash chain tip."""
        stmt = (
            select(AuditEventModel)
            .order_by(desc(AuditEventModel.timestamp), desc(AuditEventModel.id))
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()

    def create(self, session: Session, audit_event: AuditEventModel) -> AuditEventModel:
        """Append a new audit event to the immutable ledger."""
        session.add(audit_event)
        session.flush()
        return audit_event

    def get_by_id(self, session: Session, event_id: str) -> AuditEventModel | None:
        """Retrieve a specific audit event by ID."""
        stmt = select(AuditEventModel).where(AuditEventModel.id == event_id)
        return session.execute(stmt).scalar_one_or_none()

    def list_events(
        self,
        session: Session,
        limit: int = DEFAULT_PAGE_LIMIT,
        offset: int = 0,
        entity_type: str | None = None,
        entity_id: str | None = None,
        event_type: str | None = None,
        actor: str | None = None,
    ) -> tuple[list[AuditEventModel], int]:
        """Retrieve bounded, filtered audit events with total count."""
        safe_limit = max(1, min(limit, MAX_PAGE_LIMIT))
        safe_offset = max(0, offset)

        stmt = select(AuditEventModel)
        count_stmt = select(func.count()).select_from(AuditEventModel)

        conditions = []
        if entity_type:
            conditions.append(AuditEventModel.entity_type == entity_type)
        if entity_id:
            conditions.append(AuditEventModel.entity_id == entity_id)
        if event_type:
            conditions.append(AuditEventModel.event_type == event_type)
        if actor:
            conditions.append(AuditEventModel.actor == actor)

        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        stmt = (
            stmt.order_by(desc(AuditEventModel.timestamp), desc(AuditEventModel.id))
            .limit(safe_limit)
            .offset(safe_offset)
        )

        total_count = session.execute(count_stmt).scalar_one()
        items = list(session.execute(stmt).scalars().all())

        return items, total_count

    def get_all_ordered_ascending(self, session: Session) -> list[AuditEventModel]:
        """Retrieve all audit events in ascending chronological order for hash chain verification."""
        stmt = select(AuditEventModel).order_by(
            AuditEventModel.timestamp.asc(), AuditEventModel.id.asc()
        )
        return list(session.execute(stmt).scalars().all())
