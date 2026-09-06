"""FraudDNA Model Registry Repository.

Provides persistent access to ML model metadata, thresholds, and registry versions.
"""

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.domain import ModelRegistryModel


class ModelRegistryRepository:
    """Encapsulates queries for ModelRegistryModel."""

    def get_active_model(
        self, session: Session, model_type: str = "lightgbm"
    ) -> ModelRegistryModel | None:
        """Retrieve the currently active model for the given model family."""
        stmt = (
            select(ModelRegistryModel)
            .where(
                ModelRegistryModel.status == "ACTIVE",
                ModelRegistryModel.model_type == model_type,
            )
            .order_by(desc(ModelRegistryModel.created_at))
            .limit(1)
        )
        return session.execute(stmt).scalar_one_or_none()

    def get_by_version(self, session: Session, version: str) -> ModelRegistryModel | None:
        """Retrieve model metadata by explicit version identifier."""
        stmt = select(ModelRegistryModel).where(ModelRegistryModel.version == version)
        return session.execute(stmt).scalar_one_or_none()

    def list_models(self, session: Session, status: str | None = None) -> list[ModelRegistryModel]:
        """Retrieve all registered models, optionally filtered by status."""
        stmt = select(ModelRegistryModel)
        if status:
            stmt = stmt.where(ModelRegistryModel.status == status)
        stmt = stmt.order_by(desc(ModelRegistryModel.created_at))
        return list(session.execute(stmt).scalars().all())
