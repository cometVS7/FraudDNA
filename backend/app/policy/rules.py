"""FraudDNA Deterministic Policy Engine Rules.

Implements pure, repeatable decision logic that maps ML scores, graph coordination,
and investigation evidence into ALLOW / REVIEW / HOLD actions.
"""

from app.policy.models import PolicyAction, PolicyReasonCode


def evaluate_policy_rules(
    risk_score: float,
    is_suspicious_cluster: bool = False,
    cluster_risk_score: float = 0.0,
    cluster_id: str | None = None,
    shared_device_count: int = 0,
    shared_ip_count: int = 0,
    shared_card_count: int = 0,
    rag_status: str = "active",
    investigation_status: str = "completed",
) -> tuple[PolicyAction, list[PolicyReasonCode], list[str]]:
    """Pure, deterministic policy evaluator mapping evidence signals to financial actions.

    Rules Precedence:
    1. HOLD:
       - Critical ML Risk (score >= 0.90)
       - Suspicious Fraud Cluster (is_suspicious=True AND cluster_risk >= 0.70)
       - Coordinated Sharing + High Risk (score >= 0.70 AND (shared_device > 0 OR shared_card > 0))
    2. ALLOW:
       - Low Risk Baseline (score < 0.30 AND not suspicious_cluster AND no shared devices/cards)
    3. REVIEW:
       - Moderate / Elevated Risk (0.30 <= score < 0.90)
       - Degraded Dependency / RAG unavailable
       - Investigation Fallback / High Uncertainty
    """
    reason_codes: list[PolicyReasonCode] = []
    evidence_summary: list[str] = []

    # 1. HOLD Evaluations
    if risk_score >= 0.90:
        reason_codes.append(PolicyReasonCode.CRITICAL_RISK_SCORE)
        evidence_summary.append(f"Critical transaction risk score: {risk_score:.4f} >= 0.90")

    if is_suspicious_cluster and cluster_risk_score >= 0.70:
        reason_codes.append(PolicyReasonCode.SUSPICIOUS_FRAUD_CLUSTER)
        evidence_summary.append(
            f"Belongs to suspicious cluster '{cluster_id}' with cluster risk {cluster_risk_score:.4f} >= 0.70"
        )

    if shared_device_count > 0:
        reason_codes.append(PolicyReasonCode.SHARED_HARDWARE_DEVICE)
        evidence_summary.append(
            f"Hardware device shared across {shared_device_count} distinct customer accounts"
        )

    if shared_card_count > 0:
        reason_codes.append(PolicyReasonCode.SHARED_PAYMENT_INSTRUMENT)
        evidence_summary.append(
            f"Payment card shared across {shared_card_count} distinct customer accounts"
        )

    if shared_ip_count >= 5:
        reason_codes.append(PolicyReasonCode.SHARED_IP_SUBNET)
        evidence_summary.append(
            f"High-density shared IP address ({shared_ip_count} connected accounts)"
        )

    # Check if HOLD condition triggered
    has_critical_score = PolicyReasonCode.CRITICAL_RISK_SCORE in reason_codes
    has_suspicious_cluster = PolicyReasonCode.SUSPICIOUS_FRAUD_CLUSTER in reason_codes
    has_high_score_with_sharing = risk_score >= 0.70 and (
        PolicyReasonCode.SHARED_HARDWARE_DEVICE in reason_codes
        or PolicyReasonCode.SHARED_PAYMENT_INSTRUMENT in reason_codes
    )

    if has_critical_score or has_suspicious_cluster or has_high_score_with_sharing:
        return PolicyAction.HOLD, reason_codes, evidence_summary

    # 2. ALLOW Evaluation
    has_shared_entities = (shared_device_count > 0) or (shared_card_count > 0)
    if risk_score < 0.30 and not is_suspicious_cluster and not has_shared_entities:
        reason_codes.append(PolicyReasonCode.LOW_RISK_BASELINE)
        evidence_summary.append(
            f"Low risk score: {risk_score:.4f} < 0.30 with no coordinated entity anomalies"
        )
        return PolicyAction.ALLOW, reason_codes, evidence_summary

    # 3. REVIEW Evaluation (All intermediate, uncertain, or degraded cases)
    if 0.30 <= risk_score < 0.70:
        reason_codes.append(PolicyReasonCode.MODERATE_RISK_ELEVATED)
        evidence_summary.append(f"Moderate elevated risk score: {risk_score:.4f} in [0.30, 0.70)")
    elif risk_score >= 0.70:
        reason_codes.append(PolicyReasonCode.HIGH_RISK_SCORE)
        evidence_summary.append(
            f"High risk score: {risk_score:.4f} in [0.70, 0.90) requiring analyst review"
        )

    if rag_status == "unavailable" or rag_status == "degraded":
        reason_codes.append(PolicyReasonCode.RAG_EVIDENCE_DEGRADED)
        evidence_summary.append("RAG policy/case evidence is operating in degraded mode")

    if investigation_status == "degraded" or investigation_status == "failed":
        reason_codes.append(PolicyReasonCode.INVESTIGATION_FALLBACK)
        evidence_summary.append("Investigation operated in fallback mode")

    if not reason_codes:
        reason_codes.append(PolicyReasonCode.POLICY_ESCALATION_REQUIRED)
        evidence_summary.append("Case requires manual review per default policy rule")

    return PolicyAction.REVIEW, reason_codes, evidence_summary
