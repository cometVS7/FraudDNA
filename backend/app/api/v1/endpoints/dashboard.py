"""FraudDNA Dashboard Overview API.

GET /api/v1/overview         - Dashboard overview metrics from actual data
GET /api/v1/transactions     - Paginated transactions list
GET /api/v1/transactions/{id} - Single transaction detail
GET /api/v1/evaluation       - Held-out ML evaluation metrics
GET /api/v1/audit            - Audit trail of investigations/decisions
"""

import json
import logging
from pathlib import Path
from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_sync_db
from app.graph.service import GraphService, get_graph_service
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.risk import RiskIntelligenceResponse
from app.services.risk_orchestrator import RiskOrchestrator, get_risk_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Dashboard"])


@router.get(
    "/overview",
    summary="Dashboard Overview",
    description="Aggregated overview metrics from actual transaction/graph data.",
)
async def get_overview(
    graph_service: GraphService = Depends(get_graph_service),
) -> dict[str, Any]:
    """Return overview metrics computed from the existing dataset and graph."""
    return graph_service.get_overview_metrics()


@router.get(
    "/transactions",
    summary="List Transactions",
    description="Paginated transaction list with risk scores, sorting, and filtering.",
)
async def list_transactions(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    sort_by: Annotated[str, Query()] = "risk_score",
    sort_order: Annotated[str, Query()] = "desc",
    risk_level: Annotated[str | None, Query()] = None,
    suspicious_only: Annotated[bool, Query()] = False,
    search: Annotated[str | None, Query()] = None,
    graph_service: GraphService = Depends(get_graph_service),
    db: Session = Depends(get_sync_db),
) -> dict[str, Any]:
    """Return paginated transactions with risk data."""
    if settings.ENABLE_PERSISTENT_STORAGE:
        try:
            tx_repo = TransactionRepository()
            risk_tier = risk_level.upper() if risk_level else None
            min_risk = 0.37 if suspicious_only else None
            customer_id = search if search and search.startswith("cust_") else None
            merchant_id = search if search and search.startswith("mer_") else None

            items, total = tx_repo.list_transactions(
                session=db,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                sort_order=sort_order,
                risk_tier=risk_tier,
                min_risk_score=min_risk,
                customer_id=customer_id,
                merchant_id=merchant_id,
            )

            results: list[dict[str, Any]] = []
            for tx in items:
                ip_addr = (
                    tx.ip.ip_address if tx.ip else (tx.ip_id.replace("ip_", "") if tx.ip_id else "")
                )
                results.append(
                    {
                        "transaction_id": tx.id,
                        "amount": float(tx.amount),
                        "timestamp": tx.timestamp.isoformat()
                        if hasattr(tx.timestamp, "isoformat")
                        else str(tx.timestamp),
                        "customer_id": tx.customer_id,
                        "merchant_id": tx.merchant_id,
                        "device_id": tx.device_id or "",
                        "ip_address": ip_addr,
                        "card_id": tx.card_id or "",
                        "risk_score": round(float(tx.risk_score), 4),
                        "risk_level": tx.risk_tier.lower(),
                        "is_fraud": tx.is_fraud,
                        "cluster_id": tx.network_id,
                    }
                )

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "transactions": results,
            }
        except Exception as exc:
            logger.warning(
                f"Persistent storage transaction lookup failed, falling back to in-memory: {exc}"
            )

    graph_service._ensure_initialized()
    transactions = list(graph_service.all_transactions)

    # Filtering
    if risk_level:
        transactions = [t for t in transactions if t["risk_level"] == risk_level]

    if suspicious_only:
        transactions = [t for t in transactions if t["risk_score"] >= 0.37]

    if search:
        q = search.lower()
        transactions = [
            t
            for t in transactions
            if q in t["transaction_id"].lower()
            or q in t["customer_id"].lower()
            or q in t["merchant_id"].lower()
        ]

    # Sorting
    reverse = sort_order == "desc"
    if sort_by in ("risk_score", "amount"):
        transactions.sort(key=lambda t: t.get(sort_by, 0), reverse=reverse)
    elif sort_by == "timestamp":
        transactions.sort(key=lambda t: t.get("timestamp", ""), reverse=reverse)
    else:
        transactions.sort(key=lambda t: t.get("risk_score", 0), reverse=reverse)

    total = len(transactions)
    paginated = transactions[offset : offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "transactions": paginated,
    }


@router.get(
    "/transactions/{transaction_id}",
    summary="Get Transaction Detail",
    description="Full transaction detail with risk information.",
)
async def get_transaction_detail(
    transaction_id: str,
    graph_service: GraphService = Depends(get_graph_service),
    db: Session = Depends(get_sync_db),
) -> dict[str, Any]:
    """Return detailed transaction data."""
    if settings.ENABLE_PERSISTENT_STORAGE:
        try:
            tx_repo = TransactionRepository()
            tx = tx_repo.get_by_id(db, transaction_id)
            if tx is not None:
                ip_addr = (
                    tx.ip.ip_address if tx.ip else (tx.ip_id.replace("ip_", "") if tx.ip_id else "")
                )
                return {
                    "transaction_id": tx.id,
                    "amount": float(tx.amount),
                    "timestamp": tx.timestamp.isoformat()
                    if hasattr(tx.timestamp, "isoformat")
                    else str(tx.timestamp),
                    "customer_id": tx.customer_id,
                    "merchant_id": tx.merchant_id,
                    "device_id": tx.device_id or "",
                    "ip_address": ip_addr,
                    "card_id": tx.card_id or "",
                    "risk_score": round(float(tx.risk_score), 4),
                    "risk_level": tx.risk_tier.lower(),
                    "is_fraud": tx.is_fraud,
                    "cluster_id": tx.network_id,
                }
        except Exception as exc:
            logger.warning(
                f"Persistent storage transaction detail lookup failed, falling back to in-memory: {exc}"
            )

    row = graph_service.get_transaction_row(transaction_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found.",
        )

    tx_node = f"transaction:{transaction_id}"
    score = 0.0
    if tx_node in graph_service.graph:
        score = float(graph_service.graph.nodes[tx_node].get("risk_score", 0.0))

    if score < 0.30:
        level = "low"
    elif score < 0.70:
        level = "medium"
    elif score < 0.90:
        level = "high"
    else:
        level = "critical"

    cluster_id = graph_service.tx_to_cluster.get(transaction_id)

    return {
        "transaction_id": transaction_id,
        "amount": float(row.get("amount", 0)),
        "timestamp": str(row.get("timestamp", "")),
        "customer_id": str(row.get("customer_id", "")),
        "merchant_id": str(row.get("merchant_id", "")),
        "device_id": str(row.get("device_id", "")),
        "ip_address": str(row.get("ip_address", "")),
        "card_id": str(row.get("card_id", "")),
        "risk_score": round(score, 4),
        "risk_level": level,
        "is_fraud": bool(row.get("is_fraud", 0)),
        "cluster_id": cluster_id,
    }


@router.get(
    "/transactions/{transaction_id}/risk-intelligence",
    response_model=RiskIntelligenceResponse,
    summary="Get Multi-Layer Risk Intelligence",
    description="Retrieve comprehensive 4-layer risk intelligence (Transaction, Entity, Network, Behavioral), composite risk, confidence, and structured explanations.",
)
async def get_transaction_risk_intelligence(
    transaction_id: str,
    persist: Annotated[
        bool, Query(description="Whether to persist composite risk updates")
    ] = False,
    db: Session = Depends(get_sync_db),
    risk_orchestrator: RiskOrchestrator = Depends(get_risk_orchestrator),
) -> RiskIntelligenceResponse:
    """Return synthesized multi-layer risk intelligence."""
    return risk_orchestrator.orchestrate_transaction_risk(
        session=db,
        transaction_id=transaction_id,
        persist_assessment=persist,
    )


@router.get(
    "/evaluation",
    summary="Model Evaluation Metrics",
    description="Held-out test set evaluation metrics from Phase 1.",
)
async def get_evaluation() -> dict[str, Any]:
    """Return persisted ML evaluation metrics."""
    metrics_path = Path("ml/evaluation/metrics.json")
    if not metrics_path.exists():
        metrics_path = Path("../ml/evaluation/metrics.json")
    if not metrics_path.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Evaluation metrics not available.",
        )

    with open(metrics_path) as f:
        metrics = json.load(f)

    return cast(dict[str, Any], metrics)


@router.get(
    "/graph/transaction/{transaction_id}",
    summary="Transaction Graph Data",
    description="Get graph subgraph data for React Flow visualization.",
)
async def get_transaction_graph(
    transaction_id: str,
    depth: Annotated[int, Query(ge=1, le=3)] = 2,
    graph_service: GraphService = Depends(get_graph_service),
) -> dict[str, Any]:
    """Return graph data for a transaction's neighborhood."""
    graph_data = graph_service.get_transaction_relationships(transaction_id, depth=depth)
    return graph_data.model_dump()


@router.get(
    "/graph/cluster/{cluster_id}",
    summary="Cluster Graph Data",
    description="Get graph subgraph data for a specific cluster.",
)
async def get_cluster_graph(
    cluster_id: str,
    graph_service: GraphService = Depends(get_graph_service),
) -> dict[str, Any]:
    """Return graph data for a cluster."""
    cluster = graph_service.get_cluster_by_id(cluster_id)
    if cluster is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster '{cluster_id}' not found.",
        )
    return cluster.graph_data.model_dump()
