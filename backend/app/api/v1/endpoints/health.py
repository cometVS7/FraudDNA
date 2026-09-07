"""Health and readiness check endpoints."""

from fastapi import APIRouter

from app.core.config import settings
from app.core.database import check_database_health
from app.graph.service import get_graph_service
from app.schemas.health import HealthResponse, ReadinessResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health (Liveness)",
    description="Returns current service health, version, environment, and server timestamp.",
)
async def get_health() -> HealthResponse:
    """Return structured liveness health status."""
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version="0.1.0",
        environment=settings.APP_ENV,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Service Readiness Probe",
    description="Checks connectivity to PostgreSQL and status of Graph/ML services.",
)
async def get_readiness() -> ReadinessResponse:
    """Return structured readiness check across critical dependencies."""
    db_health = await check_database_health()
    db_status = db_health.get("status", "unknown")

    gs = get_graph_service()
    graph_status = "ready" if gs.is_initialized else "initializing"

    overall = "ready"
    if settings.is_production and db_status != "connected":
        overall = "unhealthy"

    return ReadinessResponse(
        status=overall,
        service=settings.APP_NAME,
        version="0.1.0",
        environment=settings.APP_ENV,
        database_status=db_status,
        graph_status=graph_status,
        persistent_storage_enabled=settings.is_persistent_mode,
    )
