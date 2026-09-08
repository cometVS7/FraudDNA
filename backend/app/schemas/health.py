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


class ReadinessResponse(BaseModel):
    """Structured response schema for service readiness probe."""

    status: str = Field(..., description="Overall readiness status ('ready' or 'unhealthy')")
    service: str = Field(default="FraudDNA Backend", description="Service identifier")
    version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(..., description="Active environment name")
    database_status: str = Field(..., description="PostgreSQL connectivity state")
    graph_status: str = Field(..., description="Graph service initialization state")
    persistent_storage_enabled: bool = Field(
        ..., description="Whether persistent database mode is active"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="UTC timestamp of the readiness check",
    )
