"""FraudDNA Case Management Application Service.

Encapsulates operational case lifecycle, triage priorities, valid state transitions,
and automatic audit event generation.
"""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.errors import NotFoundDomainError, ValidationDomainError
from app.models.domain import CaseModel
from app.repositories.case_repository import CaseRepository
from app.repositories.investigation_repository import InvestigationRepository
from app.schemas.case import (
    CaseCreateRequest,
    CaseListResponse,
    CaseResponse,
    CaseStatus,
    CaseStatusUpdateRequest,
)
from app.services.audit import AuditService, get_audit_service

logger = logging.getLogger(__name__)

VALID_CASE_TRANSITIONS: dict[str, set[str]] = {
    CaseStatus.NEW: {CaseStatus.IN_REVIEW, CaseStatus.CLOSED},
    CaseStatus.IN_REVIEW: {CaseStatus.ESCALATED, CaseStatus.RESOLVED, CaseStatus.CLOSED},
    CaseStatus.ESCALATED: {CaseStatus.IN_REVIEW, CaseStatus.RESOLVED, CaseStatus.CLOSED},
    CaseStatus.RESOLVED: {CaseStatus.CLOSED, CaseStatus.IN_REVIEW},
    CaseStatus.CLOSED: {CaseStatus.IN_REVIEW},  # Reopen capability
}


class CaseService:
    """Manages operational cases and enforces valid state transitions."""

    def __init__(
        self,
        case_repo: CaseRepository | None = None,
        investigation_repo: InvestigationRepository | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self.case_repo = case_repo or CaseRepository()
        self.investigation_repo = investigation_repo or InvestigationRepository()
        self.audit_service = audit_service or get_audit_service()

    def create_case(
        self,
        session: Session,
        request: CaseCreateRequest,
        actor: str = "analyst",
    ) -> CaseResponse:
        """Create a new case, optionally link an initial investigation, and log to audit."""
        case_id = f"case_{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC)

        case = CaseModel(
            id=case_id,
            title=request.title,
            status=CaseStatus.NEW.value,
            priority=request.priority.value,
            owner=request.owner,
            notes=request.notes,
            created_at=now,
            updated_at=now,
        )

        persisted = self.case_repo.create(session, case)

        investigation_ids: list[str] = []
        if request.investigation_id:
            inv = self.investigation_repo.get_by_id(session, request.investigation_id)
            if not inv:
                raise NotFoundDomainError(
                    f"Investigation '{request.investigation_id}' not found.",
                    details={"investigation_id": request.investigation_id},
                )
            inv.case_id = persisted.id
            investigation_ids.append(inv.id)

        # Audit event
        self.audit_service.record_event(
            session=session,
            actor=actor,
            actor_type="USER",
            event_type="CASE_CREATED",
            entity_type="case",
            entity_id=case_id,
            payload={
                "title": request.title,
                "priority": request.priority.value,
                "owner": request.owner,
                "investigation_id": request.investigation_id,
            },
            timestamp=now,
        )

        return self._to_response(persisted, investigation_ids)

    def get_case(self, session: Session, case_id: str) -> CaseResponse:
        """Retrieve case by ID or raise NotFoundDomainError."""
        case = self.case_repo.get_by_id(session, case_id)
        if not case:
            raise NotFoundDomainError(
                f"Case '{case_id}' not found.",
                details={"case_id": case_id},
            )
        inv_ids = [inv.id for inv in case.investigations] if case.investigations else []
        return self._to_response(case, inv_ids)

    def update_case_status(
        self,
        session: Session,
        case_id: str,
        request: CaseStatusUpdateRequest,
        actor: str = "analyst",
    ) -> CaseResponse:
        """Update case status enforcing valid state transition rules."""
        case = self.case_repo.get_by_id(session, case_id)
        if not case:
            raise NotFoundDomainError(
                f"Case '{case_id}' not found.",
                details={"case_id": case_id},
            )

        current_status = case.status
        target_status = request.status.value

        if current_status != target_status:
            allowed = VALID_CASE_TRANSITIONS.get(current_status, set())
            if target_status not in allowed:
                raise ValidationDomainError(
                    f"Invalid case status transition from '{current_status}' to '{target_status}'. "
                    f"Allowed transitions: {sorted(allowed)}",
                    details={
                        "current_status": current_status,
                        "target_status": target_status,
                        "allowed_transitions": sorted(allowed),
                    },
                )
            case.status = target_status

            now = datetime.now(UTC)
            if target_status == CaseStatus.CLOSED.value:
                case.closed_at = now
            elif current_status == CaseStatus.CLOSED.value:
                case.closed_at = None

        if request.notes:
            existing_notes = case.notes or ""
            timestamp_tag = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
            case.notes = f"{existing_notes}\n[{timestamp_tag} {actor}]: {request.notes}".strip()

        if request.owner is not None:
            case.owner = request.owner

        updated_case = self.case_repo.update(session, case)

        # Audit transition
        self.audit_service.record_event(
            session=session,
            actor=actor,
            actor_type="USER",
            event_type="CASE_STATUS_UPDATED",
            entity_type="case",
            entity_id=case_id,
            payload={
                "from_status": current_status,
                "to_status": target_status,
                "notes": request.notes,
                "owner": request.owner,
            },
        )

        inv_ids = (
            [inv.id for inv in updated_case.investigations] if updated_case.investigations else []
        )
        return self._to_response(updated_case, inv_ids)

    def link_investigation(
        self,
        session: Session,
        case_id: str,
        investigation_id: str,
        actor: str = "analyst",
    ) -> CaseResponse:
        """Associate an existing investigation with a case."""
        case = self.case_repo.get_by_id(session, case_id)
        if not case:
            raise NotFoundDomainError(f"Case '{case_id}' not found.", details={"case_id": case_id})

        inv = self.investigation_repo.get_by_id(session, investigation_id)
        if not inv:
            raise NotFoundDomainError(
                f"Investigation '{investigation_id}' not found.",
                details={"investigation_id": investigation_id},
            )

        inv.case_id = case.id
        session.flush()

        self.audit_service.record_event(
            session=session,
            actor=actor,
            actor_type="USER",
            event_type="INVESTIGATION_LINKED_TO_CASE",
            entity_type="case",
            entity_id=case_id,
            payload={"investigation_id": investigation_id},
        )

        return self.get_case(session, case_id)

    def list_cases(
        self,
        session: Session,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        priority: str | None = None,
        owner: str | None = None,
    ) -> CaseListResponse:
        """Query bounded, filtered cases."""
        items, total = self.case_repo.list_cases(
            session=session,
            limit=limit,
            offset=offset,
            status=status,
            priority=priority,
            owner=owner,
        )
        responses = [
            self._to_response(c, [inv.id for inv in c.investigations] if c.investigations else [])
            for c in items
        ]
        return CaseListResponse(
            items=responses,
            total_count=total,
            limit=limit,
            offset=offset,
        )

    def _to_response(self, case: CaseModel, investigation_ids: list[str]) -> CaseResponse:
        return CaseResponse(
            id=case.id,
            title=case.title,
            status=case.status,
            priority=case.priority,
            owner=case.owner,
            notes=case.notes,
            created_at=case.created_at,
            updated_at=case.updated_at,
            closed_at=case.closed_at,
            investigation_ids=investigation_ids,
        )


_case_service_instance: CaseService | None = None


def get_case_service() -> CaseService:
    """Dependency provider for CaseService."""
    global _case_service_instance
    if _case_service_instance is None:
        _case_service_instance = CaseService()
    return _case_service_instance
