"""FraudDNA AI Investigation Agent State Definition.

Defines the explicit, bounded state TypedDict managed across LangGraph nodes.
"""

from typing import Any, TypedDict


class InvestigationState(TypedDict, total=False):
    """Explicit bounded state schema for the FraudDNA LangGraph investigation workflow."""

    investigation_id: str
    transaction_id: str
    current_step: int
    max_steps: int
    tool_budget: int

    # Observable tool execution traces
    tools_called: list[str]
    tool_results: dict[str, Any]
    tool_trace: list[dict[str, Any]]
    errors: list[str]

    # Contextual cache populated during investigation
    risk_info: dict[str, Any]
    graph_info: dict[str, Any]
    cluster_info: dict[str, Any]
    historical_cases: list[dict[str, Any]]
    policy_guidelines: list[dict[str, Any]]

    # Agent structured findings
    structured_output: dict[str, Any] | None
    is_complete: bool
    status: str  # "completed", "degraded", "failed"
    retry_count: int
