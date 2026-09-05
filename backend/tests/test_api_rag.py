"""Unit tests for /api/v1/rag endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.rag.retrieval import get_rag_service


@pytest.fixture(autouse=True)
def ensure_rag_initialized() -> None:
    service = get_rag_service()
    service.initialize("knowledge")


@pytest.mark.asyncio
async def test_api_rag_status() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/rag/status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["mode"] == "degraded"
    assert data["vector_store"] == "in_memory_fallback"
    assert "PostgreSQL persistent vector store is unavailable" in data["message"]
    assert data["documents_count"] >= 8
    assert data["chunks_count"] > 0
    assert data["embedding_provider"] == "deterministic_local_dev"


@pytest.mark.asyncio
async def test_api_rag_ingest() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/rag/ingest",
            json={"knowledge_dir": "knowledge", "force_reload": False},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["documents_ingested"] >= 8


@pytest.mark.asyncio
async def test_api_rag_search() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/rag/search",
            json={"query": "shared emulator hardware collusion", "top_k": 3},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["store_status"] == "degraded"
    assert "query" in data
    assert "total_results" in data
    assert "results" in data
    assert len(data["results"]) <= 3
    if data["results"]:
        first = data["results"][0]
        assert "source_type" in first
        assert "source_id" in first
        assert "document_title" in first
        assert "chunk_id" in first
        assert "similarity" in first
        assert "content" in first


@pytest.mark.asyncio
async def test_api_rag_documents_list() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/rag/documents")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_documents"] >= 8
    assert len(data["documents"]) >= 8
    first = data["documents"][0]
    assert "document_id" in first
    assert "title" in first
    assert "document_type" in first
    assert "chunk_count" in first


@pytest.mark.asyncio
async def test_api_rag_document_detail_success() -> None:
    service = get_rag_service()
    doc_ids = list(service._documents.keys())
    assert len(doc_ids) > 0
    sample_id = doc_ids[0]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(f"/api/v1/rag/documents/{sample_id}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["document_id"] == sample_id
    assert "title" in data
    assert "chunks" in data
    assert len(data["chunks"]) > 0


@pytest.mark.asyncio
async def test_api_rag_document_detail_not_found() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/rag/documents/doc_non_existent_99999")

    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
