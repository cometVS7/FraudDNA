"""FraudDNA Deterministic Policy Engine Models.

Defines Pydantic models and Enums for deterministic financial actions,
structured reason codes, and policy decision audit objects.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PolicyAction(StrEnum):
    """Deterministic financial-risk recommendation."""

    ALLOW = "ALLOW"
    REVIEW = "REVIEW"
    HOLD = "HOLD"


class PolicyReasonCode(StrEnum):
    """Explicit, human-readable reason codes supporting a deterministic policy decision."""

    LOW_RISK_BASELINE = "LOW_RISK_BASELINE"
    MODERATE_RISK_ELEVATED = "MODERATE_RISK_ELEVATED"
    HIGH_RISK_SCORE = "HIGH_RISK_SCORE"
    CRITICAL_RISK_SCORE = "CRITICAL_RISK_SCORE"
    SUSPICIOUS_FRAUD_CLUSTER = "SUSPICIOUS_FRAUD_CLUSTER"
    SHARED_HARDWARE_DEVICE = "SHARED_HARDWARE_DEVICE"
    SHARED_IP_SUBNET = "SHARED_IP_SUBNET"
    SHARED_PAYMENT_INSTRUMENT = "SHARED_PAYMENT_INSTRUMENT"
    HIGH_VELOCITY_BURST = "HIGH_VELOCITY_BURST"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    RAG_EVIDENCE_DEGRADED = "RAG_EVIDENCE_DEGRADED"
    AGENT_UNCERTAINTY = "AGENT_UNCERTAINTY"
    POLICY_ESCALATION_REQUIRED = "POLICY_ESCALATION_REQUIRED"
    INVESTIGATION_FALLBACK = "INVESTIGATION_FALLBACK"


class PolicyEvaluationRequest(BaseModel):
    """Request payload to trigger deterministic policy evaluation for a transaction."""

    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(
        ...,
        description="Unique identifier of the transaction to evaluate.",
        examples=["txn_00001"],
    )
    risk_score_override: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Optional simulation risk score override [0.0, 1.0].",
    )


class PolicyDecision(BaseModel):
    """Deterministic policy evaluation result for a transaction."""

    model_config = ConfigDict(extra="forbid")

    decision_id: str = Field(
        ..., description="Deterministic unique identifier for this policy decision."
    )
    transaction_id: str = Field(..., description="Evaluated transaction identifier.")
    action: PolicyAction = Field(
        ..., description="Final deterministic policy action (ALLOW, REVIEW, HOLD)."
    )
    reason_codes: list[PolicyReasonCode] = Field(
        ..., description="Explicit reason codes supporting the policy decision."
    )
    risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Numerical transaction fraud risk score [0.0, 1.0]."
    )
    risk_level: str = Field(..., description="Categorical risk tier (low, medium, high, critical).")
    cluster_id: str | None = Field(
        None, description="Cluster identifier if transaction is in a FraudDNA cluster."
    )
    policy_version: str = Field(..., description="Configuration version of the evaluated rule set.")
    evidence_summary: list[str] = Field(
        default_factory=list, description="Summary of evidence points triggering the decision."
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="UTC timestamp of the policy decision."
    )
    is_deterministic: bool = Field(
        default=True, description="Always True; confirms rule matrix is deterministic."
    )
