"""FraudDNA Evidence Application Service.

Encapsulates persistent, attributable evidence storage and retrieval.
"""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundDomainError
from app.models.domain import EvidenceModel

logger = logging.getLogger(__name__)


class EvidenceService:
    """Manages attributable, verifiable evidence linked to investigations and cases."""

    def record_evidence(
        self,
        session: Session,
        evidence_type: str,
        source: str,
        description: str,
        severity: str = "LOW",
        confidence: float = 1.0,
        source_id: str | None = None,
        investigation_id: str | None = None,
        case_id: str | None = None,
    ) -> EvidenceModel:
        """Persist an attributable evidence item."""
        ev_id = f"ev_{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC)

        ev = EvidenceModel(
            id=ev_id,
            investigation_id=investigation_id,
            case_id=case_id,
            evidence_type=evidence_type,
            source=source,
            source_id=source_id,
            description=description,
            severity=severity.upper(),
            confidence=max(0.0, min(confidence, 1.0)),
            timestamp=now,
        )
        session.add(ev)
        session.flush()
        return ev

    def get_evidence(self, session: Session, evidence_id: str) -> EvidenceModel:
        """Retrieve evidence item by ID."""
        stmt = select(EvidenceModel).where(EvidenceModel.id == evidence_id)
        ev = session.execute(stmt).scalar_one_or_none()
        if not ev:
            raise NotFoundDomainError(
                f"Evidence '{evidence_id}' not found.",
                details={"evidence_id": evidence_id},
            )
        return ev

    def list_for_investigation(
        self, session: Session, investigation_id: str
    ) -> list[EvidenceModel]:
        """Retrieve all evidence items bound to an investigation."""
        stmt = select(EvidenceModel).where(EvidenceModel.investigation_id == investigation_id)
        return list(session.execute(stmt).scalars().all())


_evidence_service_instance: EvidenceService | None = None


def get_evidence_service() -> EvidenceService:
    """Dependency provider for EvidenceService."""
    global _evidence_service_instance
    if _evidence_service_instance is None:
        _evidence_service_instance = EvidenceService()
    return _evidence_service_instance
