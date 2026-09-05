"""FraudDNA Vector Store Implementations.

Defines the vector storage interface along with:
1. NORMAL: PgVectorVectorStore for production PostgreSQL + pgvector persistence
2. DEGRADED: InMemoryVectorStore for offline development, CI, and test execution
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class VectorRecord:
    """Stored vector item representing a document chunk and its embedding."""

    chunk_id: str
    document_id: str
    content: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseVectorStore(ABC):
    """Abstract interface for vector similarity storage and search."""

    @abstractmethod
    def upsert(self, records: list[VectorRecord]) -> int:
        """Insert or update vector records."""

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        min_similarity: float = 0.0,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[VectorRecord, float]]:
        """Retrieve top-k most similar vector records matching metadata filters."""

    @abstractmethod
    def count(self) -> int:
        """Return total number of stored vectors."""

    @abstractmethod
    def clear(self) -> None:
        """Remove all stored vectors."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether the vector store is reachable."""

    @property
    @abstractmethod
    def store_name(self) -> str:
        """Name of the vector store backend."""

    @property
    @abstractmethod
    def is_degraded(self) -> bool:
        """Return True if running in a fallback/degraded mode."""


class InMemoryVectorStore(BaseVectorStore):
    """High-performance, deterministic in-memory vector store using NumPy cosine similarity.

    Used when PostgreSQL is offline or in isolated unit tests.
    Explicitly operates in DEGRADED mode.
    """

    def __init__(self) -> None:
        self._records: dict[str, VectorRecord] = {}

    @property
    def store_name(self) -> str:
        return "in_memory_fallback"

    @property
    def is_degraded(self) -> bool:
        return True

    def is_available(self) -> bool:
        return True

    def count(self) -> int:
        return len(self._records)

    def clear(self) -> None:
        self._records.clear()

    def upsert(self, records: list[VectorRecord]) -> int:
        """Insert or update records deterministically by chunk_id."""
        for r in records:
            self._records[r.chunk_id] = r
        return len(records)

    def delete_by_document_id(self, document_id: str) -> int:
        """Remove all chunks belonging to a specific document."""
        to_delete = [cid for cid, r in self._records.items() if r.document_id == document_id]
        for cid in to_delete:
            del self._records[cid]
        return len(to_delete)

    def get_record(self, chunk_id: str) -> VectorRecord | None:
        return self._records.get(chunk_id)

    def get_records_by_document(self, document_id: str) -> list[VectorRecord]:
        return [r for r in self._records.values() if r.document_id == document_id]

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        min_similarity: float = 0.0,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[VectorRecord, float]]:
        """Search for top-k vectors matching filters, sorted by (-similarity, chunk_id)."""
        if not self._records:
            return []

        q_vec = np.asarray(query_embedding, dtype=np.float64)
        q_norm = float(np.linalg.norm(q_vec))
        if q_norm > 0:
            q_vec = q_vec / q_norm

        scored_candidates: list[tuple[VectorRecord, float]] = []

        for record in self._records.values():
            if filters and not self._matches_filters(record.metadata, filters):
                continue

            r_vec = np.asarray(record.embedding, dtype=np.float64)
            r_norm = float(np.linalg.norm(r_vec))
            if r_norm > 0:
                r_vec = r_vec / r_norm

            sim = float(np.dot(q_vec, r_vec))
            sim_rounded = round(float(sim), 4)

            if sim_rounded >= min_similarity:
                scored_candidates.append((record, sim_rounded))

        # Deterministic tie-breaker: highest similarity first, then chunk_id alphabetically
        scored_candidates.sort(key=lambda item: (-item[1], item[0].chunk_id))
        return scored_candidates[:top_k]

    @staticmethod
    def _matches_filters(metadata: dict[str, Any], filters: dict[str, Any]) -> bool:
        """Check if metadata satisfies all filter conditions."""
        for key, expected in filters.items():
            if expected is None:
                continue
            actual = metadata.get(key)
            if actual is None:
                return False
            if isinstance(expected, list | set | tuple):
                if actual not in expected:
                    return False
            elif str(actual).lower() != str(expected).lower():
                return False
        return True


class PgVectorVectorStore(BaseVectorStore):
    """Production vector store using PostgreSQL with the pgvector extension.

    Provides persistent, index-accelerated similarity search using cosine distance operator (<=>).
    """

    def __init__(self, connection_url: str | None = None) -> None:
        from sqlalchemy import create_engine

        self._url = connection_url or settings.DATABASE_URL_SYNC
        self._engine = create_engine(self._url, pool_pre_ping=True)

    @property
    def store_name(self) -> str:
        return "postgresql_pgvector"

    @property
    def is_degraded(self) -> bool:
        return False

    def is_available(self) -> bool:
        """Check whether PostgreSQL and the rag_document_chunks table are reachable."""
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1 FROM rag_document_chunks LIMIT 1;"))
            return True
        except Exception as exc:
            logger.debug(f"PgVectorVectorStore connection check failed: {exc}")
            return False

    def count(self) -> int:
        """Count total stored chunks in rag_document_chunks."""
        try:
            with self._engine.connect() as conn:
                res = conn.execute(text("SELECT COUNT(*) FROM rag_document_chunks;"))
                row = res.fetchone()
                return int(row[0]) if row else 0
        except Exception as exc:
            logger.warning(f"Failed to count pgvector chunks: {exc}")
            return 0

    def clear(self) -> None:
        """Remove all chunks from database table."""
        try:
            with self._engine.begin() as conn:
                conn.execute(text("TRUNCATE TABLE rag_document_chunks CASCADE;"))
        except Exception as exc:
            logger.warning(f"Failed to clear pgvector chunks: {exc}")

    def upsert(self, records: list[VectorRecord]) -> int:
        """Upsert records into rag_document_chunks with embedding vector."""
        if not records:
            return 0

        upsert_stmt = text(
            """
            INSERT INTO rag_document_chunks (id, document_id, chunk_index, content, metadata_json, embedding)
            VALUES (:id, :document_id, :chunk_index, :content, :metadata_json, :embedding)
            ON CONFLICT (id) DO UPDATE SET
                content = EXCLUDED.content,
                metadata_json = EXCLUDED.metadata_json,
                embedding = EXCLUDED.embedding;
            """
        )

        with self._engine.begin() as conn:
            for r in records:
                # Format embedding vector as literal array string e.g. '[0.1, 0.2, ...]'
                emb_str = f"[{','.join(f'{x:.6f}' for x in r.embedding)}]"
                conn.execute(
                    upsert_stmt,
                    {
                        "id": r.chunk_id,
                        "document_id": r.document_id,
                        "chunk_index": int(r.metadata.get("chunk_index", 0)),
                        "content": r.content,
                        "metadata_json": json.dumps(r.metadata),
                        "embedding": emb_str,
                    },
                )
        return len(records)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        min_similarity: float = 0.0,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[VectorRecord, float]]:
        """Search top-k chunks using pgvector cosine distance operator (<=>)."""
        emb_str = f"[{','.join(f'{x:.6f}' for x in query_embedding)}]"

        where_clauses = ["1 - (embedding <=> :query_emb) >= :min_sim"]
        params: dict[str, Any] = {
            "query_emb": emb_str,
            "min_sim": float(min_similarity),
            "top_k": int(top_k),
        }

        if filters:
            for key, val in filters.items():
                param_key = f"filter_{key}"
                where_clauses.append(f"metadata_json->>'{key}' = :{param_key}")
                params[param_key] = str(val)

        where_sql = " AND ".join(where_clauses)
        query_sql = text(
            f"""
            SELECT id, document_id, content, metadata_json,
                   ROUND((1 - (embedding <=> :query_emb))::numeric, 4) AS similarity
            FROM rag_document_chunks
            WHERE {where_sql}
            ORDER BY similarity DESC, id ASC
            LIMIT :top_k;
            """
        )

        results: list[tuple[VectorRecord, float]] = []
        with self._engine.connect() as conn:
            rows = conn.execute(query_sql, params).fetchall()
            for row in rows:
                meta = row[3] if isinstance(row[3], dict) else json.loads(row[3])
                rec = VectorRecord(
                    chunk_id=str(row[0]),
                    document_id=str(row[1]),
                    content=str(row[2]),
                    embedding=[],  # Omit raw vector to preserve memory
                    metadata=meta,
                )
                results.append((rec, float(row[4])))

        return results


# Global Vector Store Singleton
_vector_store_instance: BaseVectorStore | None = None


def get_vector_store() -> BaseVectorStore:
    """Dependency provider for vector store.

    Attempts PostgreSQL + pgvector (NORMAL mode).
    If PostgreSQL is unreachable, falls back to InMemoryVectorStore (DEGRADED mode)
    with explicit logging so failure is never silently masked.
    """
    global _vector_store_instance
    if _vector_store_instance is None:
        try:
            pg_store = PgVectorVectorStore()
            if pg_store.is_available():
                logger.info("NORMAL mode: Initialized PgVectorVectorStore connected to PostgreSQL.")
                _vector_store_instance = pg_store
            else:
                logger.warning(
                    "DEGRADED mode: PostgreSQL / pgvector unreachable. "
                    "Falling back to InMemoryVectorStore. Persistent storage is NOT active."
                )
                _vector_store_instance = InMemoryVectorStore()
        except Exception as exc:
            logger.warning(
                f"DEGRADED mode: PostgreSQL initialization error ({exc}). "
                "Falling back to InMemoryVectorStore."
            )
            _vector_store_instance = InMemoryVectorStore()

    return _vector_store_instance
