"""Tests for Application Initialization and Configuration."""

from app.core.config import settings
from app.main import app


def test_app_title_and_routes() -> None:
    """Test that the application initializes with proper configuration and routes."""
    assert app.title == settings.APP_NAME
    openapi_schema = app.openapi()
    assert f"{settings.API_V1_PREFIX}/health" in openapi_schema["paths"]
