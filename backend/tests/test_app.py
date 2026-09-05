"""Tests for Application Initialization, Configuration, and CORS."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings, settings
from app.main import app


def test_app_title_and_routes() -> None:
    """Test that the application initializes with proper configuration and routes."""
    assert app.title == settings.APP_NAME
    openapi_schema = app.openapi()
    assert f"{settings.API_V1_PREFIX}/health" in openapi_schema["paths"]


@pytest.mark.asyncio
async def test_cors_preflight_production_vercel_origin() -> None:
    """Verify that OPTIONS preflight request from production Vercel frontend succeeds."""
    origin = "https://fraud-dna.vercel.app"
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Content-Type, Authorization",
    }
    endpoints = ["/api/v1/health", "/api/v1/overview", "/api/v1/clusters"]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for endpoint in endpoints:
            response = await client.options(endpoint, headers=headers)
            assert response.status_code == 200, (
                f"OPTIONS {endpoint} failed with status {response.status_code}"
            )
            assert response.headers.get("access-control-allow-origin") == origin
            assert response.headers.get("access-control-allow-credentials") == "true"
            assert "GET" in response.headers.get("access-control-allow-methods", "")


@pytest.mark.asyncio
async def test_cors_preflight_localhost_origin() -> None:
    """Verify that OPTIONS preflight request from local frontend succeeds."""
    origin = "http://localhost:3000"
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.options("/api/v1/health", headers=headers)

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.asyncio
async def test_cors_preflight_disallowed_origin_rejected() -> None:
    """Verify that OPTIONS preflight request from untrusted origin is rejected."""
    headers = {
        "Origin": "https://untrusted-attacker-domain.com",
        "Access-Control-Request-Method": "GET",
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.options("/api/v1/health", headers=headers)

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_cors_settings_parsing_formats() -> None:
    """Verify that Settings parses various CORS_ORIGINS environment variable formats correctly."""
    # 1. Single string
    s1 = Settings(CORS_ORIGINS="https://fraud-dna.vercel.app")
    assert "https://fraud-dna.vercel.app" in s1.CORS_ORIGINS
    assert "http://localhost:3000" in s1.CORS_ORIGINS

    # 2. Comma-separated string with trailing slashes
    s2 = Settings(CORS_ORIGINS="https://custom.domain.com/, https://fraud-dna.vercel.app/")
    assert "https://custom.domain.com" in s2.CORS_ORIGINS
    assert "https://fraud-dna.vercel.app" in s2.CORS_ORIGINS
    assert "http://localhost:3000" in s2.CORS_ORIGINS

    # 3. JSON array string
    s3 = Settings(CORS_ORIGINS='["http://localhost:3000", "https://fraud-dna.vercel.app"]')
    assert "https://fraud-dna.vercel.app" in s3.CORS_ORIGINS
    assert "http://localhost:3000" in s3.CORS_ORIGINS

    # 4. Default origins contain production Vercel app
    s_default = Settings()
    assert "https://fraud-dna.vercel.app" in s_default.CORS_ORIGINS
    assert "http://localhost:3000" in s_default.CORS_ORIGINS
    assert "http://127.0.0.1:3000" in s_default.CORS_ORIGINS
