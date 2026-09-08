"""FraudDNA Risk Assessment Application Service.

Encapsulates persistent access to RiskAssessmentModel and RiskSignalModel (SHAP attributions).
"""

import logging

from sqlalchemy import desc, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NotFoundDomainError
from app.models.domain import RiskAssessmentModel

logger = logging.getLogger(__name__)


class RiskService:
    """Coordinates risk assessments and feature attribution signals."""

    def get_assessment(self, session: Session, assessment_id: str) -> RiskAssessmentModel:
        """Retrieve risk assessment with eager-loaded risk signals."""
        stmt = (
            select(RiskAssessmentModel)
            .where(RiskAssessmentModel.id == assessment_id)
            .options(selectinload(RiskAssessmentModel.risk_signals))
        )
        rec = session.execute(stmt).scalar_one_or_none()
        if not rec:
            raise NotFoundDomainError(
                f"Risk assessment '{assessment_id}' not found.",
                details={"assessment_id": assessment_id},
            )
        return rec

    def get_latest_for_transaction(
        self, session: Session, transaction_id: str
    ) -> RiskAssessmentModel | None:
        """Retrieve latest assessment for a transaction."""
        stmt = (
            select(RiskAssessmentModel)
            .where(RiskAssessmentModel.transaction_id == transaction_id)
            .options(selectinload(RiskAssessmentModel.risk_signals))
            .order_by(desc(RiskAssessmentModel.generated_at))
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()


_risk_service_instance: RiskService | None = None


def get_risk_service() -> RiskService:
    """Dependency provider for RiskService."""
    global _risk_service_instance
    if _risk_service_instance is None:
        _risk_service_instance = RiskService()
    return _risk_service_instance
