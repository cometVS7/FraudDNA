"""Health check endpoint."""

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns current service health, version, environment, and server timestamp.",
)
async def get_health() -> HealthResponse:
    """Return structured health status."""
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version="0.1.0",
        environment=settings.APP_ENV,
    )
