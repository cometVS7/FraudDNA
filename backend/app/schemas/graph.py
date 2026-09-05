"""Graph Data Schemas for API and Frontend (React Flow) Consumption."""

from typing import Any

from pydantic import BaseModel, Field


class GraphNode(BaseModel):
    """Represents a node in the FraudDNA relationship graph."""

    id: str = Field(..., description="Unique namespaced node ID (e.g. 'device:dev_001')")
    raw_id: str = Field(..., description="Original raw entity identifier")
    entity_type: str = Field(..., description="Type of entity (customer, transaction, etc.)")
    label: str = Field(..., description="Display label for node")
    risk_score: float = Field(
        default=0.0, description="Risk score associated with the node [0.0 - 1.0]"
    )
    amount: float | None = Field(default=None, description="Transaction amount if applicable")
    timestamp: str | None = Field(default=None, description="Timestamp ISO string if applicable")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional node metadata")


class GraphEdge(BaseModel):
    """Represents a relationship edge connecting two graph nodes."""

    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node namespaced ID")
    target: str = Field(..., description="Target node namespaced ID")
    relation: str = Field(..., description="Semantic relation type (EXECUTED, ON_DEVICE, etc.)")
    weight: float = Field(default=1.0, description="Edge weight / confidence")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional edge metadata")


class GraphData(BaseModel):
    """Structured graph representation containing nodes and edges."""

    nodes: list[GraphNode] = Field(default_factory=list, description="List of graph nodes")
    edges: list[GraphEdge] = Field(default_factory=list, description="List of graph edges")
    total_nodes: int = Field(default=0, description="Total node count")
    total_edges: int = Field(default=0, description="Total edge count")
