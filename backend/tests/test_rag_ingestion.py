from app.rag.retrieval import RAGService
from app.rag.vector_store import InMemoryVectorStore


def test_ingestion_of_knowledge_directory() -> None:
    store = InMemoryVectorStore()
    service = RAGService(vector_store=store)

    resp = service.ingest_knowledge_directory(knowledge_dir="knowledge")

    assert resp.status == "completed"
    assert resp.documents_ingested >= 8  # Our 8 synthetic policies, cases, and guidelines
    assert resp.chunks_created > 0
    assert store.count() > 0


def test_ingestion_idempotency_prevents_duplicates() -> None:
    store = InMemoryVectorStore()
    service = RAGService(vector_store=store)

    # First ingestion
    resp1 = service.ingest_knowledge_directory(knowledge_dir="knowledge")
    assert resp1.status == "completed"
    count1 = store.count()

    # Second ingestion without force reload
    resp2 = service.ingest_knowledge_directory(knowledge_dir="knowledge", force_reload=False)
    count2 = store.count()

    # Chunks count must not increase (no duplicate chunks)
    assert count1 == count2
    assert resp2.status == "completed"


def test_force_reload_clears_and_reindexes() -> None:
    store = InMemoryVectorStore()
    service = RAGService(vector_store=store)

    service.ingest_knowledge_directory(knowledge_dir="knowledge")
    initial_count = store.count()

    resp_reload = service.ingest_knowledge_directory(knowledge_dir="knowledge", force_reload=True)
    assert resp_reload.status == "completed"
    assert store.count() == initial_count


def test_ingestion_non_existent_dir() -> None:
    store = InMemoryVectorStore()
    service = RAGService(vector_store=store)

    resp = service.ingest_knowledge_directory(knowledge_dir="non_existent_folder_xyz")
    assert resp.status == "directory_not_found"
    assert resp.documents_ingested == 0
