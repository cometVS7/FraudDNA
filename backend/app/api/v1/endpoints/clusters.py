"""FraudDNA Clusters API Endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_sync_db
from app.core.errors import NotFoundDomainError
from app.graph.service import GraphService, get_graph_service
from app.schemas.cluster import ClusterDetail, ClusterListResponse, ClusterSummary
from app.services.network import NetworkService, get_network_service

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
    db: Session = Depends(get_sync_db),
    network_service: NetworkService = Depends(get_network_service),
    graph_service: GraphService = Depends(get_graph_service),
) -> ClusterListResponse:
    """Return paginated list of fraud clusters."""
    if settings.ENABLE_PERSISTENT_STORAGE:
        try:
            networks, total = network_service.list_networks(
                session=db,
                limit=limit,
                offset=offset,
                is_suspicious=True if suspicious_only else None,
                min_risk_score=min_risk if min_risk > 0 else None,
            )
            if total > 0:
                summaries = [
                    ClusterSummary(
                        cluster_id=n.id,
                        cluster_risk_score=float(n.risk_score),
                        is_suspicious=n.is_suspicious,
                        transaction_count=n.transaction_count,
                        customer_count=n.customer_count,
                        device_count=n.device_count,
                        ip_count=n.ip_count,
                        card_count=n.card_count,
                        merchant_count=n.merchant_count,
                        suspicious_transaction_count=n.transaction_count if n.is_suspicious else 0,
                        total_transaction_amount=float(n.total_amount),
                        suspicious_transaction_amount=float(n.total_amount)
                        if n.is_suspicious
                        else 0.0,
                        primary_reason=n.primary_reason or "Detected risk network",
                    )
                    for n in networks
                ]
                return ClusterListResponse(
                    total_clusters=total,
                    limit=limit,
                    offset=offset,
                    clusters=summaries,
                )
        except Exception:
            pass

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
    db: Session = Depends(get_sync_db),
    network_service: NetworkService = Depends(get_network_service),
    graph_service: GraphService = Depends(get_graph_service),
) -> ClusterDetail:
    """Return full details and subgraph for a specific cluster."""
    if settings.ENABLE_PERSISTENT_STORAGE:
        try:
            return network_service.get_network_detail(db, cluster_id)
        except NotFoundDomainError:
            pass

    cluster = graph_service.get_cluster_by_id(cluster_id)
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster with ID '{cluster_id}' not found.",
        )
    return cluster
