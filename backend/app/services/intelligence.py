"""FraudDNA Intelligence Application Service.

Coordinates external regulatory policies, fraud guidelines, and RAG knowledge retrieval.
"""

import logging
from typing import Any

from app.rag.retrieval import RAGService, get_rag_service

logger = logging.getLogger(__name__)


class IntelligenceService:
    """Provides unified access to RAG knowledge, fraud typologies, and regulatory policies."""

    def __init__(self, rag_service: RAGService | None = None) -> None:
        self.rag = rag_service or get_rag_service()

    def query_intelligence(
        self,
        query: str,
        top_k: int = 5,
        min_similarity: float = 0.0,
        doc_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query knowledge corpus via semantic vector similarity."""
        filters = {"doc_type": doc_type} if doc_type else None
        search_res = self.rag.search(
            query=query,
            top_k=top_k,
            min_similarity=min_similarity,
            filters=filters,
        )
        return [
            {
                "chunk_id": r.chunk_id,
                "source_id": r.source_id,
                "source_title": r.document_title,
                "source_type": r.source_type,
                "content": r.content,
                "score": r.similarity,
                "metadata": r.metadata,
            }
            for r in search_res.results
        ]


_intelligence_service_instance: IntelligenceService | None = None


def get_intelligence_service() -> IntelligenceService:
    """Dependency provider for IntelligenceService."""
    global _intelligence_service_instance
    if _intelligence_service_instance is None:
        _intelligence_service_instance = IntelligenceService()
    return _intelligence_service_instance
