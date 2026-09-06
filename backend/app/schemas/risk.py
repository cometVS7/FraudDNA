"""FraudDNA Advanced Multi-Layer Risk Intelligence Schemas.

Defines schemas for the four-layer risk model:
Transaction Risk, Entity Risk, Network Risk, and Behavioral Risk,
along with composite score orchestration, confidence/evidence completeness,
structured signal taxonomy, and explainability breakdowns.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SignalCategory(StrEnum):
    """Authoritative taxonomy categories for risk signals."""

    TRANSACTION_SIGNAL = "TRANSACTION_SIGNAL"
    ENTITY_SIGNAL = "ENTITY_SIGNAL"
    NETWORK_SIGNAL = "NETWORK_SIGNAL"
    BEHAVIOR_SIGNAL = "BEHAVIOR_SIGNAL"


class SignalDirection(StrEnum):
    """Direction of influence on composite risk."""

    INCREASES_RISK = "INCREASES_RISK"
    DECREASES_RISK = "DECREASES_RISK"
    NEUTRAL = "NEUTRAL"


class StructuredRiskSignal(BaseModel):
    """Represents a discrete, evidence-backed risk signal across any risk layer."""

    category: SignalCategory = Field(..., description="Signal domain taxonomy category")
    name: str = Field(..., description="Machine-readable signal code")
    value: float = Field(..., description="Observed feature or metric value")
    impact: float = Field(..., description="Contribution weight/magnitude to risk score")
    direction: SignalDirection = Field(
        default=SignalDirection.INCREASES_RISK,
        description="Whether this signal elevates or mitigates risk",
    )
    source: str = Field(..., description="Originating engine (ML_SHAP, ENTITY, NETWORK, VELOCITY)")
    evidence_reference: str | None = Field(
        default=None, description="Identifier of source entity, network, or transaction"
    )
    description: str = Field(..., description="Human-readable explanation of the signal")


class RiskLayerContribution(BaseModel):
    """Decomposition of a single risk layer's contribution to composite risk."""

    layer_name: str = Field(
        ..., description="Layer name: 'transaction', 'entity', 'network', or 'behavioral'"
    )
    score: float = Field(..., ge=0.0, le=1.0, description="Layer-specific risk score [0.0 - 1.0]")
    weight: float = Field(
        ..., ge=0.0, le=1.0, description="Server-controlled weighting coefficient"
    )
    contribution: float = Field(..., description="Weighted contribution to composite risk score")
    evidence_completeness: float = Field(
        ..., ge=0.0, le=1.0, description="Completeness of input evidence for this layer"
    )
    source: str = Field(..., description="Underlying intelligence engine or model")
    explanation: str = Field(..., description="Summary explanation of layer's risk evaluation")


class TransactionRiskContext(BaseModel):
    """Risk layer 1: Core predictive ML score and feature attributions."""

    score: float = Field(..., ge=0.0, le=1.0, description="LightGBM model fraud probability")
    risk_tier: str = Field(..., description="LOW, MEDIUM, HIGH, or CRITICAL")
    model_version: str = Field(..., description="Deployed model identifier")
    operating_threshold: float = Field(..., description="Classification decision threshold")
    signals: list[StructuredRiskSignal] = Field(
        default_factory=list, description="Top Tree SHAP feature attributions"
    )
    explanation: str = Field(..., description="Transaction ML risk explanation")

    @property
    def model_threshold(self) -> float:
        return self.operating_threshold

    @property
    def threshold(self) -> float:
        return self.operating_threshold

    @property
    def confidence(self) -> float:
        return 1.0

    @property
    def contributing_signals(self) -> list[StructuredRiskSignal]:
        return self.signals


class EntityRiskContext(BaseModel):
    """Risk layer 2: Persistent entity profile risk posture and cross-account sharing."""

    score: float = Field(..., ge=0.0, le=1.0, description="Deterministic entity risk score")
    risk_tier: str = Field(..., description="Entity risk tier")
    primary_customer_id: str | None = Field(default=None, description="Primary customer ID")
    associated_device_id: str | None = Field(default=None, description="Associated device ID")
    associated_card_id: str | None = Field(default=None, description="Associated card ID")
    associated_ip_id: str | None = Field(default=None, description="Associated IP address")
    signals: list[StructuredRiskSignal] = Field(
        default_factory=list, description="Entity sharing and historical risk signals"
    )
    risk_components: dict[str, float] = Field(
        default_factory=dict, description="Component contributions (R_max, R_avg3, sharing)"
    )
    explanation: str = Field(..., description="Entity risk explanation")

    @property
    def confidence(self) -> float:
        return 1.0

    @property
    def primary_entity_type(self) -> str:
        return "customer"

    @property
    def primary_entity_id(self) -> str | None:
        return self.primary_customer_id

    @property
    def contributing_signals(self) -> list[StructuredRiskSignal]:
        return self.signals

    @property
    def contextual_entities(self) -> dict[str, str | None]:
        return {
            "customer": self.primary_customer_id,
            "device": self.associated_device_id,
            "card": self.associated_card_id,
            "ip": self.associated_ip_id,
        }


class NetworkRiskContext(BaseModel):
    """Risk layer 3: Fraud syndicate cluster and coordinated abuse intelligence."""

    score: float = Field(..., ge=0.0, le=1.0, description="Syndicate cluster risk score")
    network_id: str | None = Field(
        default=None, description="Cluster identifier if transaction is in a network"
    )
    is_suspicious: bool = Field(default=False, description="Whether network exceeds risk threshold")
    exposure_amount: float = Field(
        default=0.0, description="Total financial exposure across network (INR)"
    )
    member_counts: dict[str, int] = Field(
        default_factory=dict, description="Entity counts by type (customers, devices, etc.)"
    )
    signals: list[StructuredRiskSignal] = Field(
        default_factory=list, description="Network collusion signals"
    )
    primary_reason: str | None = Field(
        default=None, description="Primary detected syndicate pattern"
    )
    explanation: str = Field(..., description="Network risk explanation")

    @property
    def is_member(self) -> bool:
        return self.network_id is not None

    @property
    def exposure(self) -> float:
        return self.exposure_amount

    @property
    def member_count(self) -> int:
        return sum(self.member_counts.values()) if self.member_counts else 0

    @property
    def confidence(self) -> float:
        return 1.0 if self.network_id is not None else 0.5

    @property
    def contributing_signals(self) -> list[StructuredRiskSignal]:
        return self.signals


class BehavioralRiskContext(BaseModel):
    """Risk layer 4: Point-in-time velocity acceleration and anomaly metrics."""

    score: float = Field(..., ge=0.0, le=1.0, description="Normalized behavioral risk score")
    as_of: datetime = Field(..., description="Point-in-time evaluation timestamp")
    tx_count_5m: int = Field(default=0, description="Transactions in last 5 minutes")
    tx_count_1h: int = Field(default=0, description="Transactions in last 1 hour")
    tx_count_24h: int = Field(default=0, description="Transactions in last 24 hours")
    amount_1h: float = Field(default=0.0, description="Amount transacted in last 1 hour")
    amount_24h: float = Field(default=0.0, description="Amount transacted in last 24 hours")
    cross_customer_sharing_count: int = Field(
        default=0, description="Other customer accounts sharing connected infrastructure"
    )
    signals: list[StructuredRiskSignal] = Field(
        default_factory=list, description="Behavioral anomaly signals"
    )
    explanation: str = Field(..., description="Behavioral risk explanation")

    @property
    def velocity_5m(self) -> int:
        return self.tx_count_5m

    @property
    def velocity_1h(self) -> int:
        return self.tx_count_1h

    @property
    def velocity_24h(self) -> int:
        return self.tx_count_24h

    @property
    def amount_velocity_24h(self) -> float:
        return self.amount_24h

    @property
    def contributing_signals(self) -> list[StructuredRiskSignal]:
        return self.signals


class ConfidenceBreakdown(BaseModel):
    """Evaluation of evidence completeness and intelligence reliability."""

    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Overall evidence completeness score [0.0 - 1.0]"
    )
    evidence_completeness: float = Field(
        ..., ge=0.0, le=1.0, description="Ratio of available vs optimal evidence dimensions"
    )
    model_available: bool = Field(default=True, description="Whether predictive ML model executed")
    entity_context_verified: bool = Field(
        default=True, description="Whether entity profile history was verified"
    )
    network_context_verified: bool = Field(
        default=True, description="Whether network topology was determined"
    )
    behavioral_history_sufficient: bool = Field(
        default=True, description="Whether historical velocity window had sufficient depth"
    )
    is_degraded: bool = Field(
        default=False, description="Whether any dependency fell back to degraded state"
    )
    degradation_reasons: list[str] = Field(
        default_factory=list, description="Explanations if any dependency is degraded"
    )

    @property
    def overall_confidence(self) -> float:
        return self.confidence_score

    @property
    def transaction_model_completeness(self) -> float:
        return 1.0 if self.model_available else 0.0

    @property
    def entity_context_completeness(self) -> float:
        return 1.0 if self.entity_context_verified else 0.0

    @property
    def network_context_completeness(self) -> float:
        return 1.0 if self.network_context_verified else 0.0

    @property
    def behavioral_history_completeness(self) -> float:
        return 1.0 if self.behavioral_history_sufficient else 0.0


class RiskIntelligenceResponse(BaseModel):
    """Authoritative composite risk intelligence response contract."""

    transaction_id: str = Field(..., description="Unique transaction identifier")
    composite_risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Deterministic composite multi-layer risk score"
    )
    risk_tier: str = Field(..., description="Calibrated risk tier: LOW, MEDIUM, HIGH, CRITICAL")
    confidence: ConfidenceBreakdown = Field(..., description="Evidence completeness evaluation")
    transaction_risk: TransactionRiskContext = Field(
        ..., description="Layer 1: Core ML transaction risk"
    )
    entity_risk: EntityRiskContext = Field(..., description="Layer 2: Persistent entity risk")
    network_risk: NetworkRiskContext = Field(..., description="Layer 3: Syndicate network risk")
    behavioral_risk: BehavioralRiskContext = Field(
        ..., description="Layer 4: Behavioral velocity risk"
    )
    contribution_breakdown: list[RiskLayerContribution] = Field(
        default_factory=list, description="Decomposed layer contributions to composite score"
    )
    structured_signals: list[StructuredRiskSignal] = Field(
        default_factory=list, description="Unified list of evidence-backed signals"
    )
    explanation: str = Field(
        ..., description="Multi-layer natural language synthesis of risk determination"
    )
    policy_recommendation: str = Field(
        ..., description="Deterministic policy engine action: ALLOW, REVIEW, or HOLD"
    )
    orchestration_version: str = Field(
        default="v2.0", description="Risk orchestrator logic version"
    )
    as_of: datetime = Field(..., description="Point-in-time timestamp (UTC)")
    degraded: bool = Field(
        default=False, description="Whether execution operated with degraded evidence"
    )

    @property
    def composite_risk_tier(self) -> str:
        return self.risk_tier

    @property
    def is_degraded(self) -> bool:
        return self.degraded

    @property
    def layer_contributions(self) -> list[RiskLayerContribution]:
        return self.contribution_breakdown

    @property
    def explanation_summary(self) -> str:
        return self.explanation

    @property
    def layer_explanations(self) -> dict[str, str]:
        return {
            "transaction": self.transaction_risk.explanation,
            "entity": self.entity_risk.explanation,
            "network": self.network_risk.explanation,
            "behavioral": self.behavioral_risk.explanation,
        }
