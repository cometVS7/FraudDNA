"""FraudDNA FastAPI Application Entrypoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.logging import get_logger, setup_logging
from app.core.middleware import RequestCorrelationMiddleware
from app.graph.service import get_graph_service

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context for startup and shutdown events."""
    logger.info("Initializing FraudDNA application services...")
    # Warm up FraudDNA GraphService during startup so request paths never block
    service = get_graph_service()
    service.initialize()
    logger.info("FraudDNA application services initialized successfully.")
    yield
    # Shutdown cleanup logic
    logger.info("Shutting down FraudDNA application services...")


def create_app() -> FastAPI:
    """Initialize and configure the FastAPI application."""
    # 1. Initialize logging foundation
    setup_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)

    application = FastAPI(
        title=settings.APP_NAME,
        description="FraudDNA — AI-Powered Fraud Defense & Risk-Intelligence API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    )

    # 2. Register Request Correlation Middleware
    application.add_middleware(RequestCorrelationMiddleware)

    # 3. Configure CORS middleware
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
        expose_headers=[settings.REQUEST_ID_HEADER, settings.CORRELATION_ID_HEADER],
    )

    # 4. Register centralized domain error handlers
    register_error_handlers(application)

    # 5. Register API v1 routes
    application.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return application


app = create_app()
