"""FraudDNA FastAPI Application Entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.graph.service import get_graph_service


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context for startup and shutdown events."""
    # Warm up FraudDNA GraphService during startup so request paths never block
    service = get_graph_service()
    service.initialize()
    yield
    # Shutdown cleanup logic


def create_app() -> FastAPI:
    """Initialize and configure the FastAPI application."""
    application = FastAPI(
        title=settings.APP_NAME,
        description="FraudDNA — AI-Powered Fraud Defense & Risk-Intelligence API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    )

    # Configure CORS middleware
    cors_origins = (
        [settings.CORS_ORIGINS]
        if isinstance(settings.CORS_ORIGINS, str)
        else list(settings.CORS_ORIGINS)
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API v1 routes
    application.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return application


app = create_app()
