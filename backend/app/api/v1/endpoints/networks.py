"""FraudDNA Risk Network Intelligence Endpoints.

GET /api/v1/networks/{network_id} - Detailed risk network profile and explanation
GET /api/v1/networks/{network_id}/members - Member entities grouped by type
GET /api/v1/networks/{network_id}/transactions - Bounded member transactions
GET /api/v1/networks/{network_id}/graph - Database-backed React Flow subgraph
GET /api/v1/networks/{network_id}/intelligence - Comprehensive V2-07 network intelligence profile
GET /api/v1/networks/{network_id}/paths - High-risk narrative traversal paths
GET /api/v1/networks/{network_id}/timeline - Temporal progression and burst analysis
GET /api/v1/networks/{network_id}/exposure - Financial & entity exposure breakdown
GET /api/v1/networks/{network_id}/patterns - Detected syndicate topology patterns
GET /api/v1/networks/{network_id}/findings - Machine-readable evidence findings
POST /api/v1/networks/paths/search - Bounded multi-hop pathfinding between two entities
"""

from datetime import datetime
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
from app.schemas.network_intelligence import (
    NetworkExposure,
    NetworkFinding,
    NetworkIntelligenceResponse,
    NetworkPath,
    NetworkTimeline,
    PathSearchRequest,
    PathSearchResponse,
    SyndicatePattern,
)
from app.services.network import NetworkService, get_network_service
from app.services.network_intelligence import (
    NetworkIntelligenceService,
    get_network_intelligence_service,
)

router = APIRouter(prefix="/networks", tags=["Networks"])


@router.post(
    "/paths/search",
    response_model=PathSearchResponse,
    summary="Search Paths Between Entities",
    description="Find bounded, ranked graph paths connecting two specific entities.",
)
def search_paths(
    payload: PathSearchRequest,
    db: Session = Depends(get_sync_db),
    net_intel_service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
) -> PathSearchResponse:
    """Find bounded, ranked paths connecting two entities."""
    return net_intel_service.find_paths_between_entities(
        session=db,
        source_id=payload.source_id,
        target_id=payload.target_id,
        source_type=payload.source_type,
        target_type=payload.target_type,
        max_depth=payload.max_depth,
        max_paths=payload.max_paths,
    )


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
    "/{network_id}/intelligence",
    response_model=NetworkIntelligenceResponse,
    summary="Get Full Network Intelligence Profile",
    description="Retrieve complete V2-07 Risk Network Intelligence assessment including exposure, topology, patterns, timeline, and findings.",
)
def get_network_intelligence(
    network_id: str,
    as_of: Annotated[
        datetime | None,
        Query(description="Point-in-time evaluation timestamp (UTC)"),
    ] = None,
    max_nodes: Annotated[
        int, Query(ge=5, le=250, description="Max nodes for graph analysis")
    ] = 100,
    max_transactions: Annotated[
        int, Query(ge=5, le=250, description="Max transactions to analyze")
    ] = 100,
    db: Session = Depends(get_sync_db),
    net_intel_service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
) -> NetworkIntelligenceResponse:
    """Retrieve complete network intelligence profile."""
    return net_intel_service.get_network_intelligence(
        session=db,
        network_id=network_id,
        as_of=as_of,
        max_nodes=max_nodes,
        max_transactions=max_transactions,
    )


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


@router.get(
    "/{network_id}/paths",
    response_model=list[NetworkPath],
    summary="Get Network Traversal Paths",
    description="Retrieve bounded, ranked entity paths within the network.",
)
def get_network_paths(
    network_id: str,
    max_paths: Annotated[int, Query(ge=1, le=25, description="Max paths to return")] = 10,
    max_depth: Annotated[int, Query(ge=1, le=3, description="Max search depth")] = 3,
    db: Session = Depends(get_sync_db),
    net_intel_service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
) -> list[NetworkPath]:
    """Retrieve ranked paths within the network."""
    return net_intel_service.get_network_paths(
        session=db,
        network_id=network_id,
        max_paths=max_paths,
        max_depth=max_depth,
    )


@router.get(
    "/{network_id}/timeline",
    response_model=NetworkTimeline,
    summary="Get Network Temporal Progression",
    description="Retrieve network timeline and temporal burst activity.",
)
def get_network_timeline(
    network_id: str,
    as_of: Annotated[
        datetime | None,
        Query(description="Point-in-time evaluation timestamp (UTC)"),
    ] = None,
    db: Session = Depends(get_sync_db),
    net_intel_service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
) -> NetworkTimeline:
    """Retrieve network temporal timeline."""
    return net_intel_service.get_network_timeline(session=db, network_id=network_id, as_of=as_of)


@router.get(
    "/{network_id}/exposure",
    response_model=NetworkExposure,
    summary="Get Network Financial & Entity Exposure",
    description="Retrieve exposure metrics and observed vs inferred values.",
)
def get_network_exposure(
    network_id: str,
    as_of: Annotated[
        datetime | None,
        Query(description="Point-in-time evaluation timestamp (UTC)"),
    ] = None,
    db: Session = Depends(get_sync_db),
    net_intel_service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
) -> NetworkExposure:
    """Retrieve network financial and entity exposure."""
    return net_intel_service.get_network_exposure(session=db, network_id=network_id, as_of=as_of)


@router.get(
    "/{network_id}/patterns",
    response_model=list[SyndicatePattern],
    summary="Get Detected Syndicate Patterns",
    description="Retrieve deterministic syndicate topology patterns detected for the network.",
)
def get_network_patterns(
    network_id: str,
    as_of: Annotated[
        datetime | None,
        Query(description="Point-in-time evaluation timestamp (UTC)"),
    ] = None,
    db: Session = Depends(get_sync_db),
    net_intel_service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
) -> list[SyndicatePattern]:
    """Retrieve detected syndicate patterns."""
    return net_intel_service.get_network_patterns(session=db, network_id=network_id, as_of=as_of)


@router.get(
    "/{network_id}/findings",
    response_model=list[NetworkFinding],
    summary="Get Network Evidence Findings",
    description="Retrieve structured, machine-readable network findings for investigation grounding.",
)
def get_network_findings(
    network_id: str,
    as_of: Annotated[
        datetime | None,
        Query(description="Point-in-time evaluation timestamp (UTC)"),
    ] = None,
    db: Session = Depends(get_sync_db),
    net_intel_service: NetworkIntelligenceService = Depends(get_network_intelligence_service),
) -> list[NetworkFinding]:
    """Retrieve structured network findings."""
    return net_intel_service.get_network_findings(session=db, network_id=network_id, as_of=as_of)
