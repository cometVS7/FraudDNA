"""Unit tests for AI Agent Allowlisted Tools."""

import pytest

from app.agent.tools import AgentTools


@pytest.fixture
def sample_tx_id() -> str:
    tools = AgentTools()
    tools.graph_service.initialize()
    assert len(tools.graph_service.transactions_by_id) > 0
    return next(iter(tools.graph_service.transactions_by_id.keys()))


def test_agent_tools_allowlist() -> None:
    tools = AgentTools()
    assert len(tools.ALLOWLISTED_TOOLS) == 7
    assert "get_transaction_history" in tools.ALLOWLISTED_TOOLS
    assert "get_customer_profile" in tools.ALLOWLISTED_TOOLS
    assert "get_related_entities" in tools.ALLOWLISTED_TOOLS
    assert "get_cluster_analysis" in tools.ALLOWLISTED_TOOLS
    assert "get_risk_explanation" in tools.ALLOWLISTED_TOOLS
    assert "search_historical_cases" in tools.ALLOWLISTED_TOOLS
    assert "retrieve_policy" in tools.ALLOWLISTED_TOOLS


def test_agent_tools_rejects_disallowed_tool(sample_tx_id: str) -> None:
    tools = AgentTools()
    with pytest.raises(ValueError, match="Disallowed or unknown tool"):
        tools.execute_tool("execute_arbitrary_sql", query="SELECT * FROM users")

    with pytest.raises(ValueError, match="Disallowed or unknown tool"):
        tools.execute_tool("refund_transaction", transaction_id=sample_tx_id)


def test_get_transaction_history_execution(sample_tx_id: str) -> None:
    tools = AgentTools()
    res, dur_ms = tools.execute_tool("get_transaction_history", transaction_id=sample_tx_id)
    assert dur_ms >= 0.0
    assert "found" in res
    assert res["found"] is True
    assert res["transaction_id"] == sample_tx_id
    assert "amount" in res
    assert "customer_id" in res


def test_get_related_entities_execution(sample_tx_id: str) -> None:
    tools = AgentTools()
    res, dur_ms = tools.execute_tool("get_related_entities", transaction_id=sample_tx_id)
    assert dur_ms >= 0.0
    assert "found" in res
    assert res["found"] is True
    assert "entities" in res
    assert "has_shared_collusion_evidence" in res


def test_get_cluster_analysis_execution(sample_tx_id: str) -> None:
    tools = AgentTools()
    res, dur_ms = tools.execute_tool("get_cluster_analysis", transaction_id=sample_tx_id)
    assert dur_ms >= 0.0
    assert "in_cluster" in res


def test_get_risk_explanation_execution(sample_tx_id: str) -> None:
    tools = AgentTools()
    res, dur_ms = tools.execute_tool("get_risk_explanation", transaction_id=sample_tx_id)
    assert dur_ms >= 0.0
    assert "transaction_id" in res
    if "risk_score" in res:
        assert 0.0 <= res["risk_score"] <= 1.0


def test_search_historical_cases_execution() -> None:
    tools = AgentTools()
    res, dur_ms = tools.execute_tool("search_historical_cases", query="device farm", top_k=2)
    assert dur_ms >= 0.0
    assert "total_matches" in res
    assert "cases" in res


def test_retrieve_policy_execution() -> None:
    tools = AgentTools()
    res, dur_ms = tools.execute_tool("retrieve_policy", query="escalation SLA", top_k=2)
    assert dur_ms >= 0.0
    assert "total_matches" in res
    assert "policies" in res
