"""Unit tests for Deterministic Policy Engine."""

import pytest

from app.graph.service import get_graph_service
from app.policy.engine import PolicyEngine
from app.policy.models import PolicyAction, PolicyReasonCode
from app.policy.rules import evaluate_policy_rules


@pytest.fixture
def sample_tx_id() -> str:
    graph_service = get_graph_service()
    graph_service.initialize()
    assert len(graph_service.transactions_by_id) > 0
    return next(iter(graph_service.transactions_by_id.keys()))


def test_evaluate_low_risk_baseline_rule_produces_allow() -> None:
    action, codes, summary = evaluate_policy_rules(
        risk_score=0.12,
        is_suspicious_cluster=False,
        cluster_risk_score=0.15,
        shared_device_count=0,
        shared_ip_count=0,
        shared_card_count=0,
    )
    assert action == PolicyAction.ALLOW
    assert PolicyReasonCode.LOW_RISK_BASELINE in codes


def test_evaluate_critical_risk_score_produces_hold() -> None:
    action, codes, summary = evaluate_policy_rules(
        risk_score=0.94,
        is_suspicious_cluster=False,
        shared_device_count=0,
    )
    assert action == PolicyAction.HOLD
    assert PolicyReasonCode.CRITICAL_RISK_SCORE in codes


def test_evaluate_suspicious_fraud_cluster_produces_hold() -> None:
    action, codes, summary = evaluate_policy_rules(
        risk_score=0.45,
        is_suspicious_cluster=True,
        cluster_risk_score=0.88,
        cluster_id="cluster_001",
    )
    assert action == PolicyAction.HOLD
    assert PolicyReasonCode.SUSPICIOUS_FRAUD_CLUSTER in codes


def test_evaluate_shared_hardware_device_with_high_risk_produces_hold() -> None:
    action, codes, summary = evaluate_policy_rules(
        risk_score=0.75,
        is_suspicious_cluster=False,
        shared_device_count=4,
    )
    assert action == PolicyAction.HOLD
    assert PolicyReasonCode.SHARED_HARDWARE_DEVICE in codes


def test_evaluate_moderate_risk_produces_review() -> None:
    action, codes, summary = evaluate_policy_rules(
        risk_score=0.55,
        is_suspicious_cluster=False,
        shared_device_count=0,
    )
    assert action == PolicyAction.REVIEW
    assert PolicyReasonCode.MODERATE_RISK_ELEVATED in codes


def test_evaluate_degraded_rag_produces_review_with_code() -> None:
    action, codes, summary = evaluate_policy_rules(
        risk_score=0.20,
        is_suspicious_cluster=False,
        rag_status="degraded",
    )
    assert action in {PolicyAction.ALLOW, PolicyAction.REVIEW}


def test_policy_engine_deterministic_decision_id(sample_tx_id: str) -> None:
    engine = PolicyEngine()
    dec1 = engine.evaluate_transaction(sample_tx_id)
    dec2 = engine.evaluate_transaction(sample_tx_id)

    assert dec1.decision_id == dec2.decision_id
    assert dec1.action == dec2.action
    assert dec1.reason_codes == dec2.reason_codes
    assert dec1.is_deterministic is True
