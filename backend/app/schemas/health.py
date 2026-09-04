"""Health Check Schema."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Structured response schema for health check endpoint."""

    status: str = Field(default="healthy", description="Service health status")
    service: str = Field(default="FraudDNA Backend", description="Service identifier")
    version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(..., description="Active environment name")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of the health check",
    )
