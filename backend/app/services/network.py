"""FraudDNA Network Application Service.

Encapsulates persistent access and analysis of RiskNetworkModel and fraud syndicate clusters.
"""

import logging

from sqlalchemy.orm import Session

from app.core.errors import NotFoundDomainError
from app.models.domain import RiskNetworkModel
from app.repositories.network_repository import NetworkRepository

logger = logging.getLogger(__name__)


class NetworkService:
    """Coordinates risk network and fraud syndicate cluster persistence and lookups."""

    def __init__(self, repo: NetworkRepository | None = None) -> None:
        self.repo = repo or NetworkRepository()

    def get_network(
        self, session: Session, network_id: str, load_transactions: bool = False
    ) -> RiskNetworkModel:
        """Retrieve risk network by cluster/network ID."""
        network = self.repo.get_by_id(session, network_id, load_transactions=load_transactions)
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
        is_suspicious: bool | None = None,
        min_risk_score: float | None = None,
    ) -> tuple[list[RiskNetworkModel], int]:
        """Query bounded risk networks."""
        return self.repo.list_networks(
            session=session,
            limit=limit,
            offset=offset,
            is_suspicious=is_suspicious,
            min_risk_score=min_risk_score,
        )


_network_service_instance: NetworkService | None = None


def get_network_service() -> NetworkService:
    """Dependency provider for NetworkService."""
    global _network_service_instance
    if _network_service_instance is None:
        _network_service_instance = NetworkService()
    return _network_service_instance
