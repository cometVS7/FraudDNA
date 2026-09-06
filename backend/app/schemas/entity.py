"""FraudDNA Entity Intelligence Schemas.

Defines Pydantic models for persistent entity profiles (Customer, Device, IP, Card, Merchant).
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


class CustomerProfileResponse(BaseModel):
    """Customer entity profile with behavioral metrics."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    account_age_days: int
    city: str | None = None
    status: str = "ACTIVE"
    risk_tier: str = "LOW"
    risk_score: float = 0.0
    total_transactions: int = 0
    recent_transactions: list[dict[str, Any]] = Field(default_factory=list)


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
