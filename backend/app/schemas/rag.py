"""FraudDNA RAG Pydantic Schemas.

Defines schemas for knowledge ingestion, semantic search, document discovery,
and vector retrieval status.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IngestRequest(BaseModel):
    """Request to ingest knowledge documents from directory."""

    model_config = ConfigDict(extra="forbid")

    knowledge_dir: str = Field(
        default="knowledge",
        description="Path to knowledge directory containing policies and cases.",
    )
    force_reload: bool = Field(
        default=False,
        description="Whether to clear existing documents before ingesting.",
    )


class IngestResponse(BaseModel):
    """Result summary of knowledge base ingestion."""

    model_config = ConfigDict(extra="forbid")

    documents_ingested: int = Field(..., description="Count of successfully ingested documents.")
    chunks_created: int = Field(..., description="Count of vector chunks generated.")
    status: str = Field(..., description="Ingestion outcome status (e.g. completed).")
    source_directory: str = Field(..., description="Root knowledge directory processed.")


class SearchRequest(BaseModel):
    """Query payload for semantic similarity search."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(
        ...,
        min_length=1,
        description="Natural language query string describing fraud scenario or policy question.",
        examples=["device collusion escalation threshold"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of relevant chunks to retrieve.",
    )
    min_similarity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum cosine similarity threshold [0.0, 1.0].",
    )
    document_type: str | None = Field(
        default=None,
        description="Optional filter by document type (policy, historical_case, guideline).",
    )
    category: str | None = Field(
        default=None,
        description="Optional filter by category tag (e.g. escalation, device_collusion).",
    )


class SearchResult(BaseModel):
    """A single retrieved evidence chunk with source attribution."""

    model_config = ConfigDict(extra="forbid")

    source_type: str = Field(
        ..., description="Type of source document (policy, historical_case, guideline)."
    )
    source_id: str = Field(
        ..., description="Reference ID (e.g. POL-001, CASE-2025-089) or document ID."
    )
    document_title: str = Field(..., description="Title of the source document.")
    chunk_id: str = Field(..., description="Deterministic chunk identifier.")
    content: str = Field(..., description="Text content of the retrieved chunk.")
    similarity: float = Field(..., description="Cosine similarity score [0.0, 1.0].")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata tags, section title, and file path."
    )


class SearchResponse(BaseModel):
    """Response containing retrieved evidence chunks."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(..., description="Original search query string.")
    total_results: int = Field(..., description="Number of matching results returned.")
    results: list[SearchResult] = Field(
        default_factory=list, description="Ranked list of semantic search results."
    )
    store_status: str = Field(
        default="active",
        description="Vector store availability state (active, degraded, unavailable).",
    )


class DocumentSummary(BaseModel):
    """Summary of an ingested knowledge base document."""

    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(..., description="Deterministic unique document ID.")
    title: str = Field(..., description="Document title.")
    document_type: str = Field(
        ..., description="Type of document (policy, historical_case, guideline)."
    )
    category: str = Field(..., description="Topic category.")
    source_path: str = Field(..., description="Relative file path in knowledge base.")
    chunk_count: int = Field(..., description="Number of vector chunks for this document.")


class DocumentListResponse(BaseModel):
    """Paginated or complete list of ingested documents."""

    model_config = ConfigDict(extra="forbid")

    total_documents: int = Field(..., description="Total documents registered in knowledge base.")
    documents: list[DocumentSummary] = Field(
        default_factory=list, description="List of document summaries."
    )


class DocumentDetailResponse(BaseModel):
    """Full detail of a single document including its generated chunks."""

    model_config = ConfigDict(extra="forbid")

    document_id: str = Field(..., description="Unique document ID.")
    title: str = Field(..., description="Document title.")
    document_type: str = Field(..., description="Document type.")
    category: str = Field(..., description="Document category.")
    source_path: str = Field(..., description="Relative file path.")
    content_hash: str = Field(..., description="SHA-256 content hash.")
    chunk_count: int = Field(..., description="Total chunks for document.")
    chunks: list[dict[str, Any]] = Field(
        default_factory=list, description="Chunk content and metadata."
    )


class RAGStatusResponse(BaseModel):
    """Health and status of the RAG subsystem."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="Overall RAG status (healthy, degraded, unavailable).")
    mode: str = Field(
        default="normal",
        description="Operating mode: 'normal' (PostgreSQL + pgvector) or 'degraded' (in-memory fallback).",
    )
    documents_count: int = Field(..., description="Total documents ingested.")
    chunks_count: int = Field(..., description="Total vector chunks indexed.")
    embedding_provider: str = Field(..., description="Active embedding provider name.")
    vector_store: str = Field(..., description="Active vector store engine.")
    message: str | None = Field(
        default=None, description="Diagnostic message or warning if operating in degraded mode."
    )
