"""FraudDNA Advanced Multi-Layer Risk Orchestration Service.

Combines four inspectable risk layers:
1. Transaction Risk (LightGBM ML + Tree SHAP attributions)
2. Entity Risk (Persistent profile risk + cross-account sharing anomalies)
3. Network Risk (Fraud syndicate cluster membership + exposure)
4. Behavioral Risk (Point-in-time velocity acceleration + temporal anomalies)

Computes deterministic composite risk, evidence-completeness confidence, structured
signal taxonomy, and multi-layer natural explanations.
"""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundDomainError, ValidationDomainError
from app.models.domain import (
    TransactionModel,
)
from app.policy.rules import evaluate_policy_rules
from app.repositories.entity_repository import EntityRepository
from app.repositories.network_repository import NetworkRepository
from app.schemas.risk import (
    BehavioralRiskContext,
    ConfidenceBreakdown,
    EntityRiskContext,
    NetworkRiskContext,
    RiskIntelligenceResponse,
    RiskLayerContribution,
    SignalCategory,
    SignalDirection,
    StructuredRiskSignal,
    TransactionRiskContext,
)
from app.services.entity import EntityService
from app.services.network import NetworkService
from app.services.risk import RiskService

logger = logging.getLogger(__name__)

# Server-controlled deterministic layer weights
W_TRANSACTION: float = 0.45
W_ENTITY: float = 0.20
W_NETWORK: float = 0.20
W_BEHAVIOR: float = 0.15


class RiskOrchestrator:
    """Coordinates deterministic multi-layer risk intelligence synthesis."""

    def __init__(
        self,
        risk_service: RiskService | None = None,
        entity_service: EntityService | None = None,
        network_service: NetworkService | None = None,
        entity_repo: EntityRepository | None = None,
        network_repo: NetworkRepository | None = None,
    ) -> None:
        self.risk_service = risk_service or RiskService()
        self.entity_service = entity_service or EntityService()
        self.network_service = network_service or NetworkService()
        self.entity_repo = entity_repo or EntityRepository()
        self.network_repo = network_repo or NetworkRepository()

    def orchestrate_transaction_risk(
        self,
        session: Session,
        transaction_id: str,
        as_of: datetime | None = None,
        weights: dict[str, float] | None = None,
        persist_assessment: bool = False,
    ) -> RiskIntelligenceResponse:
        """Synthesize composite multi-layer risk intelligence for a transaction."""
        # Validate weights if explicitly provided
        w_tx = W_TRANSACTION
        w_ent = W_ENTITY
        w_net = W_NETWORK
        w_beh = W_BEHAVIOR
        if weights is not None:
            required = {"transaction", "entity", "network", "behavioral"}
            if set(weights.keys()) != required:
                raise ValidationDomainError(
                    f"Weights must specify exactly: {required}",
                    details={"provided_keys": list(weights.keys())},
                )
            if abs(sum(weights.values()) - 1.0) > 1e-4:
                raise ValidationDomainError(
                    f"Weights must sum to 1.0, got {sum(weights.values()):.4f}",
                    details={"sum": sum(weights.values())},
                )
            w_tx = weights["transaction"]
            w_ent = weights["entity"]
            w_net = weights["network"]
            w_beh = weights["behavioral"]

        # 1. Retrieve authoritative transaction
        tx_stmt = select(TransactionModel).where(TransactionModel.id == transaction_id)
        tx = session.execute(tx_stmt).scalar_one_or_none()
        if not tx:
            raise NotFoundDomainError(
                f"Transaction '{transaction_id}' not found.",
                details={"transaction_id": transaction_id},
            )

        as_of_time = as_of or tx.timestamp
        degradation_reasons: list[str] = []
        is_degraded = False

        # ----------------------------------------------------------------------
        # LAYER 1: Transaction Risk (LightGBM ML + Tree SHAP)
        # ----------------------------------------------------------------------
        tx_assessment = self.risk_service.get_latest_for_transaction(session, transaction_id)
        tx_signals: list[StructuredRiskSignal] = []

        if tx_assessment:
            tx_score = float(tx_assessment.risk_score)
            tx_tier = tx_assessment.risk_tier
            model_ver = tx_assessment.model_version
            c_model = 1.0

            # Convert persisted SHAP signals
            if tx_assessment.signals:
                for sig in sorted(tx_assessment.signals, key=lambda s: s.rank)[:5]:
                    impact_val = float(sig.impact)
                    direction = (
                        SignalDirection.INCREASES_RISK
                        if impact_val > 0
                        else SignalDirection.DECREASES_RISK
                    )
                    tx_signals.append(
                        StructuredRiskSignal(
                            category=SignalCategory.TRANSACTION_SIGNAL,
                            name=sig.feature_name,
                            value=float(sig.feature_value),
                            impact=round(abs(impact_val), 4),
                            direction=direction,
                            source="ML_TREE_SHAP",
                            evidence_reference=tx_assessment.id,
                            description=(
                                f"Feature '{sig.feature_name}'={sig.feature_value:.2f} "
                                f"{'elevates' if impact_val > 0 else 'reduces'} transaction risk by {abs(impact_val):.4f}"
                            ),
                        )
                    )
        else:
            # Fallback to transaction model attributes if assessment not yet created
            tx_score = float(tx.risk_score)
            tx_tier = tx.risk_tier
            model_ver = "lightgbm_v010"
            c_model = 0.90

        tx_explanation = f"Transaction predictive score {tx_score:.4f} ({tx_tier}) evaluated by model '{model_ver}'."
        if tx_signals:
            top_signal = tx_signals[0]
            tx_explanation += (
                f" Primary predictive driver: {top_signal.name} (impact: {top_signal.impact:.4f})."
            )

        tx_context = TransactionRiskContext(
            score=round(tx_score, 4),
            risk_tier=tx_tier,
            model_version=model_ver,
            operating_threshold=0.37,
            signals=tx_signals,
            explanation=tx_explanation,
        )

        # ----------------------------------------------------------------------
        # LAYER 2: Entity Risk (Customer + Connected Instruments)
        # ----------------------------------------------------------------------
        entity_signals: list[StructuredRiskSignal] = []
        entity_components: dict[str, float] = {}
        c_entity = 0.0

        try:
            cust_profile = self.entity_service.get_customer_profile(
                session, tx.customer_id, as_of=as_of_time
            )
            entity_score = (
                cust_profile.risk_aggregation.risk_score
                if cust_profile.risk_aggregation
                else cust_profile.risk_score
            )
            entity_tier = (
                cust_profile.risk_aggregation.risk_tier
                if cust_profile.risk_aggregation
                else cust_profile.risk_tier
            )
            c_entity = 1.0

            if cust_profile.risk_aggregation:
                entity_components = {
                    "max_tx_risk": cust_profile.risk_aggregation.max_tx_risk,
                    "avg_top3_tx_risk": cust_profile.risk_aggregation.avg_top3_tx_risk,
                    "network_exposure": cust_profile.risk_aggregation.network_exposure,
                    "sharing_anomaly": cust_profile.risk_aggregation.sharing_anomaly,
                }
                if cust_profile.risk_aggregation.sharing_anomaly > 0:
                    entity_signals.append(
                        StructuredRiskSignal(
                            category=SignalCategory.ENTITY_SIGNAL,
                            name="SHARED_INFRASTRUCTURE_ANOMALY",
                            value=cust_profile.risk_aggregation.sharing_anomaly,
                            impact=round(cust_profile.risk_aggregation.sharing_anomaly, 4),
                            direction=SignalDirection.INCREASES_RISK,
                            source="ENTITY_GRAPH",
                            evidence_reference=tx.customer_id,
                            description=f"Customer '{tx.customer_id}' shares hardware devices or cards with other accounts.",
                        )
                    )
                if cust_profile.risk_aggregation.max_tx_risk >= 0.70:
                    entity_signals.append(
                        StructuredRiskSignal(
                            category=SignalCategory.ENTITY_SIGNAL,
                            name="HISTORICAL_HIGH_RISK_EXPOSURE",
                            value=cust_profile.risk_aggregation.max_tx_risk,
                            impact=round(cust_profile.risk_aggregation.max_tx_risk, 4),
                            direction=SignalDirection.INCREASES_RISK,
                            source="ENTITY_GRAPH",
                            evidence_reference=tx.customer_id,
                            description=f"Customer exhibits prior high-risk transactions (max score: {cust_profile.risk_aggregation.max_tx_risk:.4f}).",
                        )
                    )
            entity_explanation = (
                f"Customer '{tx.customer_id}' entity risk evaluated at {entity_score:.4f} ({entity_tier}) "
                f"across {cust_profile.total_transactions} historical transactions."
            )
        except Exception as e:
            logger.warning(
                f"Failed to retrieve entity profile for customer '{tx.customer_id}': {e}"
            )
            entity_score = 0.0
            entity_tier = "LOW"
            c_entity = 0.0
            is_degraded = True
            degradation_reasons.append(f"Entity profile unavailable: {e}")
            entity_explanation = (
                f"Entity profile for customer '{tx.customer_id}' could not be verified."
            )

        entity_context = EntityRiskContext(
            score=round(entity_score, 4),
            risk_tier=entity_tier,
            primary_customer_id=tx.customer_id,
            associated_device_id=tx.device_id,
            associated_card_id=tx.card_id,
            associated_ip_id=tx.ip_id,
            signals=entity_signals,
            risk_components=entity_components,
            explanation=entity_explanation,
        )

        # ----------------------------------------------------------------------
        # LAYER 3: Network Risk (Syndicate Clusters)
        # ----------------------------------------------------------------------
        network_signals: list[StructuredRiskSignal] = []
        network_score = 0.0
        is_suspicious_net = False
        exposure_amt = 0.0
        member_counts: dict[str, int] = {}
        primary_reason: str | None = None
        c_network = 1.0  # Successfully verified presence or absence

        if tx.network_id:
            net = self.network_repo.get_by_id(session, tx.network_id)
            if net:
                network_score = float(net.risk_score)
                is_suspicious_net = net.is_suspicious
                exposure_amt = float(net.total_amount)
                primary_reason = net.primary_reason
                member_counts = {
                    "customers": net.customer_count,
                    "devices": net.device_count,
                    "cards": net.card_count,
                    "ips": net.ip_count,
                    "transactions": net.transaction_count,
                }
                if is_suspicious_net:
                    network_signals.append(
                        StructuredRiskSignal(
                            category=SignalCategory.NETWORK_SIGNAL,
                            name="SUSPICIOUS_NETWORK_MEMBERSHIP",
                            value=network_score,
                            impact=round(network_score, 4),
                            direction=SignalDirection.INCREASES_RISK,
                            source="RISK_NETWORK_GRAPH",
                            evidence_reference=tx.network_id,
                            description=(
                                f"Member of suspicious fraud syndicate '{tx.network_id}' "
                                f"({net.customer_count} accounts, {net.device_count} devices, INR {exposure_amt:,.2f} exposure)."
                            ),
                        )
                    )
                if net.device_count < net.customer_count and net.device_count > 0:
                    network_signals.append(
                        StructuredRiskSignal(
                            category=SignalCategory.NETWORK_SIGNAL,
                            name="COORDINATED_DEVICE_SHARING",
                            value=float(net.customer_count - net.device_count),
                            impact=0.35,
                            direction=SignalDirection.INCREASES_RISK,
                            source="RISK_NETWORK_GRAPH",
                            evidence_reference=tx.network_id,
                            description=f"{net.customer_count} distinct customers operate across only {net.device_count} devices.",
                        )
                    )
                net_explanation = (
                    f"Transaction belongs to risk network '{tx.network_id}' (risk: {network_score:.4f}, "
                    f"suspicious={is_suspicious_net}). Pattern: {primary_reason or 'Coordinated abuse'}."
                )
            else:
                net_explanation = (
                    f"Referenced risk network '{tx.network_id}' not found in registry."
                )
        else:
            net_explanation = (
                "Transaction does not belong to any detected fraud syndicate or risk network."
            )

        network_context = NetworkRiskContext(
            score=round(network_score, 4),
            network_id=tx.network_id,
            is_suspicious=is_suspicious_net,
            exposure_amount=round(exposure_amt, 2),
            member_counts=member_counts,
            signals=network_signals,
            primary_reason=primary_reason,
            explanation=net_explanation,
        )

        # ----------------------------------------------------------------------
        # LAYER 4: Behavioral Risk (Point-in-Time Velocity & Acceleration)
        # ----------------------------------------------------------------------
        behavior_signals: list[StructuredRiskSignal] = []
        c_behavior = 1.0

        try:
            behavior_data = self.entity_repo.get_behavioral_metrics(
                session=session,
                entity_type="customer",
                entity_id=tx.customer_id,
                as_of=as_of_time,
            )
            tx_count_5m = behavior_data["tx_count_5m"]
            tx_count_1h = behavior_data["tx_count_1h"]
            tx_count_24h = behavior_data["tx_count_24h"]
            amount_1h = behavior_data["amount_1h"]
            amount_24h = behavior_data["amount_24h"]
            cross_sharing = behavior_data["cross_customer_sharing_count"]

            # Compute normalized behavioral risk score deterministically
            freq_score = 0.0
            if tx_count_5m >= 3:
                freq_score = 0.50
                behavior_signals.append(
                    StructuredRiskSignal(
                        category=SignalCategory.BEHAVIOR_SIGNAL,
                        name="HIGH_BURST_VELOCITY_5M",
                        value=float(tx_count_5m),
                        impact=0.50,
                        direction=SignalDirection.INCREASES_RISK,
                        source="BEHAVIORAL_ENGINE",
                        evidence_reference=tx.customer_id,
                        description=f"Rapid velocity: {tx_count_5m} transactions executed within the last 5 minutes.",
                    )
                )
            elif tx_count_1h >= 5:
                freq_score = 0.30
                behavior_signals.append(
                    StructuredRiskSignal(
                        category=SignalCategory.BEHAVIOR_SIGNAL,
                        name="ELEVATED_HOURLY_VELOCITY",
                        value=float(tx_count_1h),
                        impact=0.30,
                        direction=SignalDirection.INCREASES_RISK,
                        source="BEHAVIORAL_ENGINE",
                        evidence_reference=tx.customer_id,
                        description=f"{tx_count_1h} transactions executed in the last 1 hour.",
                    )
                )

            amt_score = 0.0
            if amount_1h >= 50000:
                amt_score = 0.40
                behavior_signals.append(
                    StructuredRiskSignal(
                        category=SignalCategory.BEHAVIOR_SIGNAL,
                        name="RAPID_MONETARY_OUTFLOW",
                        value=amount_1h,
                        impact=0.40,
                        direction=SignalDirection.INCREASES_RISK,
                        source="BEHAVIORAL_ENGINE",
                        evidence_reference=tx.customer_id,
                        description=f"High hourly outflow: INR {amount_1h:,.2f} spent in the last 1 hour.",
                    )
                )

            sharing_score = min(0.40, float(cross_sharing) * 0.20)
            if cross_sharing > 0:
                behavior_signals.append(
                    StructuredRiskSignal(
                        category=SignalCategory.BEHAVIOR_SIGNAL,
                        name="INFRASTRUCTURE_COLLUSION_SHARING",
                        value=float(cross_sharing),
                        impact=sharing_score,
                        direction=SignalDirection.INCREASES_RISK,
                        source="BEHAVIORAL_ENGINE",
                        evidence_reference=tx.customer_id,
                        description=f"Infrastructure connected to {cross_sharing} other distinct customer account(s).",
                    )
                )

            behavior_score = min(1.0, max(0.0, freq_score + amt_score + sharing_score))
            behavior_explanation = (
                f"Observed {tx_count_24h} transactions in 24h totaling INR {amount_24h:,.2f} "
                f"({tx_count_1h} in last hour, {tx_count_5m} in last 5m)."
            )
        except Exception as e:
            logger.warning(f"Failed to calculate behavioral metrics: {e}")
            tx_count_5m = 0
            tx_count_1h = 0
            tx_count_24h = 0
            amount_1h = 0.0
            amount_24h = 0.0
            cross_sharing = 0
            behavior_score = 0.0
            c_behavior = 0.0
            is_degraded = True
            degradation_reasons.append(f"Behavioral history unavailable: {e}")
            behavior_explanation = "Behavioral velocity window could not be determined."

        behavioral_context = BehavioralRiskContext(
            score=round(behavior_score, 4),
            as_of=as_of_time,
            tx_count_5m=tx_count_5m,
            tx_count_1h=tx_count_1h,
            tx_count_24h=tx_count_24h,
            amount_1h=round(amount_1h, 2),
            amount_24h=round(amount_24h, 2),
            cross_customer_sharing_count=cross_sharing,
            signals=behavior_signals,
            explanation=behavior_explanation,
        )

        # ----------------------------------------------------------------------
        # COMPOSITE RISK CALCULATION & ORCHESTRATION
        # ----------------------------------------------------------------------
        raw_composite = (
            w_tx * tx_score + w_ent * entity_score + w_net * network_score + w_beh * behavior_score
        )

        # Coordinated ring escalation invariant:
        # If transaction is in a suspicious network and has high transaction risk,
        # composite risk must reflect critical syndicate threat (>= 0.90).
        if is_suspicious_net and network_score >= 0.70 and tx_score >= 0.70:
            composite_score = round(min(1.0, max(raw_composite, 0.90)), 4)
        else:
            composite_score = round(min(1.0, max(0.0, raw_composite)), 4)

        # Calibrate risk tier
        if composite_score >= 0.90:
            composite_tier = "CRITICAL"
        elif composite_score >= 0.70:
            composite_tier = "HIGH"
        elif composite_score >= 0.30:
            composite_tier = "MEDIUM"
        else:
            composite_tier = "LOW"

        # Evidence completeness & confidence
        confidence_val = round(
            0.30 * c_model + 0.25 * c_entity + 0.20 * c_network + 0.25 * c_behavior, 4
        )

        confidence_breakdown = ConfidenceBreakdown(
            confidence_score=confidence_val,
            evidence_completeness=confidence_val,
            model_available=c_model > 0,
            entity_context_verified=c_entity > 0,
            network_context_verified=c_network > 0,
            behavioral_history_sufficient=c_behavior > 0,
            is_degraded=is_degraded,
            degradation_reasons=degradation_reasons,
        )

        # Layer contribution breakdown
        contribution_breakdown = [
            RiskLayerContribution(
                layer_name="transaction",
                score=tx_context.score,
                weight=w_tx,
                contribution=round(tx_context.score * w_tx, 4),
                evidence_completeness=c_model,
                source=f"LightGBM ({model_ver})",
                explanation=tx_context.explanation,
            ),
            RiskLayerContribution(
                layer_name="entity",
                score=entity_context.score,
                weight=w_ent,
                contribution=round(entity_context.score * w_ent, 4),
                evidence_completeness=c_entity,
                source="EntityService_V2",
                explanation=entity_context.explanation,
            ),
            RiskLayerContribution(
                layer_name="network",
                score=network_context.score,
                weight=w_net,
                contribution=round(network_context.score * w_net, 4),
                evidence_completeness=c_network,
                source="RiskNetwork_V2",
                explanation=network_context.explanation,
            ),
            RiskLayerContribution(
                layer_name="behavioral",
                score=behavioral_context.score,
                weight=w_beh,
                contribution=round(behavioral_context.score * w_beh, 4),
                evidence_completeness=c_behavior,
                source="VelocityEngine_V2",
                explanation=behavioral_context.explanation,
            ),
        ]

        # Unified signals
        all_signals = tx_signals + entity_signals + network_signals + behavior_signals

        # Natural multi-layer explanation
        composite_explanation = (
            f"Composite risk evaluated at {composite_score:.4f} ({composite_tier}) with evidence confidence {confidence_val:.2f}. "
            f"Contributions: ML Transaction={tx_context.score * w_tx:.4f} ({w_tx * 100:.0f}%), "
            f"Entity={entity_context.score * w_ent:.4f} ({w_ent * 100:.0f}%), "
            f"Network={network_context.score * w_net:.4f} ({w_net * 100:.0f}%), "
            f"Behavioral={behavioral_context.score * w_beh:.4f} ({w_beh * 100:.0f}%)."
        )

        # ----------------------------------------------------------------------
        # DETERMINISTIC POLICY GUIDANCE
        # ----------------------------------------------------------------------
        shared_dev_count = (
            self.entity_repo._get_cross_customer_sharing_count(
                session, "device", tx.device_id, as_of_time
            )
            if tx.device_id
            else 0
        )
        shared_crd_count = (
            self.entity_repo._get_cross_customer_sharing_count(
                session, "card", tx.card_id, as_of_time
            )
            if tx.card_id
            else 0
        )
        shared_ip_count = (
            self.entity_repo._get_cross_customer_sharing_count(session, "ip", tx.ip_id, as_of_time)
            if tx.ip_id
            else 0
        )

        policy_action, policy_reasons, _ = evaluate_policy_rules(
            risk_score=composite_score,
            is_suspicious_cluster=is_suspicious_net,
            cluster_risk_score=network_score,
            cluster_id=tx.network_id,
            shared_device_count=shared_dev_count,
            shared_card_count=shared_crd_count,
            shared_ip_count=shared_ip_count,
            investigation_status="completed" if not is_degraded else "degraded",
        )

        response = RiskIntelligenceResponse(
            transaction_id=transaction_id,
            composite_risk_score=composite_score,
            risk_tier=composite_tier,
            confidence=confidence_breakdown,
            transaction_risk=tx_context,
            entity_risk=entity_context,
            network_risk=network_context,
            behavioral_risk=behavioral_context,
            contribution_breakdown=contribution_breakdown,
            structured_signals=all_signals,
            explanation=composite_explanation,
            policy_recommendation=policy_action.value,
            orchestration_version="v2.0",
            as_of=as_of_time,
            degraded=is_degraded,
        )

        # Optional persistence
        if persist_assessment and tx_assessment:
            try:
                tx_assessment.composite_risk_score = composite_score
                tx_assessment.confidence_score = confidence_val
                tx_assessment.entity_risk_score = entity_score
                tx_assessment.network_risk_score = network_score
                tx_assessment.behavioral_risk_score = behavior_score
                tx_assessment.orchestration_version = "v2.0"
                tx_assessment.contribution_breakdown = [
                    c.model_dump() for c in contribution_breakdown
                ]
                tx_assessment.explanation_summary = composite_explanation
                session.flush()
            except Exception as e:
                logger.warning(f"Failed to persist composite assessment updates: {e}")

        return response


_risk_orchestrator_instance: RiskOrchestrator | None = None


def get_risk_orchestrator() -> RiskOrchestrator:
    """Dependency provider for RiskOrchestrator singleton."""
    global _risk_orchestrator_instance
    if _risk_orchestrator_instance is None:
        _risk_orchestrator_instance = RiskOrchestrator()
    return _risk_orchestrator_instance
