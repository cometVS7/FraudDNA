"""FraudDNA Risk Network Intelligence Endpoints.

GET /api/v1/networks/{network_id} - Detailed risk network profile and explanation
GET /api/v1/networks/{network_id}/members - Member entities grouped by type
GET /api/v1/networks/{network_id}/transactions - Bounded member transactions
GET /api/v1/networks/{network_id}/graph - Database-backed React Flow subgraph
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_sync_db
from app.schemas.cluster import (
    ClusterDetail,
    NetworkMembersResponse,
    NetworkTransactionsResponse,
)
from app.schemas.graph import GraphData
from app.services.network import NetworkService, get_network_service

router = APIRouter(prefix="/networks", tags=["Networks"])


@router.get(
    "/{network_id}",
    response_model=ClusterDetail,
    summary="Get Network Details",
    description="Retrieve comprehensive risk network profile, member entities, and risk factors.",
)
def get_network_detail(
    network_id: str,
    db: Session = Depends(get_sync_db),
    network_service: NetworkService = Depends(get_network_service),
) -> ClusterDetail:
    """Retrieve full cluster and network details."""
    return network_service.get_network_detail(db, network_id)


@router.get(
    "/{network_id}/members",
    response_model=NetworkMembersResponse,
    summary="Get Network Member Entities",
    description="Retrieve all member entity IDs involved in the risk network grouped by entity category.",
)
def get_network_members(
    network_id: str,
    db: Session = Depends(get_sync_db),
    network_service: NetworkService = Depends(get_network_service),
) -> NetworkMembersResponse:
    """Retrieve member entities of the risk network."""
    return network_service.get_network_members(db, network_id)


@router.get(
    "/{network_id}/transactions",
    response_model=NetworkTransactionsResponse,
    summary="Get Network Transactions",
    description="Retrieve bounded, paginated transactions belonging to the risk network.",
)
def get_network_transactions(
    network_id: str,
    limit: Annotated[int, Query(ge=1, le=250, description="Page size limit")] = 50,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
    db: Session = Depends(get_sync_db),
    network_service: NetworkService = Depends(get_network_service),
) -> NetworkTransactionsResponse:
    """Retrieve paginated member transactions."""
    return network_service.get_network_transactions(
        session=db,
        network_id=network_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{network_id}/graph",
    response_model=GraphData,
    summary="Get Network Subgraph",
    description="Retrieve bounded, deterministic React Flow graph data for the risk network.",
)
def get_network_graph(
    network_id: str,
    max_nodes: Annotated[int, Query(ge=5, le=250, description="Maximum nodes in graph")] = 100,
    max_transactions: Annotated[
        int, Query(ge=5, le=250, description="Maximum transactions to traverse")
    ] = 100,
    db: Session = Depends(get_sync_db),
    network_service: NetworkService = Depends(get_network_service),
) -> GraphData:
    """Retrieve bounded network subgraph for visualization."""
    return network_service.get_network_graph(
        session=db,
        network_id=network_id,
        max_nodes=max_nodes,
        max_transactions=max_transactions,
    )
