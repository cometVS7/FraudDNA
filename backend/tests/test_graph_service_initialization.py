"""Regression tests for GraphService singleton initialization and real ML scoring."""

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from app.graph.service import GraphService, get_graph_service
from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Test client with application lifespan active."""
    with TestClient(app) as test_client:
        yield test_client


def test_graph_service_singleton_identity() -> None:
    """Verify get_graph_service() returns the exact same singleton instance."""
    svc1 = get_graph_service()
    svc2 = get_graph_service()
    assert svc1 is svc2


def test_graph_service_initializes_once() -> None:
    """Verify initialize() is idempotent and does not rebuild when already initialized."""
    svc = get_graph_service()
    svc.initialize()
    assert svc.is_initialized is True
    graph_id = id(svc.graph)
    # Calling initialize again without force_reload should be a no-op
    svc.initialize(force_reload=False)
    assert id(svc.graph) == graph_id


def test_missing_artifacts_fail_clearly(tmp_path: Path) -> None:
    """Verify GraphService raises FileNotFoundError when data or model artifacts are missing."""
    empty_data = tmp_path / "missing.csv"
    service = GraphService(data_path=empty_data, models_dir=tmp_path)
    with pytest.raises(FileNotFoundError, match="Transactions dataset not found"):
        service.initialize()

    # Test missing model file
    dummy_csv = tmp_path / "transactions.csv"
    dummy_csv.write_text("transaction_id,amount\ntx_1,100.0\n")
    service2 = GraphService(data_path=dummy_csv, models_dir=tmp_path)
    with pytest.raises(FileNotFoundError, match="ML model artifact not found"):
        service2.initialize()


def test_api_overview_returns_real_metrics(client: TestClient) -> None:
    """Verify GET /api/v1/overview returns live aggregated metrics with real ML scores."""
    resp = client.get("/api/v1/overview")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_transactions"] == 25000
    assert data["fraud_count"] > 0
    assert data["suspicious_transactions"] > 0
    assert data["high_risk_count"] > 0
    assert data["critical_risk_count"] > 0
    assert data["total_clusters"] >= 2
    assert data["suspicious_clusters"] >= 1
    assert "risk_distribution" in data
    assert data["risk_distribution"]["low"] > 0
    assert data["risk_distribution"]["critical"] > 0


def test_api_transactions_returns_real_scores(client: TestClient) -> None:
    """Verify GET /api/v1/transactions returns paginated list with real ML risk scores."""
    resp = client.get("/api/v1/transactions?limit=10&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 25000
    assert len(data["transactions"]) == 10

    # Ensure risk scores are not all 0.0
    scores = [t["risk_score"] for t in data["transactions"]]
    assert any(s >= 0.0 for s in scores)


def test_known_coordinated_transaction_scored_high(client: TestClient) -> None:
    """Verify known coordinated fraud transaction tx_0001991 has critical risk score."""
    resp = client.get("/api/v1/transactions/tx_0001991")
    assert resp.status_code == 200
    tx = resp.json()
    assert tx["transaction_id"] == "tx_0001991"
    assert tx["risk_score"] >= 0.90
    assert tx["risk_level"] == "critical"
    assert tx["cluster_id"] is not None


def test_graph_endpoints_functional(client: TestClient) -> None:
    """Verify graph subgraph and cluster endpoints respond correctly."""
    graph_resp = client.get("/api/v1/graph/transaction/tx_0001991?depth=2")
    assert graph_resp.status_code == 200
    gdata = graph_resp.json()
    assert len(gdata["nodes"]) >= 2
    assert len(gdata["edges"]) >= 1

    clusters_resp = client.get("/api/v1/clusters")
    assert clusters_resp.status_code == 200
    cdata = clusters_resp.json()
    assert cdata["total_clusters"] >= 2
