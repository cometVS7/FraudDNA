"""Unit tests for RAG document parsing and chunking."""

from pathlib import Path

import pytest

from app.rag.ingestion import DocumentChunker, DocumentParser, ParsedDocument


@pytest.fixture
def sample_markdown() -> str:
    return """# POL-999: Test Fraud Prevention Policy

## 1. Scope and Objective
This is a test policy for evaluating document chunking and parsing.

## 2. High Risk Triggers
Transactions above INR 50,000 must be inspected for device anomalies and proxy farm activity.
"""


def test_parser_extracts_title_and_type(sample_markdown: str, tmp_path: Path) -> None:
    test_file = tmp_path / "POL-999_test_policy.md"
    test_file.write_text(sample_markdown, encoding="utf-8")

    parser = DocumentParser()
    doc = parser.parse_file(test_file)

    assert doc.title == "POL-999: Test Fraud Prevention Policy"
    assert doc.document_type == "policy"
    assert doc.metadata.get("reference_id") == "POL-999"


def test_parser_generates_deterministic_ids(sample_markdown: str, tmp_path: Path) -> None:
    test_file = tmp_path / "CASE-2025-001_sample_case.md"
    test_file.write_text(sample_markdown, encoding="utf-8")

    parser = DocumentParser()
    doc1 = parser.parse_file(test_file)
    doc2 = parser.parse_file(test_file)

    assert doc1.document_id == doc2.document_id
    assert doc1.document_id.startswith("doc_")
    assert doc1.content_hash == doc2.content_hash


def test_chunker_creates_deterministic_chunks(sample_markdown: str) -> None:
    doc = ParsedDocument(
        document_id="doc_sample_123",
        title="Test Policy",
        document_type="policy",
        category="escalation",
        source_path="policies/test.md",
        content_hash="abc123hash",
        raw_content=sample_markdown,
        metadata={"reference_id": "POL-999"},
    )

    chunker = DocumentChunker(target_chunk_size=300, chunk_overlap=50)
    chunks1 = chunker.chunk_document(doc)
    chunks2 = chunker.chunk_document(doc)

    assert len(chunks1) == len(chunks2)
    assert len(chunks1) >= 2

    for i, (c1, c2) in enumerate(zip(chunks1, chunks2, strict=False)):
        assert c1.chunk_id == c2.chunk_id
        assert c1.chunk_id == f"doc_sample_123_c{i}"
        assert c1.content == c2.content
        assert c1.metadata["document_id"] == "doc_sample_123"
        assert "section" in c1.metadata
