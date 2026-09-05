"""FraudDNA RAG Retrieval and Service Orchestration Module.

Orchestrates document parsing, embedding generation, vector indexing, and grounded
semantic similarity retrieval with strict source attribution and deterministic tie-breaking.
"""

from pathlib import Path
from typing import Any

from app.rag.embeddings import (
    BaseEmbeddingProvider,
    DeterministicLocalEmbeddingProvider,
    get_embedding_provider,
)
from app.rag.ingestion import IngestionPipeline, ParsedDocument
from app.rag.vector_store import (
    BaseVectorStore,
    InMemoryVectorStore,
    VectorRecord,
    get_vector_store,
)
from app.schemas.rag import (
    DocumentDetailResponse,
    DocumentListResponse,
    DocumentSummary,
    IngestResponse,
    RAGStatusResponse,
    SearchResponse,
    SearchResult,
)


class RAGService:
    """Manages knowledge base ingestion, vector storage, and semantic retrieval."""

    def __init__(
        self,
        vector_store: BaseVectorStore | None = None,
        embedding_provider: BaseEmbeddingProvider | None = None,
        pipeline: IngestionPipeline | None = None,
        auto_initialize: bool = False,
    ) -> None:
        self.vector_store = vector_store or get_vector_store()
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.pipeline = pipeline or IngestionPipeline()
        self.auto_initialize = auto_initialize

        # In-memory document registry for fast metadata queries
        self._documents: dict[str, ParsedDocument] = {}
        self._is_initialized: bool = False

    def initialize(self, knowledge_dir: str | Path = "knowledge") -> None:
        """Autoload knowledge base if not already initialized."""
        if not self._is_initialized:
            self.ingest_knowledge_directory(knowledge_dir=knowledge_dir)
            self._is_initialized = True

    def ingest_knowledge_directory(
        self,
        knowledge_dir: str | Path = "knowledge",
        force_reload: bool = False,
    ) -> IngestResponse:
        """Ingest all knowledge documents from directory into vector store."""
        path = Path(knowledge_dir)
        if not path.exists():
            alt_path = Path("..") / path
            if alt_path.exists():
                path = alt_path

        if not path.exists():
            return IngestResponse(
                documents_ingested=0,
                chunks_created=0,
                status="directory_not_found",
                source_directory=str(knowledge_dir),
            )

        if force_reload:
            self.vector_store.clear()
            self._documents.clear()

        parsed_docs = self.pipeline.process_directory(path)
        total_chunks = 0
        ingested_doc_count = 0

        for doc in parsed_docs:
            existing = self._documents.get(doc.document_id)
            # Idempotency check: if document already exists with identical content_hash, skip re-embedding
            if existing and existing.content_hash == doc.content_hash and not force_reload:
                continue

            # Generate embeddings for all chunks in batch
            chunk_texts = [c.content for c in doc.chunks]
            embeddings = self.embedding_provider.embed_batch(chunk_texts)

            records: list[VectorRecord] = []
            for chunk, emb in zip(doc.chunks, embeddings, strict=False):
                records.append(
                    VectorRecord(
                        chunk_id=chunk.chunk_id,
                        document_id=doc.document_id,
                        content=chunk.content,
                        embedding=emb,
                        metadata=chunk.metadata,
                    )
                )

            # If document was previously ingested with different content, clear old chunks
            if isinstance(self.vector_store, InMemoryVectorStore):
                self.vector_store.delete_by_document_id(doc.document_id)

            self.vector_store.upsert(records)
            self._documents[doc.document_id] = doc
            total_chunks += len(records)
            ingested_doc_count += 1

        self._is_initialized = True

        return IngestResponse(
            documents_ingested=ingested_doc_count or len(self._documents),
            chunks_created=total_chunks or self.vector_store.count(),
            status="completed",
            source_directory=str(knowledge_dir),
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.0,
        filters: dict[str, Any] | None = None,
    ) -> SearchResponse:
        """Execute grounded semantic search against vector store with source attribution."""
        self._ensure_initialized()

        if not self.vector_store.is_available():
            return SearchResponse(
                query=query,
                total_results=0,
                results=[],
                store_status="unavailable",
            )

        if not query or not query.strip():
            return SearchResponse(
                query=query,
                total_results=0,
                results=[],
                store_status="active",
            )

        # Generate query vector
        query_embedding = self.embedding_provider.embed_text(query)

        # Search vector store
        matches = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            min_similarity=min_similarity,
            filters=filters,
        )

        results: list[SearchResult] = []
        for record, similarity in matches:
            meta = record.metadata
            source_type = meta.get("doc_type", "general")
            source_id = meta.get("reference_id") or record.document_id
            doc_title = meta.get("title", "Document")

            results.append(
                SearchResult(
                    source_type=source_type,
                    source_id=source_id,
                    document_title=doc_title,
                    chunk_id=record.chunk_id,
                    content=record.content,
                    similarity=similarity,
                    metadata=meta,
                )
            )

        active_status = "degraded" if self.vector_store.is_degraded else "active"

        return SearchResponse(
            query=query,
            total_results=len(results),
            results=results,
            store_status=active_status,
        )

    def list_documents(self) -> DocumentListResponse:
        """List all ingested documents with summary statistics."""
        self._ensure_initialized()
        summaries: list[DocumentSummary] = []

        # Sort deterministically by document_id
        for doc_id in sorted(self._documents.keys()):
            doc = self._documents[doc_id]
            summaries.append(
                DocumentSummary(
                    document_id=doc.document_id,
                    title=doc.title,
                    document_type=doc.document_type,
                    category=doc.category,
                    source_path=doc.source_path,
                    chunk_count=len(doc.chunks),
                )
            )

        return DocumentListResponse(
            total_documents=len(summaries),
            documents=summaries,
        )

    def get_document_by_id(self, document_id: str) -> DocumentDetailResponse | None:
        """Retrieve full document detail including its chunk breakdown."""
        self._ensure_initialized()
        doc = self._documents.get(document_id)
        if not doc:
            return None

        chunks_data = [
            {
                "chunk_id": c.chunk_id,
                "chunk_index": c.chunk_index,
                "content": c.content,
                "metadata": c.metadata,
            }
            for c in doc.chunks
        ]

        return DocumentDetailResponse(
            document_id=doc.document_id,
            title=doc.title,
            document_type=doc.document_type,
            category=doc.category,
            source_path=doc.source_path,
            content_hash=doc.content_hash,
            chunk_count=len(doc.chunks),
            chunks=chunks_data,
        )

    def get_status(self) -> RAGStatusResponse:
        """Return operational health status of RAG subsystem."""
        provider_name = (
            "deterministic_local_dev"
            if isinstance(self.embedding_provider, DeterministicLocalEmbeddingProvider)
            else "external_api"
        )

        is_avail = self.vector_store.is_available()
        is_degraded = self.vector_store.is_degraded

        if not is_avail:
            status_val = "unavailable"
            mode_val = "degraded"
            msg = "Vector store is unreachable and offline."
        elif is_degraded:
            status_val = "degraded"
            mode_val = "degraded"
            msg = (
                "PostgreSQL persistent vector store is unavailable; "
                "operating in degraded in-memory mode."
            )
        else:
            status_val = "healthy"
            mode_val = "normal"
            msg = "PostgreSQL + pgvector persistent vector store is active."

        return RAGStatusResponse(
            status=status_val,
            mode=mode_val,
            documents_count=len(self._documents),
            chunks_count=self.vector_store.count(),
            embedding_provider=provider_name,
            vector_store=self.vector_store.store_name,
            message=msg,
        )

    def _ensure_initialized(self) -> None:
        if self.auto_initialize and not self._is_initialized and not self._documents:
            self.initialize()


# Global Singleton
_rag_service_instance: RAGService | None = None


def get_rag_service() -> RAGService:
    """Dependency provider for RAGService singleton."""
    global _rag_service_instance
    if _rag_service_instance is None:
        _rag_service_instance = RAGService(auto_initialize=True)
        _rag_service_instance.initialize()
    return _rag_service_instance
