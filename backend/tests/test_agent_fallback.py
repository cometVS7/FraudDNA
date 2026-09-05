"""Unit tests for Agent Failure Modes & Fallback Semantics."""

import pytest

from app.agent.service import AgentInvestigationService
from app.graph.service import get_graph_service
from app.services.investigation import TransactionNotFoundError


@pytest.fixture
def sample_tx_id() -> str:
    graph_service = get_graph_service()
    graph_service.initialize()
    assert len(graph_service.transactions_by_id) > 0
    return next(iter(graph_service.transactions_by_id.keys()))


def test_agent_nonexistent_transaction_raises_not_found() -> None:
    service = AgentInvestigationService()
    with pytest.raises(TransactionNotFoundError, match="txn_nonexistent_99999"):
        service.investigate("txn_nonexistent_99999")


def test_agent_idempotent_investigation_ids(sample_tx_id: str) -> None:
    service = AgentInvestigationService()
    resp1 = service.investigate(sample_tx_id)
    resp2 = service.investigate(sample_tx_id)

    assert resp1.investigation_id == resp2.investigation_id
    assert resp1.findings.risk_score == resp2.findings.risk_score
    assert resp1.findings.recommended_action == resp2.findings.recommended_action


def test_get_investigation_by_id_retrieval(sample_tx_id: str) -> None:
    service = AgentInvestigationService()
    resp = service.investigate(sample_tx_id)
    cached = service.get_investigation_by_id(resp.investigation_id)

    assert cached is not None
    assert cached.investigation_id == resp.investigation_id
    assert cached.transaction_id == sample_tx_id

    missing = service.get_investigation_by_id("inv_agent_nonexistent")
    assert missing is None


def test_llm_external_call_wired_with_credentials(
    monkeypatch: pytest.MonkeyPatch, sample_tx_id: str
) -> None:
    from app.agent.graph import InvestigationGraphRunner

    runner = InvestigationGraphRunner()

    # Mock _call_llm_synthesis to simulate external LLM response
    mock_llm_response = {
        "investigation_id": "inv_agent_mock",
        "transaction_id": sample_tx_id,
        "risk_level": "high",
        "risk_score": 0.85,
        "summary": "Mock LLM synthesized findings.",
        "fraud_hypothesis": "Collusive device sharing.",
        "evidence": [
            {
                "source": "frauddna_graph",
                "evidence_type": "shared_device",
                "snippet": "Hardware device shared across multiple accounts.",
                "severity": "high",
            }
        ],
        "related_entities": ["device:dev_1"],
        "cluster_context": "Cluster 1",
        "historical_cases": ["CASE-2025-089"],
        "policy_context": ["POL-001"],
        "confidence": 0.90,
        "recommended_action": "HOLD",
        "reasoning": "High risk score combined with device sharing.",
        "limitations": [],
        "agent_steps": 6,
        "tool_trace": [],
    }

    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "sk-mock-test-key")
    monkeypatch.setattr(runner, "_call_llm_synthesis", lambda **_kwargs: mock_llm_response)

    output = runner.run(sample_tx_id)
    assert output.summary == "Mock LLM synthesized findings."
    assert output.recommended_action == "HOLD"
    assert output.confidence == 0.90


def test_llm_external_call_failure_triggers_deterministic_fallback(
    monkeypatch: pytest.MonkeyPatch, sample_tx_id: str
) -> None:
    from app.agent.graph import InvestigationGraphRunner

    runner = InvestigationGraphRunner()

    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "sk-mock-failing-key")
    monkeypatch.setattr(runner, "_call_llm_synthesis", lambda **_kwargs: None)

    # Should gracefully fall back to deterministic synthesis
    output = runner.run(sample_tx_id)
    assert output.investigation_id.startswith("inv_agent_")
    assert output.recommended_action in {"ALLOW", "REVIEW", "HOLD"}
    assert output.agent_steps >= 1
