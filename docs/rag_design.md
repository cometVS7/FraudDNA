# FraudDNA RAG Architecture & Design

## 1. Overview & Purpose

The **Retrieval-Augmented Generation (RAG)** infrastructure provides verified, grounded policy and historical-case context to the FraudDNA platform and future AI investigation agents (Phase 5).

```text
                               +---------------------------------+
                               |   knowledge/                    |
                               |   ├── policies/                 |
                               |   ├── guidelines/               |
                               |   └── historical_cases/         |
                               +----------------+----------------+
                                                |
                                                v
                               +---------------------------------+
                               | IngestionPipeline               |
                               | (Deterministic Parsing/Chunking)|
                               +----------------+----------------+
                                                |
                                                v
                               +---------------------------------+
                               | BaseEmbeddingProvider           |
                               | (DeterministicLocal / External) |
                               +----------------+----------------+
                                                |
                                                v
                               +---------------------------------+
                               | BaseVectorStore                 |
                               | (NORMAL: PgVectorVectorStore    |
                               |  DEGRADED: InMemoryVectorStore) |
                               +----------------+----------------+
                                                |
                                                v
+-------------------------------+      +-------------------------+
| Query via POST /api/v1/rag/search| -> | RAGService              |
+-------------------------------+      | (Cosine Sim + Filtering)|
                                       +------------+------------+
                                                    |
                                                    v
                                       +-------------------------+
                                       | SearchResponse          |
                                       | [Grounded Evidence]     |
                                       +-------------------------+
```

---

## 2. Hard Security & AI Boundaries

RAG acts strictly as an evidentiary knowledge store. It is governed by non-negotiable boundaries:
- **NO Financial Decisions**: RAG does not approve, block, refund, or hold payments.
- **NO Autonomous Mutation**: RAG cannot alter transaction data, ML risk scores, or graph cluster state.
- **NO Hallucinated Evidence**: When queries match no documents or when services are unavailable, RAG returns an explicit empty or degraded state. Fake or random evidence is strictly prohibited.
- **Defense-Only Evidence**: All outputs are traceable to verified source documents (`source_type`, `source_id`, `chunk_id`, `similarity`).

---

## 3. Ingestion & Chunking Strategy

### A. Document Discovery & Parsing
- Recursively discovers `.md` and `.txt` files under `knowledge/`.
- Extracts document titles from `# Title` headings or sanitized filenames.
- Infers `document_type` (`policy`, `historical_case`, `guideline`) and `category` (`escalation`, `merchant_risk`, `device_collusion`, `proxy_farm`, `card_cycling`, `evidence_standards`).
- Computes `content_hash` via SHA-256 for duplicate detection.
- Generates deterministic `document_id`:
  ```text
  document_id = "doc_" + sha256(normalized_relative_path)[:16]
  ```

### B. Section-Aware Chunking
- Splits documents on major markdown headings (`## Section Header`).
- Segments sections larger than target chunk size (~500 characters) with a sliding window (~100 character overlap).
- Preserves context by prepending `[Document Title > Section Title]` to each chunk.
- Generates deterministic `chunk_id`:
  ```text
  chunk_id = f"{document_id}_c{chunk_index}"
  ```
- **Idempotency**: Re-ingesting unchanged documents is a no-op; re-ingesting modified documents replaces existing chunks cleanly without creating duplicates.

---

## 4. Embedding Provider Abstraction

The interface [`BaseEmbeddingProvider`](file:///c:/Users/mailv/Desktop/SIT/Razorpay%20Buildathon/FraudDNA/backend/app/rag/embeddings.py) abstracts embedding generation:

1. **`DeterministicLocalEmbeddingProvider`** (Development / Testing):
   - Generates 384-dimensional dense vectors using word/bigram/character feature hashing with L2 unit normalization.
   - 100% reproducible, zero network latency, zero external API cost.
   - Used for development and test suites to eliminate paid API requirements.
   - *Note*: Not equivalent to dense transformer embeddings intended for production.
2. **`ExternalAPIEmbeddingProvider`** (Production):
   - Connects to standard HTTP embedding endpoints (e.g. OpenAI `text-embedding-3-small` or Voyage) using `EMBEDDING_API_KEY`.
   - Strict timeout controls and explicit `EmbeddingProviderError` on network or quota failure.

---

## 5. Storage Modes: NORMAL vs DEGRADED

The architecture explicitly differentiates between production persistence and offline fallback:

### NORMAL Mode: PostgreSQL + pgvector (`PgVectorVectorStore`)
- Active when the PostgreSQL database container with pgvector extension is running.
- **SQLAlchemy Models**: [`DocumentModel`](file:///c:/Users/mailv/Desktop/SIT/Razorpay%20Buildathon/FraudDNA/backend/app/models/rag.py) (`rag_documents`) and [`DocumentChunkModel`](file:///c:/Users/mailv/Desktop/SIT/Razorpay%20Buildathon/FraudDNA/backend/app/models/rag.py) (`rag_document_chunks`).
- **Alembic Migration**: [`backend/alembic/versions/0001_create_rag_tables.py`](file:///c:/Users/mailv/Desktop/SIT/Razorpay%20Buildathon/FraudDNA/backend/alembic/versions/0001_create_rag_tables.py) creates tables, vector extension, and cosine index.
- **Similarity Search**: Accelerated using pgvector's cosine distance operator (`<=>`).
- **Reported Status**: `status="healthy"`, `mode="normal"`, `vector_store="postgresql_pgvector"`.

### DEGRADED Mode: In-Memory Fallback (`InMemoryVectorStore`)
- Active when PostgreSQL is unreachable (e.g. Docker daemon stopped, local developer machine without database running, or isolated CI unit tests).
- Uses NumPy dot product for exact cosine similarity calculation and deterministic tie-breaking:
  $$\text{sim}(q, r) = \frac{q \cdot r}{\|q\| \|r\|}$$
- **Never Silently Masks Failure**:
  - `GET /api/v1/rag/status` reports `status="degraded"`, `mode="degraded"`, `vector_store="in_memory_fallback"`, and includes an explicit warning message:
    `"PostgreSQL persistent vector store is unavailable; operating in degraded in-memory mode."`
  - `POST /api/v1/rag/search` response sets `store_status="degraded"`.

---

## 6. API Contract

### Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/rag/ingest` | Ingests and indexes all knowledge documents |
| `POST` | `/api/v1/rag/search` | Grounded semantic search with optional metadata filters |
| `GET` | `/api/v1/rag/documents` | Lists all ingested documents and chunk counts |
| `GET` | `/api/v1/rag/documents/{id}` | Retrieves document detail and constituent chunks |
| `GET` | `/api/v1/rag/status` | Reports RAG health, vector store state, operating mode, and diagnostic message |

### Example Search Response (Degraded Fallback Mode)
```json
{
  "query": "device ring emulator collusion",
  "total_results": 1,
  "results": [
    {
      "source_type": "historical_case",
      "source_id": "CASE-2025-089",
      "document_title": "CASE-2025-089: Synthetic Device Ring with Multi-Account Emulator Collusion",
      "chunk_id": "doc_c96305d90ffc2669_c0",
      "content": "[CASE-2025-089... > Summary of Incident]\nA coordinated fraud network operated 40 distinct synthetic customer profiles...",
      "similarity": 0.8421,
      "metadata": {
        "doc_type": "historical_case",
        "category": "device_collusion",
        "reference_id": "CASE-2025-089"
      }
    }
  ],
  "store_status": "degraded"
}
```

---

## 7. Phase 5 AI Agent Integration Point

In **Phase 5 (AI Investigation Agent)**, LangGraph workflows will consume this RAG infrastructure via allowlisted tools:
- `retrieve_policy_guidance(query: str, category: str | None = None)`
- `retrieve_historical_precedents(query: str)`

The agent receives structured `SearchResult` items with explicit attributions, synthesizing reasoning strictly bounded by verified policies and historical cases.
