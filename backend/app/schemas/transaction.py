"""FraudDNA Transaction Schemas.

Defines Pydantic models for persistent transaction retrieval,
filtering, and bounded pagination.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TransactionSummary(BaseModel):
    """Summary of a financial transaction."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    timestamp: datetime
    amount: Decimal
    currency: str = "INR"
    payment_method: str
    city: str | None = None
    customer_id: str
    merchant_id: str
    card_id: str | None = None
    device_id: str | None = None
    ip_id: str | None = None
    network_id: str | None = None
    risk_score: float = 0.0
    risk_tier: str = "LOW"
    decision_action: str | None = None
    is_fraud: bool = False
    fraud_scenario: str = "legitimate"


class TransactionDetail(TransactionSummary):
    """Detailed transaction response including assessment signals and linked entities."""

    risk_signals: list[dict[str, Any]] = Field(default_factory=list)
    customer_city: str | None = None
    merchant_category: str | None = None


class TransactionListResponse(BaseModel):
    """Paginated collection of transactions."""

    items: list[TransactionSummary]
    total_count: int
    limit: int
    offset: int
