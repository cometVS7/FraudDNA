"""FraudDNA Clusters API Endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.graph.service import GraphService, get_graph_service
from app.schemas.cluster import ClusterDetail, ClusterListResponse

router = APIRouter(prefix="/clusters", tags=["FraudDNA Clusters"])


@router.get(
    "",
    response_model=ClusterListResponse,
    summary="List Detected Fraud Clusters",
    description="Retrieve paginated list of detected fraud clusters and coordinated abuse networks.",
)
async def list_clusters(
    min_risk: Annotated[
        float,
        Query(ge=0.0, le=1.0, description="Filter clusters with minimum risk score"),
    ] = 0.0,
    suspicious_only: Annotated[
        bool,
        Query(description="Filter only clusters flagged as suspicious"),
    ] = False,
    limit: Annotated[
        int,
        Query(ge=1, le=200, description="Maximum number of clusters to return"),
    ] = 50,
    offset: Annotated[
        int,
        Query(ge=0, description="Pagination offset index"),
    ] = 0,
    sort_by: Annotated[
        str,
        Query(description="Sort field: 'risk_score', 'transaction_count', or 'amount'"),
    ] = "risk_score",
    graph_service: GraphService = Depends(get_graph_service),
) -> ClusterListResponse:
    """Return paginated list of fraud clusters."""
    return graph_service.get_clusters(
        min_risk=min_risk,
        suspicious_only=suspicious_only,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
    )


@router.get(
    "/{cluster_id}",
    response_model=ClusterDetail,
    summary="Get Cluster Details",
    description="Retrieve comprehensive details, entity subgraph, and risk explanation for a specific cluster.",
)
async def get_cluster_detail(
    cluster_id: str,
    graph_service: GraphService = Depends(get_graph_service),
) -> ClusterDetail:
    """Return full details and subgraph for a specific cluster."""
    cluster = graph_service.get_cluster_by_id(cluster_id)
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster with ID '{cluster_id}' not found.",
        )
    return cluster
