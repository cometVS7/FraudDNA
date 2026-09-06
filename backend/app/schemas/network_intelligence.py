"""FraudDNA V2 Risk Network Intelligence Schemas.

Defines Pydantic models for multi-hop pathfinding, syndicate pattern detection,
network risk propagation, exposure metrics, temporal timelines, and structured findings.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.graph import GraphData


class PatternSeverity(StrEnum):
    """Severity classification for detected syndicate patterns."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class SyndicatePatternType(StrEnum):
    """Canonical attack patterns recognized by the syndicate detector."""

    DEVICE_REUSE_RING = "DEVICE_REUSE_RING"
    CARD_SHARING_RING = "CARD_SHARING_RING"
    IP_CONCENTRATION_CLUSTER = "IP_CONCENTRATION_CLUSTER"
    MULTI_INFRASTRUCTURE_COLLUSION = "MULTI_INFRASTRUCTURE_COLLUSION"
    MERCHANT_TARGETING_CLUSTER = "MERCHANT_TARGETING_CLUSTER"
    HIGH_VELOCITY_BURST_ATTACK = "HIGH_VELOCITY_BURST_ATTACK"
    LAYERED_ENTITY_CHAIN = "LAYERED_ENTITY_CHAIN"


class PathSegment(BaseModel):
    """A single directed or undirected hop in an entity connection path."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., description="Source node namespaced ID")
    source_type: str = Field(..., description="Source entity type (customer, device, card, etc.)")
    relation: str = Field(..., description="Relationship type (e.g. SHARES_DEVICE, EXECUTED)")
    target_id: str = Field(..., description="Target node namespaced ID")
    target_type: str = Field(..., description="Target entity type")
    weight: float = Field(..., ge=0.0, le=1.0, description="Semantic edge weight")


class NetworkPath(BaseModel):
    """A bounded, scored connection path between two entities in the network."""

    model_config = ConfigDict(extra="forbid")

    path_id: str = Field(..., description="Unique deterministic path identifier")
    source_id: str = Field(..., description="Source entity ID")
    target_id: str = Field(..., description="Target entity ID")
    hop_count: int = Field(..., ge=1, le=4, description="Number of hops in the path")
    path_strength: float = Field(
        ..., ge=0.0, le=1.0, description="Calculated path relevance score [0.0, 1.0]"
    )
    segments: list[PathSegment] = Field(default_factory=list, description="Ordered path segments")
    summary: str = Field(..., description="Human-readable explanation of the connection path")


class SyndicatePattern(BaseModel):
    """A detected coordinated fraud pattern or syndicate signature."""

    model_config = ConfigDict(extra="forbid")

    pattern_type: SyndicatePatternType = Field(..., description="Canonical pattern identifier")
    name: str = Field(..., description="Human-readable pattern title")
    severity: PatternSeverity = Field(..., description="Threat severity level")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Pattern detection confidence")
    triggered: bool = Field(..., description="Whether the pattern criteria are met")
    description: str = Field(..., description="Detailed description of the pattern match")
    evidence: dict[str, Any] = Field(
        default_factory=dict, description="Supporting metrics and entity IDs"
    )


class NetworkTimelinePoint(BaseModel):
    """Activity metrics for a specific temporal window in the network."""

    model_config = ConfigDict(extra="forbid")

    time_bucket: str = Field(..., description="ISO 8601 timestamp representing the bucket start")
    transaction_count: int = Field(..., ge=0, description="Total transactions in window")
    suspicious_count: int = Field(..., ge=0, description="Suspicious transactions in window")
    total_amount: float = Field(..., ge=0.0, description="Total INR volume in window")
    suspicious_amount: float = Field(..., ge=0.0, description="Suspicious INR volume in window")
    active_customers: int = Field(..., ge=0, description="Distinct customers active in window")
    active_devices: int = Field(..., ge=0, description="Distinct devices active in window")


class NetworkTimeline(BaseModel):
    """Temporal progression and burst analysis for a risk network."""

    model_config = ConfigDict(extra="forbid")

    network_id: str = Field(..., description="Risk network identifier")
    first_seen: datetime = Field(..., description="Timestamp of first observed transaction")
    last_seen: datetime = Field(..., description="Timestamp of latest observed transaction")
    active_duration_hours: float = Field(..., ge=0.0, description="Total active duration in hours")
    is_burst_attack: bool = Field(..., description="True if activity occurred in a rapid spike")
    timeline_points: list[NetworkTimelinePoint] = Field(
        default_factory=list, description="Chronological activity buckets"
    )


class NetworkExposure(BaseModel):
    """Financial and entity exposure metrics for a risk network."""

    model_config = ConfigDict(extra="forbid")

    network_id: str = Field(..., description="Risk network identifier")
    total_transactions: int = Field(..., ge=0, description="Total member transactions")
    suspicious_transactions: int = Field(
        ..., ge=0, description="Transactions with risk score >= 0.37"
    )
    total_amount: float = Field(..., ge=0.0, description="Total financial volume across network")
    suspicious_amount: float = Field(
        ..., ge=0.0, description="Financial volume of suspicious transactions"
    )
    exposed_customer_count: int = Field(..., ge=0, description="Count of linked customer accounts")
    exposed_device_count: int = Field(..., ge=0, description="Count of linked hardware devices")
    exposed_card_count: int = Field(..., ge=0, description="Count of linked payment cards")
    exposed_ip_count: int = Field(..., ge=0, description="Count of linked IP addresses")
    exposed_merchant_count: int = Field(..., ge=0, description="Count of targeted merchants")
    primary_targeted_merchant_id: str | None = Field(
        None, description="Disproportionately targeted merchant if any"
    )
    merchant_concentration_ratio: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of volume to the top merchant"
    )


class NetworkTopologyMetrics(BaseModel):
    """Structural graph metrics for the network subgraph."""

    model_config = ConfigDict(extra="forbid")

    node_count: int = Field(..., ge=0, description="Total nodes in network subgraph")
    edge_count: int = Field(..., ge=0, description="Total edges in network subgraph")
    density: float = Field(..., ge=0.0, le=1.0, description="Graph edge density")
    customer_to_device_ratio: float = Field(
        ..., ge=0.0, description="Ratio of distinct customers to devices"
    )
    customer_to_card_ratio: float = Field(
        ..., ge=0.0, description="Ratio of distinct customers to cards"
    )
    infrastructure_sharing_index: float = Field(
        ..., ge=0.0, le=1.0, description="Normalized infrastructure collusion score"
    )


class NetworkFinding(BaseModel):
    """A structured, machine-readable finding produced by network intelligence."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Deterministic unique finding identifier (fnd_...)")
    finding_type: str = Field(..., description="Classification of finding")
    severity: PatternSeverity = Field(..., description="Finding severity")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in finding")
    title: str = Field(..., description="Short finding summary")
    description: str = Field(..., description="Comprehensive explanation")
    affected_entities: list[str] = Field(
        default_factory=list, description="IDs of implicated entities"
    )
    affected_transactions: list[str] = Field(
        default_factory=list, description="IDs of implicated transactions"
    )
    evidence_items: list[dict[str, Any]] = Field(
        default_factory=list, description="Structured supporting evidence records"
    )
    pattern_name: str | None = Field(None, description="Associated pattern if applicable")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="UTC generation timestamp"
    )


class NetworkIntelligenceResponse(BaseModel):
    """Comprehensive intelligence package for a risk network."""

    model_config = ConfigDict(extra="forbid")

    network_id: str = Field(..., description="Unique risk network / cluster identifier")
    network_name: str = Field(..., description="Display name for the risk syndicate")
    status: str = Field(..., description="Operational status (ACTIVE, MONITOR, MITIGATED)")
    is_suspicious: bool = Field(..., description="True if flagged as suspicious fraud syndicate")
    primary_reason: str = Field(..., description="Core heuristic or signature driving risk")
    propagated_risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Mathematically derived network risk score"
    )
    risk_tier: str = Field(..., description="LOW, MEDIUM, HIGH, or CRITICAL")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Evidence completeness and confidence"
    )
    exposure: NetworkExposure = Field(..., description="Financial and entity exposure metrics")
    topology: NetworkTopologyMetrics = Field(..., description="Structural graph metrics")
    patterns: list[SyndicatePattern] = Field(
        default_factory=list, description="Detected attack signatures"
    )
    key_paths: list[NetworkPath] = Field(
        default_factory=list, description="Top ranked entity connection paths"
    )
    timeline: NetworkTimeline = Field(..., description="Temporal progression analytics")
    findings: list[NetworkFinding] = Field(
        default_factory=list, description="Machine-readable structured findings"
    )
    subgraph: GraphData = Field(..., description="Bounded React Flow graph data")
    as_of: datetime | None = Field(None, description="Point-in-time timestamp if specified")


class EntityNetworkIntelligenceResponse(BaseModel):
    """Network intelligence context for an individual entity (customer, device, etc.)."""

    model_config = ConfigDict(extra="forbid")

    entity_type: str = Field(..., description="Entity type (customer, device, ip, card, etc.)")
    entity_id: str = Field(..., description="Raw entity identifier")
    network_id: str | None = Field(None, description="Primary network ID if affiliated")
    is_network_member: bool = Field(..., description="Whether entity belongs to a risk network")
    network_risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Risk score of the affiliated network"
    )
    connected_networks_count: int = Field(
        ..., ge=0, description="Total risk networks touching this entity"
    )
    cross_customer_sharing_count: int = Field(
        ..., ge=0, description="Number of other distinct accounts sharing this entity"
    )
    patterns: list[SyndicatePattern] = Field(
        default_factory=list, description="Active patterns involving this entity"
    )
    key_paths: list[NetworkPath] = Field(
        default_factory=list, description="Paths connecting entity to other high-risk nodes"
    )
    findings: list[NetworkFinding] = Field(
        default_factory=list, description="Findings relevant to this entity"
    )


class PathSearchRequest(BaseModel):
    """Request payload for finding connection paths between two entities."""

    model_config = ConfigDict(extra="forbid")

    source_type: str = Field(..., description="Source entity category (customer, device, etc.)")
    source_id: str = Field(..., description="Source entity ID")
    target_type: str = Field(..., description="Target entity category")
    target_id: str = Field(..., description="Target entity ID")
    max_depth: int = Field(default=3, ge=1, le=4, description="Maximum traversal depth")
    max_paths: int = Field(default=10, ge=1, le=50, description="Maximum paths to return")


class PathSearchResponse(BaseModel):
    """Response payload containing ranked entity connection paths."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(..., description="Source entity identifier")
    target_id: str = Field(..., description="Target entity identifier")
    paths_found: int = Field(..., ge=0, description="Total discovered paths")
    paths: list[NetworkPath] = Field(default_factory=list, description="Ranked connection paths")
