"""Tests for Health Check Endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint_returns_200() -> None:
    """Test that GET /api/v1/health returns 200 and structured health payload."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "FraudDNA"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data
    assert "environment" in data
