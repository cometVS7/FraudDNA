"""Unit tests for RAG semantic retrieval service."""

from app.rag.retrieval import RAGService
from app.rag.vector_store import InMemoryVectorStore


def test_retrieval_returns_relevant_policy_results() -> None:
    service = RAGService(vector_store=InMemoryVectorStore())
    service.ingest_knowledge_directory("knowledge")

    resp = service.search(query="escalation SLA for critical risk transactions", top_k=3)

    assert resp.store_status == "degraded"
    assert resp.total_results > 0
    assert len(resp.results) <= 3

    top_match = resp.results[0]
    assert top_match.source_type in {"policy", "guideline", "historical_case"}
    assert top_match.similarity > 0.0
    assert top_match.chunk_id.startswith("doc_")
    assert len(top_match.content) > 0


def test_retrieval_with_metadata_filter() -> None:
    service = RAGService(vector_store=InMemoryVectorStore())
    service.ingest_knowledge_directory("knowledge")

    # Filter strictly to policies
    resp = service.search(
        query="merchant fraud risk threshold",
        top_k=5,
        filters={"doc_type": "policy"},
    )

    assert resp.total_results > 0
    for r in resp.results:
        assert r.source_type == "policy"


def test_retrieval_minimum_similarity_threshold() -> None:
    service = RAGService(vector_store=InMemoryVectorStore())
    service.ingest_knowledge_directory("knowledge")

    resp_strict = service.search(
        query="emulator device farm collusion",
        top_k=10,
        min_similarity=0.999,  # Very strict
    )

    for r in resp_strict.results:
        assert r.similarity >= 0.999


def test_retrieval_empty_query() -> None:
    service = RAGService(vector_store=InMemoryVectorStore())
    service.ingest_knowledge_directory("knowledge")

    resp = service.search(query="")
    assert resp.total_results == 0
    assert resp.results == []


def test_retrieval_empty_knowledge_base() -> None:
    service = RAGService(vector_store=InMemoryVectorStore())
    # Do not ingest anything
    resp = service.search(query="device ring")
    assert resp.total_results == 0
    assert resp.results == []


def test_deterministic_tie_breaking() -> None:
    store = InMemoryVectorStore()
    service = RAGService(vector_store=store)
    service.ingest_knowledge_directory("knowledge")

    # Run query twice
    res1 = service.search("proxy farm subnet micro-transactions", top_k=5)
    res2 = service.search("proxy farm subnet micro-transactions", top_k=5)

    assert [r.chunk_id for r in res1.results] == [r.chunk_id for r in res2.results]
    assert [r.similarity for r in res1.results] == [r.similarity for r in res2.results]


def test_pgvector_store_semantics_and_degraded_fallback() -> None:
    from app.rag.vector_store import PgVectorVectorStore

    pg_store = PgVectorVectorStore()
    assert pg_store.store_name == "postgresql_pgvector"
    assert pg_store.is_degraded is False
    # When PostgreSQL container is offline, is_available returns False cleanly
    assert pg_store.is_available() is False

    mem_store = InMemoryVectorStore()
    assert mem_store.store_name == "in_memory_fallback"
    assert mem_store.is_degraded is True
    assert mem_store.is_available() is True


def test_no_silent_fallback_in_service_status() -> None:
    mem_store = InMemoryVectorStore()
    service = RAGService(vector_store=mem_store)
    service.ingest_knowledge_directory("knowledge")

    status = service.get_status()
    # It must NOT report healthy when running in in-memory fallback!
    assert status.status == "degraded"
    assert status.mode == "degraded"
    assert status.vector_store == "in_memory_fallback"
    assert status.message is not None
    assert "PostgreSQL persistent vector store is unavailable" in status.message
