"""FraudDNA AI Investigation Agent State Definition.

Defines the explicit, bounded state TypedDict managed across LangGraph nodes.
"""

from typing import Any, TypedDict


class InvestigationState(TypedDict, total=False):
    """Explicit bounded state schema for the FraudDNA LangGraph investigation workflow."""

    # Context & Identifiers
    correlation_id: str
    investigation_id: str
    transaction_id: str
    customer_id: str | None
    network_id: str | None

    # Step & Budget Tracking
    current_step: int
    max_steps: int
    tool_budget: int
    tools_called_count: int

    # Observable Tool Execution Traces
    tools_called: list[str]
    tool_results: dict[str, Any]
    tool_trace: list[dict[str, Any]]
    errors: list[str]
    limitations: list[str]

    # Contextual cache populated during investigation
    transaction_context: dict[str, Any]
    risk_orchestration_context: dict[str, Any]
    shap_signals_context: list[dict[str, Any]]
    entity_profile_context: dict[str, Any]
    ego_graph_context: dict[str, Any]
    network_intelligence_context: dict[str, Any]
    multi_hop_paths_context: list[dict[str, Any]]
    typology_rag_context: list[dict[str, Any]]
    audit_history_context: list[dict[str, Any]]

    # Verified Evidence Items (Accumulator)
    accumulated_evidence: list[dict[str, Any]]

    # Agent structured findings & output
    structured_output: dict[str, Any] | None
    confidence_score: float
    is_complete: bool
    status: str  # "completed", "degraded", "failed"
    retry_count: int
    is_degraded: bool
    model_provider: str
    model_name: str
