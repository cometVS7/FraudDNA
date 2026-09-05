"""End-to-End Integration tests for Phase 5 (Agent + Policy Engine APIs)."""

import pytest
from fastapi.testclient import TestClient

from app.graph.service import get_graph_service
from app.main import app

client = TestClient(app)


@pytest.fixture
def sample_tx_id() -> str:
    graph_service = get_graph_service()
    graph_service.initialize()
    assert len(graph_service.transactions_by_id) > 0
    return next(iter(graph_service.transactions_by_id.keys()))


def test_api_run_agent_investigation_success(sample_tx_id: str) -> None:
    resp = client.post(
        "/api/v1/agent/investigate",
        json={"transaction_id": sample_tx_id, "max_steps": 6},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "investigation_id" in data
    assert data["transaction_id"] == sample_tx_id
    assert "findings" in data
    findings = data["findings"]
    assert "risk_score" in findings
    assert "risk_level" in findings
    assert "recommended_action" in findings
    assert "tool_trace" in findings


def test_api_get_agent_investigation_by_id(sample_tx_id: str) -> None:
    # 1. Run investigation
    create_resp = client.post(
        "/api/v1/agent/investigate",
        json={"transaction_id": sample_tx_id},
    )
    assert create_resp.status_code == 200
    inv_id = create_resp.json()["investigation_id"]

    # 2. Fetch by ID
    get_resp = client.get(f"/api/v1/agent/investigate/{inv_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["investigation_id"] == inv_id


def test_api_agent_investigation_not_found() -> None:
    resp = client.post(
        "/api/v1/agent/investigate",
        json={"transaction_id": "txn_nonexistent_88888"},
    )
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_api_evaluate_policy_decision(sample_tx_id: str) -> None:
    resp = client.post(
        "/api/v1/decisions/evaluate",
        json={"transaction_id": sample_tx_id},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "decision_id" in data
    assert data["transaction_id"] == sample_tx_id
    assert data["action"] in {"ALLOW", "REVIEW", "HOLD"}
    assert isinstance(data["reason_codes"], list)
    assert len(data["reason_codes"]) > 0
    assert data["is_deterministic"] is True


def test_api_get_policy_decision_by_transaction_id(sample_tx_id: str) -> None:
    resp = client.get(f"/api/v1/decisions/{sample_tx_id}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["transaction_id"] == sample_tx_id
    assert data["action"] in {"ALLOW", "REVIEW", "HOLD"}
