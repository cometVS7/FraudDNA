"""FraudDNA Audit Trail Schemas.

Defines Pydantic models for tamper-evident audit events and cryptographic chain verification.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditEventResponse(BaseModel):
    """Structured response for an immutable audit event."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    timestamp: datetime
    actor: str
    actor_type: str
    event_type: str
    entity_type: str
    entity_id: str
    payload_hash: str
    previous_hash: str | None
    event_hash: str
    payload: dict[str, Any] = Field(default_factory=dict)


class AuditEventListResponse(BaseModel):
    """Paginated collection of audit events."""

    items: list[AuditEventResponse]
    total_count: int
    limit: int
    offset: int


class AuditChainVerifyResponse(BaseModel):
    """Cryptographic verification result of the audit hash chain."""

    is_valid: bool
    total_events: int
    verified_events: int
    tampered_at_id: str | None = None
    verification_message: str
