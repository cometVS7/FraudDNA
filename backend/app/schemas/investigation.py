"""FraudDNA Investigation Schemas.

Defines Pydantic models for transaction risk investigations, explainability (XAI),
entity relationships, cluster context, and deterministic evidence synthesis.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(StrEnum):
    """Deterministic risk severity level based on risk score."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceSeverity(StrEnum):
    """Severity tier for an individual evidence item."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EvidenceSource(StrEnum):
    """Source subsystem generating the evidence item."""

    RISK_MODEL = "risk_model"
    SHAP = "shap"
    FRAUDDNA_GRAPH = "frauddna_graph"
    FRAUDDNA_CLUSTER = "frauddna_cluster"


class FactorDirection(StrEnum):
    """Direction of risk influence for an XAI feature factor."""

    INCREASES_RISK = "increases_risk"
    DECREASES_RISK = "decreases_risk"
    NEUTRAL = "neutral"


class InvestigationStatus(StrEnum):
    """Overall status of the investigation output."""

    COMPLETED = "completed"
    DEGRADED = "degraded"
    FAILED = "failed"


class InvestigationRequest(BaseModel):
    """Request payload to initiate a transaction risk investigation."""

    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(
        ...,
        description="Unique identifier of the transaction to investigate.",
        examples=["txn_00001"],
    )


class RiskFactor(BaseModel):
    """Structured XAI feature contribution explaining transaction-level risk."""

    model_config = ConfigDict(extra="forbid")

    feature: str = Field(..., description="Name of the model feature.")
    value: Any = Field(..., description="Observed value of the feature in this transaction.")
    impact: float = Field(..., description="SHAP attribution value (magnitude/direction).")
    direction: FactorDirection = Field(
        ..., description="Whether this factor increases or decreases risk."
    )
    rank: int = Field(..., ge=1, description="Importance rank of this factor (1 = top driver).")


class RelatedEntity(BaseModel):
    """An entity directly or closely connected to the transaction in the FraudDNA graph."""

    model_config = ConfigDict(extra="forbid")

    entity_type: str = Field(..., description="Entity type (customer, device, ip, card, merchant).")
    entity_id: str = Field(
        ..., description="Namespaced entity ID in the graph (e.g. device:dev_1)."
    )
    relationship: str = Field(
        ..., description="Relationship to transaction (e.g. transacted_from, used_payment_method)."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Contextual graph attributes (degrees, velocity, flags)."
    )


class RelatedTransaction(BaseModel):
    """A transaction connected via shared entities in the FraudDNA graph."""

    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(..., description="Identifier of the connected transaction.")
    timestamp: str | datetime = Field(..., description="Timestamp of the transaction.")
    amount: float = Field(..., description="Transaction amount in INR.")
    risk_score: float = Field(..., description="ML risk score of the connected transaction.")
    relationship: str = Field(
        ...,
        description="Relationship path (e.g. shared_device, shared_ip, shared_card, same_customer).",
    )


class ClusterInvestigationSummary(BaseModel):
    """Summary of the FraudDNA cluster that the investigated transaction belongs to."""

    model_config = ConfigDict(extra="forbid")

    cluster_id: str = Field(..., description="Unique cluster identifier.")
    cluster_risk_score: float = Field(..., description="Aggregated cluster risk score [0.0, 1.0].")
    is_suspicious: bool = Field(..., description="Whether the cluster is classified as suspicious.")
    transaction_count: int = Field(..., description="Total transactions in the cluster.")
    customer_count: int = Field(..., description="Distinct customers in the cluster.")
    device_count: int = Field(..., description="Distinct devices in the cluster.")
    ip_count: int = Field(..., description="Distinct IP addresses in the cluster.")
    card_count: int = Field(..., description="Distinct payment instruments in the cluster.")
    suspicious_transaction_count: int = Field(
        ..., description="Number of transactions with risk >= threshold."
    )
    primary_reason: str | None = Field(
        None, description="Primary explanation for cluster risk classification."
    )


class InvestigationEvidence(BaseModel):
    """A single deterministic, verifiable piece of evidence supporting the risk evaluation."""

    model_config = ConfigDict(extra="forbid")

    evidence_type: str = Field(
        ..., description="Machine-readable evidence key (e.g. shared_device_collusion)."
    )
    description: str = Field(..., description="Human-readable explanation of the verified signal.")
    severity: EvidenceSeverity = Field(..., description="Risk severity tier of this signal.")
    source: EvidenceSource = Field(..., description="Subsystem that verified this evidence.")


class InvestigationResponse(BaseModel):
    """Comprehensive structured risk investigation for a transaction."""

    model_config = ConfigDict(extra="forbid")

    investigation_id: str = Field(
        ..., description="Deterministic unique identifier for this investigation."
    )
    transaction_id: str = Field(..., description="Investigated transaction identifier.")
    risk_score: float = Field(..., description="ML model transaction risk score [0.0, 1.0].")
    risk_level: RiskLevel = Field(
        ..., description="Categorical risk level (low, medium, high, critical)."
    )
    risk_factors: list[RiskFactor] = Field(
        default_factory=list, description="Top XAI feature attribution factors."
    )
    related_entities: list[RelatedEntity] = Field(
        default_factory=list, description="Direct and neighboring entities in the FraudDNA graph."
    )
    related_transactions: list[RelatedTransaction] = Field(
        default_factory=list,
        description="Related transactions connected via shared graph entities.",
    )
    cluster: ClusterInvestigationSummary | None = Field(
        None, description="FraudDNA cluster context if transaction belongs to a detected cluster."
    )
    evidence: list[InvestigationEvidence] = Field(
        default_factory=list,
        description="Deterministic evidence items synthesized from all signals.",
    )
    status: InvestigationStatus = Field(
        InvestigationStatus.COMPLETED, description="Execution status of the investigation."
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when investigation was synthesized.",
    )
