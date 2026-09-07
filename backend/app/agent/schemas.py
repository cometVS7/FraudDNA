"""FraudDNA AI Investigation Agent Schemas.

Defines strict Pydantic models for structured agent findings, evidence items,
hypotheses, case recommendations, tool traces, request payloads, and response envelopes.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.investigation import RiskLevel


class EvidenceType(StrEnum):
    """Categorization of evidence in the FraudDNA intelligence hierarchy."""

    TRANSACTION_EVIDENCE = "TRANSACTION_EVIDENCE"
    XAI_EVIDENCE = "XAI_EVIDENCE"
    ENTITY_EVIDENCE = "ENTITY_EVIDENCE"
    NETWORK_EVIDENCE = "NETWORK_EVIDENCE"
    TYPOLOGY_EVIDENCE = "TYPOLOGY_EVIDENCE"
    AUDIT_EVIDENCE = "AUDIT_EVIDENCE"


class EvidenceSeverity(StrEnum):
    """Severity tier for an individual evidence item."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentEvidenceItem(BaseModel):
    """A single piece of grounded, source-attributed evidence verified by the investigation agent."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        ...,
        description="Deterministic unique evidence identifier (evi_...).",
        examples=["evi_9f83a2c1"],
    )
    category: EvidenceType = Field(
        default=EvidenceType.TRANSACTION_EVIDENCE,
        description="Hierarchy tier classification for this evidence.",
    )
    source: str = Field(
        ...,
        description="Subsystem or tool providing the evidence (e.g. risk_orchestrator, shap, network_intel, rag, audit).",
    )
    source_id: str = Field(
        ...,
        description="Referenced entity ID, transaction ID, pattern name, or document ID.",
    )
    snippet: str = Field(
        ...,
        description="Grounded, verifiable factual statement supporting the investigation.",
    )
    severity: str = Field(
        ...,
        description="Severity tier of the evidence (low, medium, high, critical).",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score in the veracity of this evidence [0.0, 1.0].",
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict,
        description="Traceable metadata (e.g. timestamps, query parameters, raw metric values).",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC generation timestamp.",
    )

    @property
    def evidence_type(self) -> str:
        """Compatibility property for legacy consumers."""
        return self.category.value


class AgentFindingOutput(BaseModel):
    """A machine-readable analytical finding produced by the agent with evidence citations."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(
        ...,
        description="Unique deterministic finding identifier (fnd_...).",
    )
    finding_type: str = Field(
        ...,
        description="Finding classification (e.g. SHARED_HARDWARE_ANOMALY, SYNDICATE_AFFILIATION).",
    )
    statement: str = Field(
        ...,
        description="Objective analytical statement explaining the finding.",
    )
    supporting_evidence_ids: list[str] = Field(
        default_factory=list,
        description="Traceable IDs of AgentEvidenceItem supporting this finding.",
    )
    observed_facts: list[str] = Field(
        default_factory=list,
        description="Directly observed empirical data points backing the claim.",
    )
    inference: str = Field(
        ...,
        description="Analytical reasoning explaining why the observed facts indicate risk.",
    )
    uncertainty: str | None = Field(
        None,
        description="Known unknowns, missing data, or limitations regarding this finding.",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Analytical confidence score [0.0, 1.0].",
    )


class InvestigationHypothesis(BaseModel):
    """A formulated fraud modus operandi or legitimate explanation hypothesis."""

    model_config = ConfigDict(extra="forbid")

    hypothesis_id: str = Field(..., description="Unique hypothesis identifier.")
    title: str = Field(..., description="Short hypothesis title.")
    description: str = Field(..., description="Comprehensive explanation of the hypothesis.")
    supporting_evidence_ids: list[str] = Field(
        default_factory=list,
        description="IDs of evidence items substantiating this hypothesis.",
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in this hypothesis.")


class CaseRecommendation(BaseModel):
    """Advisory operational recommendation for human fraud operations analysts."""

    model_config = ConfigDict(extra="forbid")

    recommended_action: str = Field(
        ...,
        description="Advisory operational action (e.g. MANUAL_REVIEW_ESCALATION, MERCHANT_INQUIRY, CLOSE_BENIGN). Note: Policy Engine controls financial action.",
    )
    priority: str = Field(
        default="MEDIUM",
        description="Case triage priority: LOW, MEDIUM, HIGH, CRITICAL.",
    )
    reasoning: str = Field(
        ...,
        description="Evidence-backed justification for the operational recommendation.",
    )
    suggested_next_steps: list[str] = Field(
        default_factory=list,
        description="Actionable next steps for the human investigator.",
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
    evidence_items: list[AgentEvidenceItem] = Field(
        default_factory=list,
        description="Grounded evidence items verified across tools.",
    )
    findings: list[AgentFindingOutput] = Field(
        default_factory=list,
        description="Structured machine-readable analytical findings.",
    )
    hypotheses: list[InvestigationHypothesis] = Field(
        default_factory=list,
        description="Formulated risk or legitimacy hypotheses.",
    )
    related_entities: list[str] = Field(
        default_factory=list,
        description="Key entities (devices, IPs, cards, accounts) discovered during investigation.",
    )
    network_id: str | None = Field(
        None,
        description="Primary risk network / syndicate identifier if affiliated.",
    )
    cluster_context: str | None = Field(
        None,
        description="FraudDNA cluster summary if transaction belongs to a detected cluster.",
    )
    detected_patterns: list[str] = Field(
        default_factory=list,
        description="Canonical syndicate patterns triggered (e.g. DEVICE_REUSE_RING).",
    )
    historical_cases: list[str] = Field(
        default_factory=list,
        description="Matched historical fraud syndicates or cases retrieved from RAG.",
    )
    policy_context: list[str] = Field(
        default_factory=list,
        description="Relevant policy rules, thresholds, or escalation SLAs retrieved from RAG.",
    )
    cited_typology_docs: list[str] = Field(
        default_factory=list,
        description="Document identifiers cited from knowledge base (e.g. GDL-001, CASE-2025-089).",
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
    recommendation: CaseRecommendation | None = Field(
        None,
        description="Detailed advisory case recommendation for human analysts.",
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
    model_provider: str = Field(
        default="deterministic",
        description="LLM provider used for synthesis (e.g. gemini, openai, deterministic).",
    )
    model_name: str = Field(
        default="rule_fallback_v2",
        description="Model name or fallback version.",
    )
    is_degraded: bool = Field(
        default=False,
        description="True if synthesis executed in degraded / deterministic fallback mode.",
    )

    @property
    def evidence(self) -> list[AgentEvidenceItem]:
        """Compatibility alias for evidence items."""
        return self.evidence_items


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
    include_network: bool = Field(
        default=True,
        description="Whether to execute multi-hop network discovery during investigation.",
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
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of investigation.",
    )
