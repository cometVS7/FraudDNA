"""FraudDNA RAG API Endpoints.

Exposes REST endpoints for knowledge base ingestion, semantic similarity search,
document inspection, and vector store health status.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.rag.retrieval import RAGService, get_rag_service
from app.schemas.rag import (
    DocumentDetailResponse,
    DocumentListResponse,
    IngestRequest,
    IngestResponse,
    RAGStatusResponse,
    SearchRequest,
    SearchResponse,
)

router = APIRouter(prefix="/rag", tags=["FraudDNA RAG"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest Knowledge Base",
    description="Parses, chunks, and indexes all policy and case documents into the vector store.",
)
def ingest_knowledge(
    payload: IngestRequest | None = None,
    rag_service: RAGService = Depends(get_rag_service),
) -> IngestResponse:
    """Trigger ingestion of policies, guidelines, and historical cases."""
    kdir = payload.knowledge_dir if payload else "knowledge"
    force = payload.force_reload if payload else False
    return rag_service.ingest_knowledge_directory(knowledge_dir=kdir, force_reload=force)


@router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic Knowledge Search",
    description="Executes grounded semantic vector search across policies and historical cases.",
)
def search_knowledge(
    payload: SearchRequest,
    rag_service: RAGService = Depends(get_rag_service),
) -> SearchResponse:
    """Search knowledge base with semantic similarity and optional metadata filters."""
    filters: dict[str, str] = {}
    if payload.document_type:
        filters["doc_type"] = payload.document_type
    if payload.category:
        filters["category"] = payload.category

    return rag_service.search(
        query=payload.query,
        top_k=payload.top_k,
        min_similarity=payload.min_similarity,
        filters=filters or None,
    )


@router.get(
    "/documents",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Ingested Documents",
    description="Returns metadata summaries of all documents currently indexed in the knowledge base.",
)
def list_documents(
    rag_service: RAGService = Depends(get_rag_service),
) -> DocumentListResponse:
    """Retrieve all ingested documents."""
    return rag_service.list_documents()


@router.get(
    "/documents/{document_id}",
    response_model=DocumentDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Document Detail",
    description="Retrieves a specific document and its constituent chunks by document ID.",
)
def get_document(
    document_id: str,
    rag_service: RAGService = Depends(get_rag_service),
) -> DocumentDetailResponse:
    """Retrieve document details and chunk breakdown."""
    doc = rag_service.get_document_by_id(document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found in knowledge base.",
        )
    return doc


@router.get(
    "/status",
    response_model=RAGStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="RAG Subsystem Status",
    description="Check operational health, document counts, and active providers for RAG.",
)
def get_status(
    rag_service: RAGService = Depends(get_rag_service),
) -> RAGStatusResponse:
    """Return RAG subsystem operational status."""
    return rag_service.get_status()
