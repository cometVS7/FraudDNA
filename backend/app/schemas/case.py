"""FraudDNA Case Management Schemas.

Defines Pydantic transfer models for case creation, status updates,
triage priorities, and analyst assignments.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class CaseStatus(StrEnum):
    """Authoritative case operational status states."""

    NEW = "NEW"
    IN_REVIEW = "IN_REVIEW"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class CasePriority(StrEnum):
    """Operational triage priority tier."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CaseCreateRequest(BaseModel):
    """Request payload for creating a new operational case."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=3, max_length=255, description="Summary title of the case.")
    priority: CasePriority = Field(
        default=CasePriority.MEDIUM, description="Triage priority level."
    )
    owner: str | None = Field(None, max_length=128, description="Assigned analyst or agent ID.")
    notes: str | None = Field(
        None, max_length=2048, description="Initial triage notes or hypothesis."
    )
    investigation_id: str | None = Field(
        None, max_length=64, description="Optional investigation ID to bind to this case."
    )


class CaseStatusUpdateRequest(BaseModel):
    """Request payload for updating case operational status."""

    model_config = ConfigDict(extra="forbid")

    status: CaseStatus = Field(..., description="New target status.")
    notes: str | None = Field(
        None, max_length=2048, description="Audit rationale for the transition."
    )
    owner: str | None = Field(None, max_length=128, description="Optional reassignment of owner.")


class CaseResponse(BaseModel):
    """Structured response representing a persisted case."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    status: str
    priority: str
    owner: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    investigation_ids: list[str] = Field(default_factory=list)


class CaseListResponse(BaseModel):
    """Paginated collection of cases."""

    items: list[CaseResponse]
    total_count: int
    limit: int
    offset: int
