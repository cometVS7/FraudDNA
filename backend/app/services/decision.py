"""FraudDNA Decision Application Service.

Encapsulates deterministic financial policy evaluation, decision persistence,
and audit record creation. Preserves the authoritative ALLOW / REVIEW / HOLD vocabulary.
"""

import logging
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import NotFoundDomainError
from app.models.domain import DecisionModel
from app.policy.models import PolicyDecision
from app.repositories.decision_repository import DecisionRepository
from app.schemas.decision import DecisionListResponse, DecisionRecordResponse
from app.services.audit import AuditService, get_audit_service

if TYPE_CHECKING:
    from app.policy.engine import PolicyEngine

logger = logging.getLogger(__name__)


class DecisionService:
    """Coordinates deterministic financial decision evaluation and persistence."""

    def __init__(
        self,
        policy_engine: "PolicyEngine | None" = None,
        decision_repo: DecisionRepository | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        if policy_engine is None:
            from app.policy.engine import PolicyEngine

            self.policy_engine = PolicyEngine()
        else:
            self.policy_engine = policy_engine
        self.decision_repo = decision_repo or DecisionRepository()
        self.audit_service = audit_service or get_audit_service()

    def evaluate_and_persist(
        self,
        session: Session,
        transaction_id: str,
        risk_score_override: float | None = None,
        actor: str = "policy_engine",
    ) -> PolicyDecision:
        """Evaluate deterministic policy and persist the decision record and audit log."""
        decision = self.policy_engine.evaluate_transaction(
            transaction_id=transaction_id,
            risk_score_override=risk_score_override,
        )

        decision_model = DecisionModel(
            id=decision.decision_id,
            transaction_id=transaction_id,
            policy_id=f"pol_{settings.POLICY_VERSION}",
            policy_version=decision.policy_version,
            action=decision.action.value,  # Authoritative "ALLOW", "REVIEW", or "HOLD"
            reason_codes=[rc.value for rc in decision.reason_codes],
            evidence_summary=decision.evidence_summary,
            is_deterministic=True,
            generated_at=decision.created_at,
        )

        self.decision_repo.create(session, decision_model)

        # Append audit event
        self.audit_service.record_event(
            session=session,
            actor=actor,
            actor_type="SERVICE",
            event_type="POLICY_DECISION_GENERATED",
            entity_type="transaction",
            entity_id=transaction_id,
            payload={
                "decision_id": decision.decision_id,
                "action": decision.action.value,
                "policy_version": decision.policy_version,
                "reason_codes": [rc.value for rc in decision.reason_codes],
                "risk_score": decision.risk_score,
            },
            timestamp=decision.created_at,
        )

        return decision

    def get_decision(self, session: Session, decision_id: str) -> DecisionRecordResponse:
        """Retrieve persisted decision by ID."""
        rec = self.decision_repo.get_by_id(session, decision_id)
        if not rec:
            raise NotFoundDomainError(
                f"Decision '{decision_id}' not found.",
                details={"decision_id": decision_id},
            )
        return DecisionRecordResponse.model_validate(rec)

    def get_decision_by_transaction(
        self, session: Session, transaction_id: str
    ) -> DecisionRecordResponse:
        """Retrieve most recent decision for a transaction."""
        rec = self.decision_repo.get_by_transaction_id(session, transaction_id)
        if not rec:
            raise NotFoundDomainError(
                f"No decision found for transaction '{transaction_id}'.",
                details={"transaction_id": transaction_id},
            )
        return DecisionRecordResponse.model_validate(rec)

    def list_decisions(
        self,
        session: Session,
        limit: int = 50,
        offset: int = 0,
        action: str | None = None,
        policy_id: str | None = None,
    ) -> DecisionListResponse:
        """Retrieve bounded, paginated decisions."""
        items, total = self.decision_repo.list_decisions(
            session=session,
            limit=limit,
            offset=offset,
            action=action,
            policy_id=policy_id,
        )
        return DecisionListResponse(
            items=[DecisionRecordResponse.model_validate(it) for it in items],
            total_count=total,
            limit=limit,
            offset=offset,
        )


_decision_service_instance: DecisionService | None = None


def get_decision_service() -> DecisionService:
    """Dependency provider for DecisionService."""
    global _decision_service_instance
    if _decision_service_instance is None:
        _decision_service_instance = DecisionService()
    return _decision_service_instance
