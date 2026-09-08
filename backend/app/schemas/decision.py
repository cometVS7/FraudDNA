"""FraudDNA Decision Schemas.

Defines Pydantic models for persistent decision records and pagination.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DecisionRecordResponse(BaseModel):
    """Structured representation of a persisted financial decision."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    transaction_id: str
    policy_id: str | None
    policy_version: str
    action: str
    reason_codes: list[str] = Field(default_factory=list)
    evidence_summary: list[str] = Field(default_factory=list)
    is_deterministic: bool = True
    generated_at: datetime


class DecisionListResponse(BaseModel):
    """Paginated collection of decisions."""

    items: list[DecisionRecordResponse]
    total_count: int
    limit: int
    offset: int
