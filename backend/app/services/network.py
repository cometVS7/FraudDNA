"""FraudDNA Network Application Service.

Encapsulates persistent access and analysis of RiskNetworkModel and fraud syndicate clusters.
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundDomainError
from app.models.domain import RiskNetworkModel

logger = logging.getLogger(__name__)


class NetworkService:
    """Coordinates risk network and fraud syndicate cluster persistence and lookups."""

    def get_network(self, session: Session, network_id: str) -> RiskNetworkModel:
        """Retrieve risk network by cluster/network ID."""
        stmt = select(RiskNetworkModel).where(RiskNetworkModel.id == network_id)
        network = session.execute(stmt).scalar_one_or_none()
        if not network:
            raise NotFoundDomainError(
                f"Risk network '{network_id}' not found.",
                details={"network_id": network_id},
            )
        return network

    def list_networks(
        self,
        session: Session,
        limit: int = 50,
        offset: int = 0,
        risk_level: str | None = None,
    ) -> tuple[list[RiskNetworkModel], int]:
        """Query bounded risk networks."""
        stmt = select(RiskNetworkModel)
        if risk_level:
            stmt = stmt.where(RiskNetworkModel.risk_level == risk_level)
        stmt = stmt.limit(limit).offset(offset)
        items = list(session.execute(stmt).scalars().all())
        return items, len(items)


_network_service_instance: NetworkService | None = None


def get_network_service() -> NetworkService:
    """Dependency provider for NetworkService."""
    global _network_service_instance
    if _network_service_instance is None:
        _network_service_instance = NetworkService()
    return _network_service_instance
