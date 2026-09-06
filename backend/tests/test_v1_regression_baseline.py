"""FraudDNA V1 Regression Baseline Protection Test Suite.

Protects all existing V1 functional capabilities and contracts before and during V2 evolution:
1. Health & Request Correlation
2. Dashboard Overview & Real Dataset Metrics
3. Transactions Ledger, Filtering & Sorting
4. Known Baseline Ground-Truth Transactions (Legitimate vs Coordinated Fraud)
5. Graph & Cluster Inspection
6. Deterministic Policy Engine Invariance
7. Structured Risk Investigation
8. Deterministic Threshold Simulation
9. Grounded RAG Knowledge Retrieval
10. Bounded LangGraph Agent Deterministic Execution
11. Centralized Domain Error & Exception Handling
"""

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.errors import (
    NotFoundDomainError,
    ValidationDomainError,
)
from app.graph.service import get_graph_service
from app.main import app

client = TestClient(app)

LEGIT_TX_ID = "tx_0000000"
COORDINATED_FRAUD_TX_ID = "tx_0001991"


@pytest.fixture(scope="module", autouse=True)
def initialize_system() -> None:
    """Ensure graph service and ML inference are warm for the entire test module."""
    service = get_graph_service()
    service.initialize()
    assert len(service.transactions_by_id) > 0


# ==============================================================================
# 1. HEALTH CHECK & REQUEST CORRELATION
# ==============================================================================


def test_health_endpoint_contract() -> None:
    """GET /api/v1/health must return healthy status and correlation headers."""
    resp = client.get(f"{settings.API_V1_PREFIX}/health")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "healthy"
    assert data["service"] == "FraudDNA"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data
    assert "environment" in data

    # Correlation header verification
    assert settings.REQUEST_ID_HEADER in resp.headers
    assert resp.headers[settings.REQUEST_ID_HEADER].startswith("req_")
    assert settings.CORRELATION_ID_HEADER in resp.headers


def test_request_correlation_propagation() -> None:
    """Safe client-supplied request ID must be preserved and echoed back."""
    custom_id = "test-client-req-999"
    resp = client.get(
        f"{settings.API_V1_PREFIX}/health",
        headers={settings.REQUEST_ID_HEADER: custom_id},
    )
    assert resp.status_code == 200
    assert resp.headers[settings.REQUEST_ID_HEADER] == custom_id
    assert resp.headers[settings.CORRELATION_ID_HEADER] == custom_id


def test_request_correlation_sanitization() -> None:
    """Malformed or oversized client request IDs must be replaced with safe generated IDs."""
    malformed_id = "bad ID with spaces and $#@! " + ("A" * 100)
    resp = client.get(
        f"{settings.API_V1_PREFIX}/health",
        headers={settings.REQUEST_ID_HEADER: malformed_id},
    )
    assert resp.status_code == 200
    returned_id = resp.headers[settings.REQUEST_ID_HEADER]
    assert returned_id != malformed_id
    assert returned_id.startswith("req_")


# ==============================================================================
# 2. OVERVIEW & DATASET METRICS
# ==============================================================================


def test_overview_metrics_contract() -> None:
    """GET /api/v1/overview must return empirical dataset overview metrics."""
    resp = client.get(f"{settings.API_V1_PREFIX}/overview")
    assert resp.status_code == 200
    data = resp.json()

    assert "total_transactions" in data
    assert data["total_transactions"] > 0
    assert "fraud_rate" in data
    assert 0.0 <= data["fraud_rate"] <= 1.0
    assert "risk_distribution" in data
    dist = data["risk_distribution"]
    assert "low" in dist and "medium" in dist and "high" in dist and "critical" in dist
    assert "total_amount" in data
    assert "total_clusters" in data


# ==============================================================================
# 3. TRANSACTIONS LISTING, SORTING & FILTERING
# ==============================================================================


def test_transactions_pagination_and_sorting() -> None:
    """GET /api/v1/transactions must support pagination and descending risk score sort."""
    resp = client.get(
        f"{settings.API_V1_PREFIX}/transactions",
        params={"limit": 10, "offset": 0, "sort_by": "risk_score", "sort_order": "desc"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["limit"] == 10
    assert data["offset"] == 0
    assert len(data["transactions"]) == 10
    assert data["total"] > 10

    # Verify descending sort order
    scores = [t["risk_score"] for t in data["transactions"]]
    assert scores == sorted(scores, reverse=True)


def test_transactions_risk_level_filter() -> None:
    """GET /api/v1/transactions must filter by risk_level correctly."""
    resp = client.get(
        f"{settings.API_V1_PREFIX}/transactions",
        params={"risk_level": "low", "limit": 10},
    )
    assert resp.status_code == 200
    data = resp.json()
    for tx in data["transactions"]:
        assert tx["risk_level"] == "low"


# ==============================================================================
# 4. GROUND TRUTH TRANSACTIONS (LEGITIMATE VS COORDINATED FRAUD)
# ==============================================================================


def test_legitimate_transaction_contract() -> None:
    """GET /api/v1/transactions/{id} for known legitimate baseline tx_0000000."""
    resp = client.get(f"{settings.API_V1_PREFIX}/transactions/{LEGIT_TX_ID}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["transaction_id"] == LEGIT_TX_ID
    assert data["is_fraud"] is False
    assert data["risk_level"] == "low"
    assert data["risk_score"] < 0.30


def test_coordinated_fraud_transaction_contract() -> None:
    """GET /api/v1/transactions/{id} for known syndicate alpha member tx_0001991."""
    resp = client.get(f"{settings.API_V1_PREFIX}/transactions/{COORDINATED_FRAUD_TX_ID}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["transaction_id"] == COORDINATED_FRAUD_TX_ID
    assert data["risk_score"] >= 0.70
    assert data["risk_level"] in {"high", "critical"}
    assert data["cluster_id"] is not None


# ==============================================================================
# 5. GRAPH AND CLUSTERS
# ==============================================================================


def test_cluster_listing_contract() -> None:
    """GET /api/v1/clusters must return list of detected network clusters."""
    resp = client.get(f"{settings.API_V1_PREFIX}/clusters", params={"limit": 5})
    assert resp.status_code == 200
    data = resp.json()

    assert "clusters" in data
    assert len(data["clusters"]) > 0
    first = data["clusters"][0]
    assert "cluster_id" in first
    assert "cluster_risk_score" in first
    assert "is_suspicious" in first


def test_transaction_neighborhood_graph_contract() -> None:
    """GET /api/v1/graph/transaction/{id} must return nodes and edges for visualization."""
    resp = client.get(f"{settings.API_V1_PREFIX}/graph/transaction/{COORDINATED_FRAUD_TX_ID}")
    assert resp.status_code == 200
    data = resp.json()

    assert "nodes" in data and len(data["nodes"]) >= 2
    assert "edges" in data and len(data["edges"]) >= 1


# ==============================================================================
# 6. DETERMINISTIC POLICY ENGINE INVARIANCE
# ==============================================================================


def test_policy_engine_legitimate_allow() -> None:
    """POST /api/v1/decisions/evaluate must deterministically ALLOW legitimate transactions."""
    resp = client.post(
        f"{settings.API_V1_PREFIX}/decisions/evaluate",
        json={"transaction_id": LEGIT_TX_ID},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["transaction_id"] == LEGIT_TX_ID
    assert data["action"] == "ALLOW"
    assert "LOW_RISK_BASELINE" in data["reason_codes"]
    assert data["is_deterministic"] is True
    assert data["decision_id"].startswith("dec_")


def test_policy_engine_coordinated_fraud_hold() -> None:
    """POST /api/v1/decisions/evaluate must deterministically HOLD coordinated fraud syndicate tx."""
    resp = client.post(
        f"{settings.API_V1_PREFIX}/decisions/evaluate",
        json={"transaction_id": COORDINATED_FRAUD_TX_ID},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["transaction_id"] == COORDINATED_FRAUD_TX_ID
    assert data["action"] == "HOLD"
    assert "SUSPICIOUS_FRAUD_CLUSTER" in data["reason_codes"]
    assert data["is_deterministic"] is True


# ==============================================================================
# 7. STRUCTURED RISK INVESTIGATION
# ==============================================================================


def test_investigation_service_contract() -> None:
    """POST /api/v1/investigations must synthesize ML, XAI, Graph, and Cluster evidence."""
    resp = client.post(
        f"{settings.API_V1_PREFIX}/investigations",
        json={"transaction_id": LEGIT_TX_ID},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["transaction_id"] == LEGIT_TX_ID
    assert "risk_factors" in data
    assert len(data["risk_factors"]) > 0
    assert "related_entities" in data
    assert "evidence" in data
    assert data["status"] in {"completed", "degraded"}


def test_investigation_not_found() -> None:
    """POST /api/v1/investigations for non-existent transaction must return 404."""
    resp = client.post(
        f"{settings.API_V1_PREFIX}/investigations",
        json={"transaction_id": "non_existent_tx_9999999"},
    )
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
    assert "non_existent_tx_9999999" in data["detail"]


# ==============================================================================
# 8. DETERMINISTIC SIMULATION
# ==============================================================================


def test_simulation_engine_contract() -> None:
    """POST /api/v1/simulations must replay threshold and cost formulas deterministically."""
    resp = client.post(
        f"{settings.API_V1_PREFIX}/simulations",
        json={"config": {"fraud_threshold": 0.37, "cost_per_false_positive": 350.0}},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_transactions"] > 0
    assert data["true_positives"] > 0
    assert data["expected_loss"] > 0.0
    assert data["is_deterministic"] is True


# ==============================================================================
# 9. RAG KNOWLEDGE RETRIEVAL
# ==============================================================================


def test_rag_search_contract() -> None:
    """POST /api/v1/rag/search must return grounded chunks from knowledge base."""
    resp = client.post(
        f"{settings.API_V1_PREFIX}/rag/search",
        json={"query": "device sharing coordinated fraud syndicate ring", "top_k": 3},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert "results" in data
    assert "total_results" in data


# ==============================================================================
# 10. BOUNDED AGENT DETERMINISTIC FALLBACK
# ==============================================================================


def test_agent_bounded_execution() -> None:
    """POST /api/v1/agent/investigate must execute bounded reasoning within step limits."""
    resp = client.post(
        f"{settings.API_V1_PREFIX}/agent/investigate",
        json={"transaction_id": LEGIT_TX_ID, "max_steps": 6},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["transaction_id"] == LEGIT_TX_ID
    assert data["status"] in {"completed", "degraded"}
    findings = data["findings"]
    assert "tool_trace" in findings
    assert len(findings["tool_trace"]) <= 6


# ==============================================================================
# 11. CENTRALIZED DOMAIN ERROR HANDLING
# ==============================================================================


def test_domain_error_handling_structure() -> None:
    """Domain errors must produce structured JSON with request_id and detail."""

    # Temporarily attach a test endpoint that raises DomainError
    @app.get("/api/v1/_test_not_found_domain_error")
    def _raise_not_found() -> None:
        raise NotFoundDomainError(
            message="Entity 'tx_custom_001' not found.",
            details={"entity_id": "tx_custom_001"},
        )

    resp = client.get("/api/v1/_test_not_found_domain_error")
    assert resp.status_code == 404
    data = resp.json()

    # Verify backwards-compatible string detail
    assert data["detail"] == "Entity 'tx_custom_001' not found."

    # Verify structured V2 error object
    assert "error" in data
    err = data["error"]
    assert err["code"] == "NOT_FOUND"
    assert err["status"] == 404
    assert err["message"] == "Entity 'tx_custom_001' not found."
    assert err["details"] == {"entity_id": "tx_custom_001"}
    assert "request_id" in err


def test_validation_domain_error_structure() -> None:
    """Validation domain errors must map to 422 with structured error payload."""

    @app.get("/api/v1/_test_validation_domain_error")
    def _raise_val_error() -> None:
        raise ValidationDomainError(
            message="Threshold out of allowable range.",
            details={"field": "fraud_threshold", "allowed": [0.0, 1.0]},
        )

    resp = client.get("/api/v1/_test_validation_domain_error")
    assert resp.status_code == 422
    data = resp.json()

    assert data["detail"] == "Threshold out of allowable range."
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["status"] == 422
    assert data["error"]["details"]["field"] == "fraud_threshold"
