"""Unit tests for LangGraph AI Investigation Agent Workflow."""

import pytest

from app.agent.graph import InvestigationGraphRunner
from app.agent.schemas import AgentInvestigationOutput
from app.graph.service import get_graph_service


@pytest.fixture
def sample_tx_id() -> str:
    graph_service = get_graph_service()
    graph_service.initialize()
    assert len(graph_service.transactions_by_id) > 0
    return next(iter(graph_service.transactions_by_id.keys()))


def test_agent_graph_runner_initialization() -> None:
    runner = InvestigationGraphRunner()
    assert runner.app is not None


def test_agent_graph_execution_produces_valid_output(sample_tx_id: str) -> None:
    runner = InvestigationGraphRunner()
    output: AgentInvestigationOutput = runner.run(
        transaction_id=sample_tx_id,
        max_steps=8,
    )

    assert output.investigation_id.startswith("inv_agent_")
    assert output.transaction_id == sample_tx_id
    assert 0.0 <= output.risk_score <= 1.0
    assert output.risk_level.value in {"low", "medium", "high", "critical"}
    assert output.recommended_action in {"ALLOW", "REVIEW", "HOLD"}
    assert 0.0 <= output.confidence <= 1.0
    assert len(output.summary) > 0
    assert len(output.fraud_hypothesis) > 0
    assert len(output.reasoning) > 0
    assert output.agent_steps >= 1
    assert len(output.tool_trace) >= 1

    # Verify tool execution records
    for record in output.tool_trace:
        assert record.tool_name in runner.tools.ALLOWLISTED_TOOLS
        assert record.status in {"success", "error", "timeout"}
        assert record.duration_ms >= 0.0


def test_agent_graph_enforces_max_steps(sample_tx_id: str) -> None:
    runner = InvestigationGraphRunner()
    max_steps = 3
    output: AgentInvestigationOutput = runner.run(
        transaction_id=sample_tx_id,
        max_steps=max_steps,
    )

    assert output.agent_steps <= max_steps + 1
    assert len(output.tool_trace) <= max_steps
