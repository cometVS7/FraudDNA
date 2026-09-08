"""FraudDNA V2 Relational Domain Models.

Implements the persistent domain entities defined in V2_DOMAIN_MODEL.md:
1. CustomerModel
2. AccountModel
3. CardModel
4. DeviceModel
5. IPAddressModel
6. MerchantModel
7. RiskNetworkModel
8. TransactionModel
9. ModelRegistryModel
10. RiskAssessmentModel
11. RiskSignalModel
12. PolicyModel
13. DecisionModel
14. CaseModel
15. InvestigationModel
16. EvidenceModel
17. AIFindingModel
18. IntelligenceSourceModel
19. AuditEventModel
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# ==============================================================================
# 1. ENTITY INTELLIGENCE MODELS
# ==============================================================================


class CustomerModel(Base):
    """Represents a customer associated with financial activity."""

    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )
    account_age_days: Mapped[int] = mapped_column(Integer, default=0)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_tier: Mapped[str] = mapped_column(String(32), default="LOW")
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Relationships
    accounts: Mapped[list["AccountModel"]] = relationship(
        "AccountModel", back_populates="customer", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["TransactionModel"]] = relationship(
        "TransactionModel", back_populates="customer"
    )


class AccountModel(Base):
    """Represents a financial account owned by a customer."""

    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    account_type: Mapped[str] = mapped_column(String(32), default="SAVINGS")
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_tier: Mapped[str] = mapped_column(String(32), default="LOW")

    # Relationships
    customer: Mapped["CustomerModel"] = relationship("CustomerModel", back_populates="accounts")
    transactions: Mapped[list["TransactionModel"]] = relationship(
        "TransactionModel", back_populates="account"
    )


class CardModel(Base):
    """Represents a payment instrument (card)."""

    __tablename__ = "cards"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    card_type: Mapped[str] = mapped_column(String(32), default="CREDIT")
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_tier: Mapped[str] = mapped_column(String(32), default="LOW")

    # Relationships
    transactions: Mapped[list["TransactionModel"]] = relationship(
        "TransactionModel", back_populates="card"
    )


class DeviceModel(Base):
    """Represents a client hardware device fingerprint."""

    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    device_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_tier: Mapped[str] = mapped_column(String(32), default="LOW")

    # Relationships
    transactions: Mapped[list["TransactionModel"]] = relationship(
        "TransactionModel", back_populates="device"
    )


class IPAddressModel(Base):
    """Represents an originating network address."""

    __tablename__ = "ip_addresses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_tier: Mapped[str] = mapped_column(String(32), default="LOW")

    # Relationships
    transactions: Mapped[list["TransactionModel"]] = relationship(
        "TransactionModel", back_populates="ip"
    )


class MerchantModel(Base):
    """Represents a receiving commercial merchant."""

    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    merchant_category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_tier: Mapped[str] = mapped_column(String(32), default="LOW")

    # Relationships
    transactions: Mapped[list["TransactionModel"]] = relationship(
        "TransactionModel", back_populates="merchant"
    )


# ==============================================================================
# 2. NETWORK & GRAPH RISK MODELS
# ==============================================================================


class RiskNetworkModel(Base):
    """Represents a connected set of suspicious entities or coordinated fraud ring."""

    __tablename__ = "risk_networks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # cluster_id
    network_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    primary_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    transaction_count: Mapped[int] = mapped_column(Integer, default=0)
    customer_count: Mapped[int] = mapped_column(Integer, default=0)
    device_count: Mapped[int] = mapped_column(Integer, default=0)
    card_count: Mapped[int] = mapped_column(Integer, default=0)
    ip_count: Mapped[int] = mapped_column(Integer, default=0)
    merchant_count: Mapped[int] = mapped_column(Integer, default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"))
    first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    transactions: Mapped[list["TransactionModel"]] = relationship(
        "TransactionModel", back_populates="network"
    )
    investigations: Mapped[list["InvestigationModel"]] = relationship(
        "InvestigationModel", back_populates="network"
    )


# ==============================================================================
# 3. TRANSACTION DOMAIN MODEL
# ==============================================================================


class TransactionModel(Base):
    """Represents an authoritative financial transaction evaluated by FraudDNA."""

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    payment_method: Mapped[str] = mapped_column(String(32), nullable=False)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_fraud: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    fraud_scenario: Mapped[str] = mapped_column(String(64), default="legitimate")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    risk_tier: Mapped[str] = mapped_column(String(32), default="LOW", index=True)
    decision_action: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)

    # Foreign Keys
    customer_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("customers.id"), nullable=False, index=True
    )
    account_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("accounts.id"), nullable=True, index=True
    )
    card_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("cards.id"), nullable=True, index=True
    )
    device_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("devices.id"), nullable=True, index=True
    )
    ip_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("ip_addresses.id"), nullable=True, index=True
    )
    merchant_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("merchants.id"), nullable=False, index=True
    )
    network_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("risk_networks.id"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    customer: Mapped["CustomerModel"] = relationship("CustomerModel", back_populates="transactions")
    account: Mapped["AccountModel | None"] = relationship(
        "AccountModel", back_populates="transactions"
    )
    card: Mapped["CardModel | None"] = relationship("CardModel", back_populates="transactions")
    device: Mapped["DeviceModel | None"] = relationship(
        "DeviceModel", back_populates="transactions"
    )
    ip: Mapped["IPAddressModel | None"] = relationship(
        "IPAddressModel", back_populates="transactions"
    )
    merchant: Mapped["MerchantModel"] = relationship("MerchantModel", back_populates="transactions")
    network: Mapped["RiskNetworkModel | None"] = relationship(
        "RiskNetworkModel", back_populates="transactions"
    )
    risk_assessments: Mapped[list["RiskAssessmentModel"]] = relationship(
        "RiskAssessmentModel", back_populates="transaction"
    )
    investigations: Mapped[list["InvestigationModel"]] = relationship(
        "InvestigationModel", back_populates="primary_transaction"
    )
    decisions: Mapped[list["DecisionModel"]] = relationship(
        "DecisionModel", back_populates="transaction"
    )


# Compound indexes for fast multi-dimensional transaction lookups
Index(
    "ix_transactions_customer_timestamp", TransactionModel.customer_id, TransactionModel.timestamp
)
Index("ix_transactions_device_timestamp", TransactionModel.device_id, TransactionModel.timestamp)
Index("ix_transactions_card_timestamp", TransactionModel.card_id, TransactionModel.timestamp)
Index("ix_transactions_risk_timestamp", TransactionModel.risk_score, TransactionModel.timestamp)


# ==============================================================================
# 4. ML MODELS & RISK SIGNALS
# ==============================================================================


class ModelRegistryModel(Base):
    """Represents a trained and deployed ML fraud detection model."""

    __tablename__ = "models"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    model_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    operating_threshold: Mapped[float] = mapped_column(Float, default=0.37)
    feature_names: Mapped[list[str]] = mapped_column(JSON, default=list)
    feature_count: Mapped[int] = mapped_column(Integer, default=18)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    artifact_path: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RiskAssessmentModel(Base):
    """Represents an immutable point-in-time risk inference output."""

    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    transaction_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("transactions.id"), nullable=False, index=True
    )
    model_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("models.id"), nullable=True, index=True
    )
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    risk_tier: Mapped[str] = mapped_column(String(32), nullable=False)
    feature_version: Mapped[str] = mapped_column(String(32), default="v1.0")
    composite_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    entity_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    network_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    behavioral_risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    orchestration_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    contribution_breakdown: Mapped[list[dict[str, Any]] | dict[str, Any] | None] = mapped_column(
        JSON, nullable=True
    )
    explanation_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )

    # Relationships
    transaction: Mapped["TransactionModel"] = relationship(
        "TransactionModel", back_populates="risk_assessments"
    )
    risk_signals: Mapped[list["RiskSignalModel"]] = relationship(
        "RiskSignalModel", back_populates="assessment", cascade="all, delete-orphan"
    )

    @property
    def signals(self) -> list["RiskSignalModel"]:
        """Compatibility property for signals."""
        return self.risk_signals


class RiskSignalModel(Base):
    """Represents an individual XAI/Tree SHAP feature attribution contribution."""

    __tablename__ = "risk_signals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    assessment_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("risk_assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category: Mapped[str] = mapped_column(String(32), default="TRANSACTION_SIGNAL", index=True)
    feature_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    feature_value: Mapped[float] = mapped_column(Float, nullable=False)
    impact: Mapped[float] = mapped_column(Float, nullable=False)
    direction: Mapped[str] = mapped_column(String(32), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    assessment: Mapped["RiskAssessmentModel"] = relationship(
        "RiskAssessmentModel", back_populates="risk_signals"
    )


# ==============================================================================
# 5. DETERMINISTIC POLICY & DECISION MODELS
# ==============================================================================


class PolicyModel(Base):
    """Represents a deterministic financial decision policy matrix."""

    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    policy_name: Mapped[str] = mapped_column(String(128), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    rules_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    effective_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class DecisionModel(Base):
    """Represents an authoritative, immutable ALLOW / REVIEW / HOLD financial decision."""

    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # dec_<sha256>
    transaction_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("transactions.id"), nullable=False, index=True
    )
    policy_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("policies.id"), nullable=True, index=True
    )
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    reason_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    evidence_summary: Mapped[list[str]] = mapped_column(JSON, default=list)
    is_deterministic: Mapped[bool] = mapped_column(Boolean, default=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )

    # Relationships
    transaction: Mapped["TransactionModel"] = relationship(
        "TransactionModel", back_populates="decisions"
    )


# ==============================================================================
# 6. INVESTIGATION & CASE MANAGEMENT MODELS
# ==============================================================================


class CaseModel(Base):
    """Represents an operational case managing one or more investigations and entities."""

    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="NEW", index=True)
    priority: Mapped[str] = mapped_column(String(16), default="MEDIUM", index=True)
    owner: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    investigations: Mapped[list["InvestigationModel"]] = relationship(
        "InvestigationModel", back_populates="case"
    )
    evidence_items: Mapped[list["EvidenceModel"]] = relationship(
        "EvidenceModel", back_populates="case"
    )


class InvestigationModel(Base):
    """Represents an analytical risk investigation into suspicious activity."""

    __tablename__ = "investigations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # inv_<sha256>
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True)
    priority: Mapped[str] = mapped_column(String(16), default="MEDIUM", index=True)
    trigger_type: Mapped[str] = mapped_column(String(64), default="TRANSACTION_RISK")
    primary_transaction_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("transactions.id"), nullable=False, index=True
    )
    primary_network_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("risk_networks.id"), nullable=True, index=True
    )
    case_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("cases.id"), nullable=True, index=True
    )
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(32), default="LOW")
    assigned_to: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    primary_transaction: Mapped["TransactionModel"] = relationship(
        "TransactionModel", back_populates="investigations"
    )
    network: Mapped["RiskNetworkModel | None"] = relationship(
        "RiskNetworkModel", back_populates="investigations"
    )
    case: Mapped["CaseModel | None"] = relationship("CaseModel", back_populates="investigations")
    evidence_items: Mapped[list["EvidenceModel"]] = relationship(
        "EvidenceModel", back_populates="investigation", cascade="all, delete-orphan"
    )
    ai_findings: Mapped[list["AIFindingModel"]] = relationship(
        "AIFindingModel", back_populates="investigation", cascade="all, delete-orphan"
    )


class EvidenceModel(Base):
    """Represents verifiable, source-attributed evidence linked to an investigation or case."""

    __tablename__ = "evidence"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    investigation_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    case_id: Mapped[str | None] = mapped_column(
        String(64), ForeignKey("cases.id", ondelete="CASCADE"), nullable=True, index=True
    )
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), default="LOW")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    investigation: Mapped["InvestigationModel | None"] = relationship(
        "InvestigationModel", back_populates="evidence_items"
    )
    case: Mapped["CaseModel | None"] = relationship("CaseModel", back_populates="evidence_items")


class AIFindingModel(Base):
    """Represents a bounded, tool-grounded finding produced by the LangGraph agent."""

    __tablename__ = "ai_findings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    investigation_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    finding_type: Mapped[str] = mapped_column(String(64), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    agent_version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    tool_trace_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    limitations: Mapped[list[str]] = mapped_column(JSON, default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    investigation: Mapped["InvestigationModel"] = relationship(
        "InvestigationModel", back_populates="ai_findings"
    )


# ==============================================================================
# 7. INTELLIGENCE SOURCES & AUDIT EVENT MODELS
# ==============================================================================


class IntelligenceSourceModel(Base):
    """Represents external or reference intelligence sources (guidelines, policies, historical cases)."""

    __tablename__ = "intelligence_sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(32), default="1.0")
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source_path: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )


class AuditEventModel(Base):
    """Represents an immutable, tamper-evident record in the system audit trail."""

    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )
    actor: Mapped[str] = mapped_column(String(128), default="system")
    actor_type: Mapped[str] = mapped_column(String(32), default="SERVICE")
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    payload_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
