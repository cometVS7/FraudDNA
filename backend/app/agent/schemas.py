"""FraudDNA AI Investigation Agent Schemas.

Defines Pydantic models for structured agent findings, evidence items,
tool traces, request payloads, and response envelopes.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.investigation import RiskLevel


class AgentEvidenceItem(BaseModel):
    """A single piece of grounded evidence verified by the investigation agent."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(
        ...,
        description="Subsystem or tool providing the evidence (e.g. risk_model, graph, rag, xai).",
    )
    evidence_type: str = Field(
        ...,
        description="Machine-readable evidence identifier (e.g. shared_device, cluster_collusion).",
    )
    snippet: str = Field(
        ..., description="Grounded, verifiable factual statement supporting the investigation."
    )
    severity: str = Field(
        ..., description="Severity tier of the evidence (low, medium, high, critical)."
    )


class ToolExecutionRecord(BaseModel):
    """Observable trace of a single bounded tool invocation by the agent."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(..., description="Name of the allowlisted tool executed.")
    tool_args: dict[str, Any] = Field(
        default_factory=dict, description="Arguments passed to the tool."
    )
    status: str = Field(..., description="Execution status: 'success', 'error', or 'timeout'.")
    duration_ms: float = Field(..., description="Execution time in milliseconds.")
    error_message: str | None = Field(None, description="Error detail if execution failed.")


class AgentInvestigationOutput(BaseModel):
    """Validated structured findings synthesized by the AI investigation agent."""

    model_config = ConfigDict(extra="forbid")

    investigation_id: str = Field(
        ..., description="Deterministic unique identifier for this investigation."
    )
    transaction_id: str = Field(..., description="Investigated transaction identifier.")
    risk_level: RiskLevel = Field(
        ..., description="Overall evaluated risk tier (low, medium, high, critical)."
    )
    risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Numerical fraud risk score [0.0, 1.0]."
    )
    summary: str = Field(
        ..., description="Concise, objective summary of the investigation findings."
    )
    fraud_hypothesis: str = Field(
        ..., description="Hypothesis regarding the modus operandi or legitimate explanation."
    )
    evidence: list[AgentEvidenceItem] = Field(
        default_factory=list, description="Grounded evidence items verified across tools."
    )
    related_entities: list[str] = Field(
        default_factory=list,
        description="Key entities (devices, IPs, cards, accounts) discovered during graph traversal.",
    )
    cluster_context: str | None = Field(
        None, description="FraudDNA cluster summary if transaction belongs to a detected cluster."
    )
    historical_cases: list[str] = Field(
        default_factory=list,
        description="Matched historical fraud syndicates or cases retrieved from RAG.",
    )
    policy_context: list[str] = Field(
        default_factory=list,
        description="Relevant policy rules, thresholds, or escalation SLAs retrieved from RAG.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score in the investigation findings [0.0, 1.0].",
    )
    recommended_action: str = Field(
        ...,
        description="Investigative recommendation: 'ALLOW', 'REVIEW', or 'HOLD'. Note: Policy Engine makes final decision.",
    )
    reasoning: str = Field(
        ..., description="Chain of evidence and logical reasoning leading to the recommendation."
    )
    limitations: list[str] = Field(
        default_factory=list,
        description="Known uncertainties, missing data, or degraded subsystem dependencies.",
    )
    agent_steps: int = Field(..., ge=1, description="Number of agent reasoning steps executed.")
    tool_trace: list[ToolExecutionRecord] = Field(
        default_factory=list, description="Audit trace of all tool invocations."
    )


class AgentInvestigationRequest(BaseModel):
    """Payload to trigger an AI agent investigation."""

    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(
        ...,
        description="Unique identifier of the transaction to investigate.",
        examples=["txn_00001"],
    )
    max_steps: int | None = Field(
        None, ge=1, le=15, description="Optional override for maximum agent reasoning steps."
    )


class AgentInvestigationResponse(BaseModel):
    """API response envelope for an agent investigation."""

    model_config = ConfigDict(extra="forbid")

    investigation_id: str = Field(..., description="Unique investigation identifier.")
    transaction_id: str = Field(..., description="Investigated transaction identifier.")
    status: str = Field(..., description="Investigation status: 'completed', 'degraded', 'failed'.")
    findings: AgentInvestigationOutput = Field(
        ..., description="Structured findings produced by the agent."
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="UTC timestamp of investigation."
    )
