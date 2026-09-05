"""FraudDNA Dashboard Overview API.

GET /api/v1/overview         - Dashboard overview metrics from actual data
GET /api/v1/transactions     - Paginated transactions list
GET /api/v1/transactions/{id} - Single transaction detail
GET /api/v1/evaluation       - Held-out ML evaluation metrics
GET /api/v1/audit            - Audit trail of investigations/decisions
"""

import json
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.graph.service import GraphService, get_graph_service

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
    graph_service.initialize()

    df = graph_service.df
    if df is None:
        return {"error": "Dataset not loaded", "status": "degraded"}

    total_txns = len(df)
    fraud_count = int(df["is_fraud"].sum()) if "is_fraud" in df.columns else 0
    legit_count = total_txns - fraud_count
    fraud_rate = round(fraud_count / total_txns, 4) if total_txns > 0 else 0.0

    # Amounts
    total_amount = round(float(df["amount"].sum()), 2) if "amount" in df.columns else 0.0
    fraud_amount = 0.0
    if "is_fraud" in df.columns and "amount" in df.columns:
        fraud_amount = round(float(df.loc[df["is_fraud"] == 1, "amount"].sum()), 2)

    # Risk score distribution from graph
    risk_scores: list[float] = []
    suspicious_count = 0
    high_risk_count = 0
    critical_count = 0
    for tx_id, _tx_data in graph_service.transactions_by_id.items():
        tx_node = f"transaction:{tx_id}"
        if tx_node in graph_service.graph:
            score = float(graph_service.graph.nodes[tx_node].get("risk_score", 0.0))
        else:
            score = 0.0
        risk_scores.append(score)
        if score >= 0.37:
            suspicious_count += 1
        if score >= 0.70:
            high_risk_count += 1
        if score >= 0.90:
            critical_count += 1

    # Cluster summary
    total_clusters = len(graph_service.clusters)
    suspicious_clusters = sum(1 for c in graph_service.clusters if c.is_suspicious)

    # Risk distribution bins
    distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for s in risk_scores:
        if s < 0.30:
            distribution["low"] += 1
        elif s < 0.70:
            distribution["medium"] += 1
        elif s < 0.90:
            distribution["high"] += 1
        else:
            distribution["critical"] += 1

    return {
        "total_transactions": total_txns,
        "fraud_count": fraud_count,
        "legitimate_count": legit_count,
        "fraud_rate": fraud_rate,
        "total_amount": total_amount,
        "fraud_exposure": fraud_amount,
        "suspicious_transactions": suspicious_count,
        "high_risk_count": high_risk_count,
        "critical_risk_count": critical_count,
        "total_clusters": total_clusters,
        "suspicious_clusters": suspicious_clusters,
        "risk_distribution": distribution,
        "data_label": "synthetic_dataset",
    }


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
) -> dict[str, Any]:
    """Return paginated transactions with risk data."""
    graph_service.initialize()

    transactions: list[dict[str, Any]] = []
    for tx_id, row in graph_service.transactions_by_id.items():
        tx_node = f"transaction:{tx_id}"
        score = 0.0
        if tx_node in graph_service.graph:
            score = float(graph_service.graph.nodes[tx_node].get("risk_score", 0.0))

        # Risk level
        if score < 0.30:
            level = "low"
        elif score < 0.70:
            level = "medium"
        elif score < 0.90:
            level = "high"
        else:
            level = "critical"

        is_fraud = bool(row.get("is_fraud", 0))
        cluster_id = graph_service.tx_to_cluster.get(tx_id)

        entry = {
            "transaction_id": tx_id,
            "amount": float(row.get("amount", 0)),
            "timestamp": str(row.get("timestamp", "")),
            "customer_id": str(row.get("customer_id", "")),
            "merchant_id": str(row.get("merchant_id", "")),
            "device_id": str(row.get("device_id", "")),
            "ip_address": str(row.get("ip_address", "")),
            "card_id": str(row.get("card_id", "")),
            "risk_score": round(score, 4),
            "risk_level": level,
            "is_fraud": is_fraud,
            "cluster_id": cluster_id,
        }
        transactions.append(entry)

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
) -> dict[str, Any]:
    """Return detailed transaction data."""
    graph_service.initialize()
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

    return metrics


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
    graph_service.initialize()
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
    graph_service.initialize()
    cluster = graph_service.get_cluster_by_id(cluster_id)
    if cluster is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster '{cluster_id}' not found.",
        )
    return cluster.graph_data.model_dump()
