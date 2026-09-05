"""Unit tests for /api/v1/investigations endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.graph.service import get_graph_service
from app.main import app


@pytest.mark.asyncio
async def test_post_investigation_success() -> None:
    """Verify POST /api/v1/investigations returns 200 with complete investigation payload."""
    graph_service = get_graph_service()
    assert len(graph_service.transactions_by_id) > 0
    sample_tx_id = next(iter(graph_service.transactions_by_id.keys()))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/investigations",
            json={"transaction_id": sample_tx_id},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["transaction_id"] == sample_tx_id
    assert "investigation_id" in data
    assert "risk_score" in data
    assert "risk_level" in data
    assert "risk_factors" in data
    assert "related_entities" in data
    assert "related_transactions" in data
    assert "evidence" in data
    assert "status" in data
    assert "generated_at" in data


@pytest.mark.asyncio
async def test_post_investigation_not_found() -> None:
    """Verify POST /api/v1/investigations returns 404 for an unknown transaction ID."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/investigations",
            json={"transaction_id": "non_existent_tx_9999999"},
        )

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "non_existent_tx_9999999" in data["detail"]


@pytest.mark.asyncio
async def test_post_investigation_invalid_payload() -> None:
    """Verify POST /api/v1/investigations returns 422 for malformed request body."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/investigations",
            json={"invalid_field": "123"},
        )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_investigation_by_id_endpoint() -> None:
    """Verify GET /api/v1/investigations/{investigation_id} retrieves a created investigation."""
    graph_service = get_graph_service()
    sample_tx_id = next(iter(graph_service.transactions_by_id.keys()))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create investigation
        post_resp = await client.post(
            "/api/v1/investigations",
            json={"transaction_id": sample_tx_id},
        )
        assert post_resp.status_code == 200
        inv_id = post_resp.json()["investigation_id"]

        # Retrieve investigation
        get_resp = await client.get(f"/api/v1/investigations/{inv_id}")

    assert get_resp.status_code == 200
    retrieved_data = get_resp.json()
    assert retrieved_data["investigation_id"] == inv_id
    assert retrieved_data["transaction_id"] == sample_tx_id


@pytest.mark.asyncio
async def test_get_investigation_by_id_not_found() -> None:
    """Verify GET /api/v1/investigations/{investigation_id} returns 404 for unknown ID."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/investigations/inv_non_existent_999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
