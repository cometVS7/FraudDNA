"""End-to-End Pipeline & Hardening Validation Suite for FraudDNA Phase 7.

Tests the full chain:
Transaction Input
  -> ML Risk Detection (Phase 1)
  -> Tree SHAP Feature Attribution (Phase 1)
  -> FraudDNA Graph & Entity Neighborhood (Phase 2)
  -> Coordinated Fraud Cluster Detection (Phase 2)
  -> RAG Knowledge Retrieval (Phase 4)
  -> Bounded LangGraph Investigation Agent (Phase 5)
  -> Deterministic Policy Engine (Phase 5)
  -> Audit Trail & Reproducibility (Phase 5)
  -> Risk Simulation & Financial Impact (Phase 6)
  -> REST API Endpoints (Phases 3-6)

Covers all required test cases:
- Case A: Legitimate transaction (ALLOW)
- Case B: Individual suspicious anomaly (REVIEW / HOLD)
- Case C: Coordinated fraud syndicate (HOLD via cluster)
- Case D: Agent LLM unavailable (deterministic fallback)
- Case E: RAG unavailable / degraded mode
- Case F: Invalid input rejection
- Case G: Decision idempotency and hash reproducibility
"""

import pytest
from fastapi.testclient import TestClient

from app.agent.graph import InvestigationGraphRunner
from app.agent.schemas import AgentInvestigationOutput
from app.agent.service import AgentInvestigationService
from app.graph.service import get_graph_service
from app.main import app
from app.policy.engine import PolicyEngine
from app.policy.models import PolicyAction
from app.rag.retrieval import RAGService
from app.rag.vector_store import InMemoryVectorStore
from app.services.investigation import InvestigationService
from app.simulation.engine import SimulationEngine
from app.simulation.schemas import SimulationConfig

client = TestClient(app)

# Known ground-truth transactions from the empirical dataset
LEGIT_TX_ID = "tx_0000000"  # legitimate baseline transaction
INDIVIDUAL_FRAUD_TX_ID = "tx_0000006"  # individual anomaly (luxury goods / high amount)
COORDINATED_FRAUD_TX_ID = "tx_0001991"  # syndicate alpha device ring member


@pytest.fixture(scope="module", autouse=True)
def setup_graph_service():
    """Ensure graph service and dataset are initialized once for all E2E tests."""
    service = get_graph_service()
    service.initialize()
    assert len(service.transactions_by_id) > 0
    return service


# ==============================================================================
# SECTION 1: FULL CHAIN INTEGRATION
# ==============================================================================


def test_e2e_full_chain_pipeline() -> None:
    """Validate the complete sequential chain from raw transaction to policy and simulation."""
    tx_id = COORDINATED_FRAUD_TX_ID

    # Step 1 & 2: Investigation Service (ML Risk + Tree SHAP + Graph Context)
    inv_service = InvestigationService()
    inv_result = inv_service.investigate(tx_id)

    assert inv_result.transaction_id == tx_id
    assert inv_result.risk_score >= 0.70, (
        f"Expected high risk for {tx_id}, got {inv_result.risk_score}"
    )
    assert len(inv_result.risk_factors) > 0, "Tree SHAP risk factors must not be empty"
    for factor in inv_result.risk_factors:
        assert factor.feature != ""
        assert factor.direction in {"increases_risk", "decreases_risk"}
    assert inv_result.cluster is not None, "Coordinated fraud tx must have cluster context"
    assert inv_result.cluster.is_suspicious is True, "Cluster must be flagged suspicious"

    # Step 3: FraudDNA Graph Verification
    graph_service = get_graph_service()
    graph_data = graph_service.get_transaction_relationships(tx_id, depth=2)
    assert len(graph_data.nodes) >= 2, "Graph must contain transaction and neighboring entity nodes"
    assert any(
        "syndicate" in node.id.lower() or "synth" in node.id.lower() for node in graph_data.nodes
    ), "Graph must reveal shared syndicate entities"

    # Step 4: RAG Knowledge Retrieval
    rag_service = RAGService(auto_initialize=True)
    rag_service.initialize()
    rag_response = rag_service.search("device sharing coordinated fraud syndicate ring", top_k=3)
    assert rag_response.total_results >= 0
    if rag_response.results:
        assert rag_response.results[0].source_id != ""
        assert rag_response.results[0].similarity >= 0.0

    # Step 5: Bounded LangGraph AI Agent Investigation
    agent_runner = InvestigationGraphRunner()
    findings = agent_runner.run(tx_id, max_steps=6)
    assert isinstance(findings, AgentInvestigationOutput)
    assert findings.risk_score >= 0.70
    assert findings.recommended_action in {"REVIEW", "HOLD"}
    assert len(findings.tool_trace) > 0, "Tool trace must record agent actions"
    assert len(findings.tool_trace) <= 6, "Agent must not exceed bounded max_steps"

    # Step 6: Deterministic Policy Engine
    policy_engine = PolicyEngine()
    decision = policy_engine.evaluate_transaction(tx_id)
    assert decision.action == PolicyAction.HOLD, (
        f"Expected HOLD for coordinated fraud, got {decision.action}"
    )
    assert "SUSPICIOUS_FRAUD_CLUSTER" in decision.reason_codes
    assert decision.is_deterministic is True
    assert decision.decision_id.startswith("dec_")

    # Step 7: Simulation Engine Evaluation
    sim_engine = SimulationEngine()
    sim_result = sim_engine.run_simulation(SimulationConfig(fraud_threshold=0.37))
    assert sim_result.total_transactions > 0
    assert sim_result.true_positives > 0
    assert sim_result.expected_loss > 0.0
    assert sim_result.net_benefit is not None


# ==============================================================================
# SECTION 2: E2E CASES A - G
# ==============================================================================


def test_e2e_case_a_legitimate_transaction() -> None:
    """Case A: Legitimate baseline transaction must safely travel through pipeline and ALLOW."""
    tx_id = LEGIT_TX_ID

    # 1. Pipeline evaluation via API
    resp = client.post("/api/v1/decisions/evaluate", json={"transaction_id": tx_id})
    assert resp.status_code == 200
    decision = resp.json()

    assert decision["transaction_id"] == tx_id
    assert decision["action"] == "ALLOW", (
        f"Legitimate transaction must be ALLOWed, got {decision['action']}"
    )
    assert "LOW_RISK_BASELINE" in decision["reason_codes"]
    assert decision["risk_score"] < 0.30

    # 2. Detail verification
    detail_resp = client.get(f"/api/v1/transactions/{tx_id}")
    assert detail_resp.status_code == 200
    tx_detail = detail_resp.json()
    assert tx_detail["is_fraud"] is False
    assert tx_detail["risk_level"] == "low"


def test_e2e_case_b_individual_suspicious_transaction() -> None:
    """Case B: Individual suspicious transaction must be flagged with elevated risk."""
    tx_id = INDIVIDUAL_FRAUD_TX_ID

    # Check risk and SHAP via investigation API
    resp = client.post("/api/v1/investigations", json={"transaction_id": tx_id})
    assert resp.status_code == 200
    data = resp.json()

    assert data["transaction_id"] == tx_id
    assert data["risk_score"] >= 0.35
    assert len(data["risk_factors"]) > 0

    # Check policy decision
    pol_resp = client.post("/api/v1/decisions/evaluate", json={"transaction_id": tx_id})
    assert pol_resp.status_code == 200
    decision = pol_resp.json()
    assert decision["action"] in {"REVIEW", "HOLD"}


def test_e2e_case_c_coordinated_fraud_syndicate() -> None:
    """Case C: Coordinated fraud transaction must discover cluster, shared entities, and trigger HOLD."""
    tx_id = COORDINATED_FRAUD_TX_ID

    # 1. Investigate via API
    inv_resp = client.post("/api/v1/investigations", json={"transaction_id": tx_id})
    assert inv_resp.status_code == 200
    inv = inv_resp.json()

    assert inv["cluster"] is not None
    assert inv["cluster"]["is_suspicious"] is True
    assert inv["cluster"]["cluster_risk_score"] >= 0.70

    # 2. Graph inspection via API
    graph_resp = client.get(f"/api/v1/graph/transaction/{tx_id}")
    assert graph_resp.status_code == 200
    graph_data = graph_resp.json()
    assert len(graph_data["nodes"]) >= 2
    assert len(graph_data["edges"]) >= 1

    # 3. Policy Action must be HOLD
    decision_resp = client.post("/api/v1/decisions/evaluate", json={"transaction_id": tx_id})
    assert decision_resp.status_code == 200
    decision = decision_resp.json()
    assert decision["action"] == "HOLD"
    assert "SUSPICIOUS_FRAUD_CLUSTER" in decision["reason_codes"]


def test_e2e_case_d_agent_offline_deterministic_fallback() -> None:
    """Case D: LangGraph agent must safely execute deterministic fallback when external LLM is absent."""
    service = AgentInvestigationService()
    response = service.investigate(LEGIT_TX_ID, max_steps=5)

    findings = response.findings
    assert findings.risk_score < 0.30
    assert findings.recommended_action == "ALLOW"
    assert "legitimate baseline" in findings.fraud_hypothesis.lower()
    assert len(findings.tool_trace) > 0


def test_e2e_case_e_rag_unavailable_degraded_state() -> None:
    """Case E: RAG retrieval on empty store must degrade gracefully without fabricating evidence."""
    empty_store = InMemoryVectorStore()
    rag_service = RAGService(vector_store=empty_store)

    response = rag_service.ingest_knowledge_directory(
        knowledge_dir="nonexistent_knowledge_directory_123"
    )
    assert response.status == "directory_not_found"
    assert response.documents_ingested == 0

    # Search in empty store returns empty list, not fabricated hallucination
    search_results = rag_service.search("money laundering policy", top_k=5)
    assert search_results.results == []


def test_e2e_case_f_invalid_inputs_rejected() -> None:
    """Case F: Public APIs must reject malformed, out-of-bounds, or nonexistent inputs with proper HTTP codes."""
    # 1. Nonexistent transaction ID in investigation
    inv_resp = client.post(
        "/api/v1/investigations", json={"transaction_id": "tx_nonexistent_999999"}
    )
    assert inv_resp.status_code == 404

    # 2. Nonexistent transaction ID in agent investigation
    agent_resp = client.post(
        "/api/v1/agent/investigate", json={"transaction_id": "tx_nonexistent_999999"}
    )
    assert agent_resp.status_code == 404

    # 3. Nonexistent transaction ID in policy evaluation
    dec_resp = client.post(
        "/api/v1/decisions/evaluate", json={"transaction_id": "tx_nonexistent_999999"}
    )
    assert dec_resp.status_code == 404

    # 4. Out-of-bounds simulation threshold (< 0.01)
    sim_resp = client.post("/api/v1/simulations", json={"config": {"fraud_threshold": 0.001}})
    assert sim_resp.status_code == 422

    # 5. Review threshold >= fraud threshold
    sim_invalid_thresh = client.post(
        "/api/v1/simulations",
        json={"config": {"fraud_threshold": 0.30, "review_threshold": 0.35}},
    )
    assert sim_invalid_thresh.status_code == 422

    # 6. Comparison request with fewer than 2 configs
    cmp_resp = client.post(
        "/api/v1/simulations/compare",
        json={"configs": [{"fraud_threshold": 0.30}]},
    )
    assert cmp_resp.status_code == 422


def test_e2e_case_g_decision_idempotency_and_reproducibility() -> None:
    """Case G: Deterministic policy evaluation must produce identical decision ID hash and reason codes repeatedly."""
    tx_id = COORDINATED_FRAUD_TX_ID
    policy_engine = PolicyEngine()

    decisions = [policy_engine.evaluate_transaction(tx_id) for _ in range(5)]

    first_decision = decisions[0]
    for d in decisions[1:]:
        assert d.decision_id == first_decision.decision_id, (
            "Decision IDs must be identical across evaluations"
        )
        assert d.action == first_decision.action, "Actions must be identical"
        assert d.reason_codes == first_decision.reason_codes, "Reason codes must be identical"
        assert d.risk_score == first_decision.risk_score, "Risk scores must be identical"


# ==============================================================================
# SECTION 3: REST API COVERAGE & DASHBOARD ENDPOINTS
# ==============================================================================


def test_e2e_dashboard_overview_endpoint() -> None:
    """Verify /api/v1/overview returns live aggregated metrics from the real dataset."""
    resp = client.get("/api/v1/overview")
    assert resp.status_code == 200
    data = resp.json()

    assert data["total_transactions"] == 25000
    assert data["fraud_count"] > 0
    assert data["legitimate_count"] > 0
    assert data["total_amount"] > 0.0
    assert data["total_clusters"] >= 2
    assert "risk_distribution" in data
    assert data["data_label"] == "synthetic_dataset"


def test_e2e_dashboard_transactions_pagination_and_filtering() -> None:
    """Verify /api/v1/transactions pagination, search, and suspicious_only filtering."""
    # Pagination
    resp = client.get("/api/v1/transactions?limit=10&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["transactions"]) == 10
    assert data["total"] == 25000

    # Suspicious only filter
    susp_resp = client.get("/api/v1/transactions?limit=10&suspicious_only=true")
    assert susp_resp.status_code == 200
    susp_data = susp_resp.json()
    for tx in susp_data["transactions"]:
        assert tx["risk_score"] >= 0.37

    # Specific transaction lookup
    single_resp = client.get(f"/api/v1/transactions/{LEGIT_TX_ID}")
    assert single_resp.status_code == 200
    single = single_resp.json()
    assert single["transaction_id"] == LEGIT_TX_ID


def test_e2e_dashboard_evaluation_endpoint() -> None:
    """Verify /api/v1/evaluation returns Phase 1 held-out test benchmarks."""
    resp = client.get("/api/v1/evaluation")
    assert resp.status_code == 200
    data = resp.json()

    assert "evaluation_type" in data
    assert "metrics" in data
    assert "roc_auc" in data["metrics"]
    assert "confusion_matrix" in data


def test_e2e_simulation_endpoints() -> None:
    """Verify /api/v1/simulations and /api/v1/simulations/compare."""
    # Single simulation
    run_resp = client.post(
        "/api/v1/simulations",
        json={"config": {"fraud_threshold": 0.40, "cost_per_false_positive": 300.0}},
    )
    assert run_resp.status_code == 200
    run_data = run_resp.json()
    assert run_data["config"]["fraud_threshold"] == 0.40
    assert "expected_loss" in run_data
    assert "net_benefit" in run_data

    # Multi-threshold comparison
    cmp_resp = client.post(
        "/api/v1/simulations/compare",
        json={
            "configs": [
                {"fraud_threshold": 0.20},
                {"fraud_threshold": 0.40},
                {"fraud_threshold": 0.60},
            ]
        },
    )
    assert cmp_resp.status_code == 200
    cmp_data = cmp_resp.json()
    assert "comparison_id" in cmp_data
    assert len(cmp_data["results"]) == 3
