"""Fraud Cluster Data Schemas for API and Investigation Views."""

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.graph import GraphData


class ClusterRiskFactor(BaseModel):
    """Structured breakdown of why a cluster is scored as suspicious."""

    factor_type: str = Field(
        ..., description="Machine-readable factor code (e.g. SHARED_DEVICE_COLLUSION)"
    )
    description: str = Field(..., description="Human-readable explanation of the risk signal")
    severity: str = Field(
        default="MEDIUM", description="Severity level: LOW, MEDIUM, HIGH, CRITICAL"
    )
    weight: float = Field(..., description="Contribution weight to cluster risk score [0.0 - 1.0]")


class ClusterSummary(BaseModel):
    """Summary of a detected fraud/abuse cluster."""

    cluster_id: str = Field(..., description="Deterministic unique cluster identifier")
    cluster_risk_score: float = Field(..., description="Overall cluster risk score [0.0 - 1.0]")
    is_suspicious: bool = Field(
        ..., description="Whether cluster exceeds the suspicious risk threshold"
    )
    transaction_count: int = Field(..., description="Total transactions in the cluster")
    customer_count: int = Field(..., description="Distinct customer accounts involved")
    device_count: int = Field(..., description="Distinct devices involved")
    ip_count: int = Field(..., description="Distinct IP addresses involved")
    card_count: int = Field(..., description="Distinct payment instruments involved")
    merchant_count: int = Field(..., description="Distinct merchants involved")
    suspicious_transaction_count: int = Field(
        ..., description="Number of transactions with elevated ML risk"
    )
    total_transaction_amount: float = Field(
        ..., description="Sum of all transaction amounts in cluster (INR)"
    )
    suspicious_transaction_amount: float = Field(
        ..., description="Sum of suspicious transaction amounts (INR)"
    )
    primary_reason: str = Field(..., description="Primary detected abuse pattern or reasoning")


class ClusterDetail(ClusterSummary):
    """Comprehensive details of a detected cluster, including member entities, reasons, and graph data."""

    member_transaction_ids: list[str] = Field(
        default_factory=list, description="List of raw transaction IDs"
    )
    connected_entity_ids: list[str] = Field(
        default_factory=list, description="List of all namespaced node IDs"
    )
    risk_factors: list[ClusterRiskFactor] = Field(
        default_factory=list, description="Individual contributing risk factors"
    )
    explanation: str = Field(
        ..., description="Comprehensive deterministic explanation for analysts"
    )
    graph_data: GraphData = Field(
        default_factory=GraphData, description="Sub-graph nodes and edges for visualization"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional cluster metrics and timestamps"
    )


class ClusterListResponse(BaseModel):
    """Paginated list response for detected fraud clusters."""

    total_clusters: int = Field(..., description="Total count of detected clusters matching filter")
    limit: int = Field(default=50, description="Page limit")
    offset: int = Field(default=0, description="Page offset")
    clusters: list[ClusterSummary] = Field(
        default_factory=list, description="List of cluster summaries"
    )


class NetworkMembersResponse(BaseModel):
    """Member entities involved in a risk network / cluster."""

    network_id: str = Field(..., description="Risk network / cluster ID")
    total_members: int = Field(default=0, description="Total distinct member entities")
    customer_ids: list[str] = Field(default_factory=list)
    device_ids: list[str] = Field(default_factory=list)
    ip_addresses: list[str] = Field(default_factory=list)
    card_ids: list[str] = Field(default_factory=list)
    merchant_ids: list[str] = Field(default_factory=list)


class NetworkTransactionsResponse(BaseModel):
    """Paginated transactions associated with a risk network / cluster."""

    network_id: str = Field(..., description="Risk network / cluster ID")
    total_transactions: int = Field(..., description="Total transactions in network")
    limit: int = Field(default=50, description="Page limit")
    offset: int = Field(default=0, description="Page offset")
    transactions: list[dict[str, Any]] = Field(default_factory=list)
