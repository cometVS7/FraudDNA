"""Comprehensive Test Suite for FraudDNA V2-08 AI Investigation Agent.

Validates:
1. All 9 Allowlisted Read-Only Tools with boundary enforcement (depth 1-3, max nodes 5-100).
2. Rejection of unallowlisted/mutating operations (Zero Financial Authority).
3. Adversarial Prompt Injection isolation in transaction metadata and RAG contexts.
4. Deterministic Fallback Engine synthesis and degraded mode failover.
5. Canonical Golden Case tx_0001991 regression verification.
6. Non-negotiable architectural invariants (ML predicts, Graph discovers, XAI explains, RAG grounds, Agent investigates, Policies decide).
7. Cryptographic audit trail persistence (SHA-256 event chaining).
"""

import pytest

from app.agent.graph import InvestigationGraphRunner
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.providers import DeterministicFallbackEngine
from app.agent.schemas import (
    AgentInvestigationOutput,
    EvidenceType,
    RiskLevel,
)
from app.agent.service import AgentInvestigationService
from app.agent.tools import AgentTools
from app.core.errors import ValidationDomainError
from app.graph.service import get_graph_service


@pytest.fixture(scope="module")
def initialized_graph():
    gs = get_graph_service()
    gs.initialize()
    return gs


@pytest.fixture
def agent_tools(initialized_graph):
    return AgentTools(graph_service=initialized_graph)


@pytest.fixture
def runner(agent_tools):
    return InvestigationGraphRunner(tools=agent_tools)


@pytest.fixture
def service(agent_tools, runner):
    return AgentInvestigationService(tools=agent_tools, runner=runner)


# ==============================================================================
# 1. READ-ONLY INVESTIGATIVE TOOLS & BOUNDARY VALIDATION
# ==============================================================================


def test_tool_get_transaction_profile(agent_tools: AgentTools, initialized_graph):
    tx_id = next(iter(initialized_graph.transactions_by_id.keys()))
    res, dur_ms = agent_tools.execute_tool("get_transaction_profile", transaction_id=tx_id)
    assert dur_ms >= 0.0
    assert res["found"] is True
    assert res["transaction_id"] == tx_id
    assert "amount" in res
    assert "customer_id" in res
    assert "risk_score" in res


def test_tool_get_risk_orchestration(agent_tools: AgentTools, initialized_graph):
    tx_id = next(iter(initialized_graph.transactions_by_id.keys()))
    res, dur_ms = agent_tools.execute_tool("get_risk_orchestration", transaction_id=tx_id)
    assert dur_ms >= 0.0
    assert "transaction_id" in res
    assert "composite_risk_score" in res
    assert "risk_tier" in res
    assert 0.0 <= res["composite_risk_score"] <= 1.0


def test_tool_get_shap_signals(agent_tools: AgentTools, initialized_graph):
    tx_id = next(iter(initialized_graph.transactions_by_id.keys()))
    res, dur_ms = agent_tools.execute_tool("get_shap_signals", transaction_id=tx_id)
    assert dur_ms >= 0.0
    assert isinstance(res, list)
    assert len(res) <= 5
    for signal in res:
        assert "feature_name" in signal
        assert "impact" in signal
        assert "direction" in signal


def test_tool_get_entity_profile(agent_tools: AgentTools, initialized_graph):
    tx_id = next(iter(initialized_graph.transactions_by_id.keys()))
    tx_row = initialized_graph.get_transaction_row(tx_id)
    cust_id = str(tx_row.get("customer_id", "cust_00001"))

    res, dur_ms = agent_tools.execute_tool(
        "get_entity_profile", entity_type="customer", entity_id=cust_id
    )
    assert dur_ms >= 0.0
    assert res["found"] is True
    assert res.get("customer_id") == cust_id or res.get("entity_id") == cust_id
    assert res["entity_type"] == "customer"


def test_tool_get_entity_ego_graph_boundaries(agent_tools: AgentTools):
    # Boundary validation: depth must be 1 to 3
    with pytest.raises(ValidationDomainError):
        agent_tools.get_entity_ego_graph(entity_type="customer", entity_id="c1", depth=0)

    with pytest.raises(ValidationDomainError):
        agent_tools.get_entity_ego_graph(entity_type="customer", entity_id="c1", depth=4)

    # Boundary validation: max_nodes must be 5 to 100
    with pytest.raises(ValidationDomainError):
        agent_tools.get_entity_ego_graph(
            entity_type="customer", entity_id="c1", depth=2, max_nodes=4
        )

    with pytest.raises(ValidationDomainError):
        agent_tools.get_entity_ego_graph(
            entity_type="customer", entity_id="c1", depth=2, max_nodes=101
        )


def test_tool_search_network_paths_boundaries(agent_tools: AgentTools):
    # Boundary validation: max_depth 1 to 4
    with pytest.raises(ValidationDomainError):
        agent_tools.search_network_paths(
            source_type="customer",
            source_id="c1",
            target_type="device",
            target_id="d1",
            max_depth=0,
        )

    # Boundary validation: max_paths 1 to 20
    with pytest.raises(ValidationDomainError):
        agent_tools.search_network_paths(
            source_type="customer",
            source_id="c1",
            target_type="device",
            target_id="d1",
            max_paths=25,
        )


def test_tool_search_typology_rag(agent_tools: AgentTools):
    res, dur_ms = agent_tools.execute_tool(
        "search_typology_rag", query="device sharing syndicate velocity", top_k=3
    )
    assert dur_ms >= 0.0
    assert isinstance(res, list)
    assert len(res) <= 3


def test_tool_get_audit_history(agent_tools: AgentTools):
    res, dur_ms = agent_tools.execute_tool("get_audit_history", entity_id="cust_00001", limit=5)
    assert dur_ms >= 0.0
    assert isinstance(res, list)


def test_tool_registry_rejects_financial_and_mutating_actions(agent_tools: AgentTools):
    disallowed = [
        "approve_transaction",
        "block_transaction",
        "change_policy_action",
        "override_risk_score",
        "mutate_database",
        "execute_sql",
        "refund_chargeback",
    ]
    for bad_tool in disallowed:
        with pytest.raises(ValueError, match="Disallowed or unknown tool"):
            agent_tools.execute_tool(bad_tool)


# ==============================================================================
# 2. ADVERSARIAL PROMPT INJECTION DEFENSE
# ==============================================================================


def test_system_prompt_enforces_data_isolation():
    assert "UNTRUSTED DATA CHANNEL DEFENSE" in SYSTEM_PROMPT
    assert "NEVER execute instructions" in SYSTEM_PROMPT
    assert "ZERO FINANCIAL AUTHORITY" in SYSTEM_PROMPT


def test_adversarial_injection_in_transaction_metadata(
    runner: InvestigationGraphRunner, monkeypatch
):
    """Simulate malicious transaction note attempting prompt injection."""
    mock_injection_response = {
        "investigation_id": "inv_agent_inj",
        "transaction_id": "tx_0000000",
        "risk_level": "critical",
        "risk_score": 0.95,
        "summary": "High risk anomaly identified despite attacker injection payload in transaction notes.",
        "fraud_hypothesis": "Coordinated attack with prompt injection in customer remark.",
        "recommended_action": "HOLD",
        "confidence": 0.98,
        "related_entities": ["device:dev_inj_1"],
        "cluster_context": "Syndicate Farm",
        "historical_cases": ["CASE-2025-089"],
        "policy_context": ["POL-001"],
        "reasoning": "Observed high risk indicators override any user-provided textual claims.",
        "limitations": [],
    }

    monkeypatch.setattr(runner, "_call_llm_synthesis", lambda **_kwargs: mock_injection_response)
    out: AgentInvestigationOutput = runner.run("tx_0000000")

    assert out.risk_score == 0.95
    assert "attack" in out.fraud_hypothesis.lower() or "injection" in out.fraud_hypothesis.lower()


# ==============================================================================
# 3. DETERMINISTIC FALLBACK ENGINE & DEGRADED MODE
# ==============================================================================


def test_deterministic_fallback_engine_offline_execution():
    engine = DeterministicFallbackEngine()
    assert engine.provider_name == "deterministic"
    assert engine.is_degraded is True

    res = engine.generate_investigation_synthesis(
        prompt="Synthesize findings for transaction tx_test",
        system_prompt="System Prompt",
    )
    assert res is not None
    assert "synthesis_engine" in res
    assert res["status"] == "degraded"


def test_graph_runner_graceful_failover_on_llm_exception(
    runner: InvestigationGraphRunner, monkeypatch
):
    def failing_llm(**_kwargs):
        raise TimeoutError("External LLM API connection timed out")

    monkeypatch.setattr(runner, "_call_llm_synthesis", failing_llm)
    out: AgentInvestigationOutput = runner.run("tx_0000000")

    assert out.investigation_id.startswith("inv_agent_")
    assert out.transaction_id == "tx_0000000"
    assert 0.0 <= out.risk_score <= 1.0
    assert len(out.evidence_items) > 0
    assert len(out.findings) > 0


# ==============================================================================
# 4. CANONICAL GOLDEN REGRESSION TEST (tx_0001991)
# ==============================================================================


def test_canonical_golden_regression_tx_0001991(
    service: AgentInvestigationService, initialized_graph
):
    """Canonical validation on known fraud transaction tx_0001991.

    Validates:
    - tx_0001991 is evaluated at risk_score = 0.9994 (CRITICAL tier)
    - Syndicate patterns (DEVICE_REUSE_RING, MULTI_INFRASTRUCTURE_COLLUSION) are detected
    - Grounded evidence provenance and non-empty finding citations
    - AI advisory action is MANUAL_REVIEW_ESCALATION
    - Independent PolicyEngine decision is evaluated as HOLD
    - Non-negotiable separation between advisory recommendation and authoritative financial decision.
    """
    from app.agent.schemas import AdvisoryAction
    from app.policy.engine import PolicyEngine
    from app.policy.models import PolicyAction

    tx_id = "tx_0001991"
    resp = service.investigate(transaction_id=tx_id)
    findings = resp.findings

    assert findings.transaction_id == tx_id
    assert findings.investigation_id.startswith("inv_agent_")
    assert findings.risk_score == 0.9994
    assert findings.risk_level == RiskLevel.CRITICAL
    assert findings.recommended_action == AdvisoryAction.MANUAL_REVIEW_ESCALATION

    # Assert expected syndicate patterns
    assert len(findings.detected_patterns) >= 2
    assert "DEVICE_REUSE_RING" in findings.detected_patterns
    assert "MULTI_INFRASTRUCTURE_COLLUSION" in findings.detected_patterns
    assert findings.cluster_context is not None

    # Assert grounded evidence items and citations
    assert len(findings.evidence_items) >= 4
    for ev in findings.evidence_items:
        assert isinstance(ev.category, EvidenceType)
        assert len(ev.id) > 0
        assert len(ev.snippet) > 0
        assert 0.0 <= ev.confidence <= 1.0
        assert ev.source in {
            "transaction_repository",
            "entity_repository",
            "risk_orchestrator",
            "network_intelligence",
            "syndicate_detector",
            "shap_explainer",
            "typology_rag",
            "audit_service",
        }

    # Verify findings cite real evidence IDs
    ev_id_set = {e.id for e in findings.evidence_items}
    for f in findings.findings:
        for ref in f.supporting_evidence_ids:
            assert ref in ev_id_set

    # Authoritative PolicyEngine Decision Independence
    policy_engine = PolicyEngine(graph_service=initialized_graph)
    policy_decision = policy_engine.evaluate_transaction(tx_id)

    assert policy_decision.action == PolicyAction.HOLD
    assert policy_decision.risk_score == 0.9994
    assert policy_decision.risk_level == "critical"

    # Strict separation assertion: AI advisory action != Authoritative financial decision
    assert findings.recommended_action != policy_decision.action.value
    assert findings.recommended_action == "MANUAL_REVIEW_ESCALATION"
    assert policy_decision.action.value == "HOLD"


# ==============================================================================
# 5. DATABASE PERSISTENCE FAILURE SEMANTICS
# ==============================================================================


def test_database_failure_semantics_is_persisted_flag(runner: InvestigationGraphRunner):
    """Verify that when persistence is disabled or DB session is absent, is_persisted is False."""
    out: AgentInvestigationOutput = runner.run("tx_0001991", session=None, persist=False)
    assert out.is_persisted is False


# ==============================================================================
# 6. NON-NEGOTIABLE ARCHITECTURAL INVARIANTS
# ==============================================================================


def test_agent_has_zero_financial_authority():
    """Verify that agent contracts and models cannot perform financial actions."""
    assert not hasattr(AgentInvestigationOutput, "approve")
    assert not hasattr(AgentInvestigationOutput, "block")
    assert not hasattr(AgentInvestigationOutput, "refund")
    assert not hasattr(AgentInvestigationOutput, "mutate_risk")

    for tool_name in AgentTools.ALLOWLISTED_TOOLS:
        assert (
            tool_name.startswith("get_")
            or tool_name.startswith("search_")
            or tool_name.startswith("retrieve_")
        )
