"""FraudDNA Entity Intelligence Schemas.

Defines Pydantic models for persistent entity profiles (Customer, Account, Device, IP, Card, Merchant),
deterministic entity risk aggregation, behavioral velocity metrics, and relationship representations.
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EntityType(StrEnum):
    """Supported entity categories in FraudDNA."""

    CUSTOMER = "customer"
    ACCOUNT = "account"
    CARD = "card"
    DEVICE = "device"
    IP = "ip"
    MERCHANT = "merchant"
    NETWORK = "network"
    TRANSACTION = "transaction"


class RelationshipType(StrEnum):
    """Semantic relationship types connecting nodes in the FraudDNA graph."""

    OWNS = "OWNS"
    EXECUTED = "EXECUTED"
    ON_DEVICE = "ON_DEVICE"
    FROM_IP = "FROM_IP"
    USING_CARD = "USING_CARD"
    AT_MERCHANT = "AT_MERCHANT"
    DEBITS = "DEBITS"
    MEMBER_OF_NETWORK = "MEMBER_OF_NETWORK"
    SHARES_DEVICE = "SHARES_DEVICE"
    SHARES_IP = "SHARES_IP"
    SHARES_CARD = "SHARES_CARD"


class EntityRiskAggregation(BaseModel):
    """Deterministic, explainable entity risk aggregation breakdown."""

    risk_score: float = Field(..., ge=0.0, le=1.0, description="Aggregated entity risk score")
    risk_tier: str = Field(..., description="Risk tier: LOW, MEDIUM, HIGH, CRITICAL")
    max_tx_risk: float = Field(default=0.0, description="Maximum transaction risk score")
    avg_top3_tx_risk: float = Field(
        default=0.0, description="Average of top-3 transaction risk scores"
    )
    network_exposure: float = Field(
        default=0.0, description="Risk contribution from risk network membership"
    )
    sharing_anomaly: float = Field(
        default=0.0, description="Risk contribution from cross-customer shared infrastructure"
    )
    explanation: str = Field(
        ..., description="Human-readable deterministic explanation of risk calculation"
    )


class BehavioralMetrics(BaseModel):
    """Point-in-time behavioral velocity and sharing metrics."""

    as_of: datetime = Field(..., description="Reference point-in-time timestamp (UTC)")
    tx_count_5m: int = Field(default=0, description="Transaction count in last 5 minutes")
    tx_count_1h: int = Field(default=0, description="Transaction count in last 1 hour")
    tx_count_24h: int = Field(default=0, description="Transaction count in last 24 hours")
    amount_1h: float = Field(default=0.0, description="Total transaction amount in last 1 hour")
    amount_24h: float = Field(default=0.0, description="Total transaction amount in last 24 hours")
    unique_merchants_24h: int = Field(
        default=0, description="Distinct merchants transacted with in last 24 hours"
    )
    unique_devices_24h: int = Field(
        default=0, description="Distinct devices observed in last 24 hours"
    )
    unique_ips_24h: int = Field(
        default=0, description="Distinct IP addresses observed in last 24 hours"
    )
    cross_customer_sharing_count: int = Field(
        default=0, description="Number of other customer accounts sharing connected infrastructure"
    )


class AssociatedNetworkSummary(BaseModel):
    """Summary of a risk network associated with an entity."""

    network_id: str
    network_name: str | None = None
    is_suspicious: bool = False
    risk_score: float = 0.0
    transaction_count: int = 0


class EntityRelationshipItem(BaseModel):
    """Represents a direct typed semantic relationship from an entity to a connected node."""

    source_id: str = Field(..., description="Namespaced source identifier")
    target_id: str = Field(..., description="Namespaced target identifier")
    target_raw_id: str = Field(..., description="Raw target entity identifier")
    target_type: str = Field(..., description="Target entity category")
    relationship_type: str = Field(..., description="Semantic relationship code")
    target_label: str = Field(..., description="Display label for target entity")
    target_risk_score: float = Field(
        default=0.0, description="Target entity or transaction risk score"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Edge metadata")


class EntityRelationshipsResponse(BaseModel):
    """Response model for directly connected entity relationships."""

    entity_type: str
    entity_id: str
    total_relationships: int
    relationships: list[EntityRelationshipItem] = Field(default_factory=list)


class EntityTransactionsResponse(BaseModel):
    """Paginated list of transactions for an entity."""

    entity_type: str
    entity_id: str
    total_transactions: int
    limit: int
    offset: int
    transactions: list[dict[str, Any]] = Field(default_factory=list)


class CustomerProfileResponse(BaseModel):
    """Customer entity profile with behavioral metrics and risk aggregation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    account_age_days: int
    city: str | None = None
    status: str = "ACTIVE"
    risk_tier: str = "LOW"
    risk_score: float = 0.0
    total_transactions: int = 0
    total_amount: float = 0.0
    recent_transactions: list[dict[str, Any]] = Field(default_factory=list)
    risk_aggregation: EntityRiskAggregation | None = None
    behavioral_metrics: BehavioralMetrics | None = None
    associated_networks: list[AssociatedNetworkSummary] = Field(default_factory=list)
    connected_entities_summary: dict[str, int] = Field(default_factory=dict)


class AccountProfileResponse(BaseModel):
    """Account entity profile."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    account_type: str = "SAVINGS"
    status: str = "ACTIVE"
    risk_score: float = 0.0
    risk_tier: str = "LOW"
    created_at: datetime
    total_transactions: int = 0
    total_amount: float = 0.0
    recent_transactions: list[dict[str, Any]] = Field(default_factory=list)
    risk_aggregation: EntityRiskAggregation | None = None
    behavioral_metrics: BehavioralMetrics | None = None
    associated_networks: list[AssociatedNetworkSummary] = Field(default_factory=list)


class DeviceProfileResponse(BaseModel):
    """Device entity profile with fingerprint and risk signals."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    device_fingerprint: str | None = None
    status: str = "ACTIVE"
    risk_score: float = 0.0
    risk_tier: str = "LOW"
    first_seen: datetime
    last_seen: datetime
    associated_transactions_count: int = 0
    total_amount: float = 0.0
    recent_transactions: list[dict[str, Any]] = Field(default_factory=list)
    risk_aggregation: EntityRiskAggregation | None = None
    behavioral_metrics: BehavioralMetrics | None = None
    associated_networks: list[AssociatedNetworkSummary] = Field(default_factory=list)
    connected_customers_count: int = 0


class IPAddressProfileResponse(BaseModel):
    """IP Address profile with network risk indicators."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    ip_address: str
    status: str = "ACTIVE"
    risk_score: float = 0.0
    risk_tier: str = "LOW"
    first_seen: datetime
    last_seen: datetime
    associated_transactions_count: int = 0
    total_amount: float = 0.0
    recent_transactions: list[dict[str, Any]] = Field(default_factory=list)
    risk_aggregation: EntityRiskAggregation | None = None
    behavioral_metrics: BehavioralMetrics | None = None
    associated_networks: list[AssociatedNetworkSummary] = Field(default_factory=list)
    connected_customers_count: int = 0


class CardProfileResponse(BaseModel):
    """Card payment instrument profile."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    card_type: str = "CREDIT"
    status: str = "ACTIVE"
    risk_score: float = 0.0
    risk_tier: str = "LOW"
    first_seen: datetime
    last_seen: datetime
    associated_transactions_count: int = 0
    total_amount: float = 0.0
    recent_transactions: list[dict[str, Any]] = Field(default_factory=list)
    risk_aggregation: EntityRiskAggregation | None = None
    behavioral_metrics: BehavioralMetrics | None = None
    associated_networks: list[AssociatedNetworkSummary] = Field(default_factory=list)
    connected_customers_count: int = 0


class MerchantProfileResponse(BaseModel):
    """Merchant entity profile."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    merchant_category: str
    status: str = "ACTIVE"
    risk_score: float = 0.0
    risk_tier: str = "LOW"
    created_at: datetime
    associated_transactions_count: int = 0
    total_amount: float = 0.0
    recent_transactions: list[dict[str, Any]] = Field(default_factory=list)
    risk_aggregation: EntityRiskAggregation | None = None
    behavioral_metrics: BehavioralMetrics | None = None
    associated_networks: list[AssociatedNetworkSummary] = Field(default_factory=list)
