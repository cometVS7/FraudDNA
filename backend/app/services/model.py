"""FraudDNA Model Registry Application Service.

Encapsulates access to model metadata, deployment statuses, and operating thresholds.
"""

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.errors import NotFoundDomainError
from app.models.domain import ModelRegistryModel
from app.repositories.model_repository import ModelRegistryRepository

logger = logging.getLogger(__name__)


class ModelService:
    """Coordinates access to registered machine learning model versions."""

    def __init__(self, model_repo: ModelRegistryRepository | None = None) -> None:
        self.repo = model_repo or ModelRegistryRepository()

    def get_active_model(
        self, session: Session, model_type: str = "lightgbm"
    ) -> ModelRegistryModel:
        """Retrieve active production model or raise NotFoundDomainError."""
        model = self.repo.get_active_model(session, model_type=model_type)
        if not model:
            raise NotFoundDomainError(
                f"No active model registered for model family '{model_type}'.",
                details={"model_type": model_type},
            )
        return model

    def get_model_by_version(self, session: Session, version: str) -> ModelRegistryModel:
        """Retrieve specific model version or raise NotFoundDomainError."""
        model = self.repo.get_by_version(session, version)
        if not model:
            raise NotFoundDomainError(
                f"Model version '{version}' not found in registry.",
                details={"version": version},
            )
        return model

    def list_models(self, session: Session, status: str | None = None) -> list[dict[str, Any]]:
        """List registered models with metadata summary."""
        models = self.repo.list_models(session, status=status)
        return [
            {
                "id": m.id,
                "model_name": m.model_name,
                "version": m.version,
                "model_type": m.model_type,
                "status": m.status,
                "operating_threshold": m.operating_threshold,
                "feature_count": m.feature_count,
                "metrics": m.metrics,
                "created_at": m.created_at.isoformat(),
            }
            for m in models
        ]


_model_service_instance: ModelService | None = None


def get_model_service() -> ModelService:
    """Dependency provider for ModelService."""
    global _model_service_instance
    if _model_service_instance is None:
        _model_service_instance = ModelService()
    return _model_service_instance
