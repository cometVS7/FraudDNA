"""FraudDNA Knowledge Ingestion and Chunking Module.

Handles deterministic parsing of Markdown policy documents, guidelines, and historical cases,
generating stable document IDs, semantic chunks, and rich source metadata.
"""

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DocumentChunk:
    """Represents a deterministic chunk of a parsed document."""

    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedDocument:
    """Represents an ingested knowledge document with extracted metadata."""

    document_id: str
    title: str
    document_type: str
    category: str
    source_path: str
    content_hash: str
    raw_content: str
    metadata: dict[str, Any]
    chunks: list[DocumentChunk] = field(default_factory=list)


class DocumentParser:
    """Parses markdown files, extracting title, category, metadata, and deterministic IDs."""

    @staticmethod
    def extract_title(content: str, fallback_filename: str) -> str:
        """Extract first H1 markdown heading or clean fallback filename."""
        for line in content.splitlines():
            line_stripped = line.strip()
            if line_stripped.startswith("# "):
                return line_stripped[2:].strip()
        # Fallback to readable filename
        clean_name = Path(fallback_filename).stem.replace("_", " ").replace("-", " ")
        return clean_name.title()

    @staticmethod
    def infer_document_type(file_path: Path) -> str:
        """Infer document type from directory structure or filename."""
        path_str = str(file_path).lower()
        if "policies" in path_str or file_path.name.startswith("POL-"):
            return "policy"
        if "historical_cases" in path_str or file_path.name.startswith("CASE-"):
            return "historical_case"
        if "guidelines" in path_str or file_path.name.startswith("GDL-"):
            return "guideline"
        return "general"

    @staticmethod
    def infer_category(file_path: Path, content: str) -> str:
        """Infer category tag from path and content keywords."""
        name_lower = file_path.stem.lower()
        content_lower = content.lower()

        if "escalat" in name_lower or "sla" in content_lower:
            return "escalation"
        if "merchant" in name_lower:
            return "merchant_risk"
        if "review" in name_lower:
            return "transaction_review"
        if "device" in name_lower or "emulator" in content_lower:
            return "device_collusion"
        if "proxy" in name_lower or "vpn" in content_lower:
            return "proxy_farm"
        if "card" in name_lower or "cycling" in content_lower:
            return "card_cycling"
        if "evidence" in name_lower:
            return "evidence_standards"
        return "fraud_defense"

    @staticmethod
    def generate_document_id(relative_path: str) -> str:
        """Generate a deterministic document identifier based on normalized relative path."""
        norm_path = relative_path.replace("\\", "/").lower()
        h = hashlib.sha256(norm_path.encode("utf-8")).hexdigest()[:16]
        return f"doc_{h}"

    @staticmethod
    def generate_content_hash(content: str) -> str:
        """Compute SHA-256 hash of document raw content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def parse_file(self, file_path: Path, base_dir: Path | None = None) -> ParsedDocument:
        """Parse a single markdown file into a ParsedDocument."""
        if not file_path.exists():
            raise FileNotFoundError(f"File {file_path} not found.")

        raw_content = file_path.read_text(encoding="utf-8")
        rel_path = str(file_path.relative_to(base_dir)) if base_dir else file_path.name

        doc_id = self.generate_document_id(rel_path)
        title = self.extract_title(raw_content, file_path.name)
        doc_type = self.infer_document_type(file_path)
        category = self.infer_category(file_path, raw_content)
        content_hash = self.generate_content_hash(raw_content)

        metadata: dict[str, Any] = {
            "filename": file_path.name,
            "relative_path": rel_path.replace("\\", "/"),
            "doc_type": doc_type,
            "category": category,
        }

        # Extract identifier from filename (e.g. POL-001, CASE-2025-089)
        id_match = re.search(r"(POL-\d+|CASE-[\d-]+|GDL-\d+)", file_path.stem)
        if id_match:
            metadata["reference_id"] = id_match.group(1)

        return ParsedDocument(
            document_id=doc_id,
            title=title,
            document_type=doc_type,
            category=category,
            source_path=rel_path.replace("\\", "/"),
            content_hash=content_hash,
            raw_content=raw_content,
            metadata=metadata,
        )


class DocumentChunker:
    """Splits parsed documents into deterministic semantic chunks with section context."""

    def __init__(
        self,
        target_chunk_size: int = 500,
        chunk_overlap: int = 100,
    ) -> None:
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: ParsedDocument) -> list[DocumentChunk]:
        """Split document into section-aware chunks."""
        sections = self._split_into_sections(document.raw_content)
        chunks: list[DocumentChunk] = []
        chunk_idx = 0

        for section_title, section_text in sections:
            # Skip empty sections
            if not section_text.strip():
                continue

            section_chunks = self._chunk_section(
                doc_title=document.title,
                section_title=section_title,
                text=section_text,
            )

            for text_chunk in section_chunks:
                chunk_id = f"{document.document_id}_c{chunk_idx}"
                chunk_meta = {
                    **document.metadata,
                    "title": document.title,
                    "section": section_title,
                    "chunk_index": chunk_idx,
                    "document_id": document.document_id,
                }

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=document.document_id,
                        chunk_index=chunk_idx,
                        content=text_chunk,
                        metadata=chunk_meta,
                    )
                )
                chunk_idx += 1

        # Fallback if document had no chunks
        if not chunks:
            chunk_id = f"{document.document_id}_c0"
            chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    chunk_index=0,
                    content=document.raw_content[: self.target_chunk_size],
                    metadata={
                        **document.metadata,
                        "title": document.title,
                        "chunk_index": 0,
                        "document_id": document.document_id,
                    },
                )
            )

        # Update total_chunks in chunk metadata
        total_chunks = len(chunks)
        for c in chunks:
            c.metadata["total_chunks"] = total_chunks

        return chunks

    def _split_into_sections(self, content: str) -> list[tuple[str, str]]:
        """Split markdown content by H2 headers (## Header)."""
        lines = content.splitlines()
        sections: list[tuple[str, list[str]]] = []
        current_title = "Overview"
        current_lines: list[str] = []

        for line in lines:
            if line.startswith("## "):
                if current_lines:
                    sections.append((current_title, current_lines))
                    current_lines = []
                current_title = line[3:].strip()
            else:
                current_lines.append(line)

        if current_lines:
            sections.append((current_title, current_lines))

        return [(title, "\n".join(body_lines).strip()) for title, body_lines in sections]

    def _chunk_section(self, doc_title: str, section_title: str, text: str) -> list[str]:
        """Chunk a section text with sliding window overlap and title header context."""
        prefix = f"[{doc_title} > {section_title}]\n"
        effective_chunk_size = max(200, self.target_chunk_size - len(prefix))

        if len(text) <= effective_chunk_size:
            return [prefix + text]

        paragraphs = text.split("\n\n")
        chunks: list[str] = []
        current_block: list[str] = []
        current_len = 0

        for p in paragraphs:
            p_len = len(p)
            if current_len + p_len > effective_chunk_size and current_block:
                full_chunk = prefix + "\n\n".join(current_block)
                chunks.append(full_chunk)
                current_block = [p]
                current_len = p_len
            else:
                current_block.append(p)
                current_len += p_len + 2

        if current_block:
            full_chunk = prefix + "\n\n".join(current_block)
            chunks.append(full_chunk)

        return chunks


class IngestionPipeline:
    """Orchestrates parsing and chunking of knowledge base files."""

    def __init__(
        self,
        parser: DocumentParser | None = None,
        chunker: DocumentChunker | None = None,
    ) -> None:
        self.parser = parser or DocumentParser()
        self.chunker = chunker or DocumentChunker()

    def process_directory(self, root_dir: Path | str) -> list[ParsedDocument]:
        """Discover and process all .md/.txt files in knowledge directory."""
        path = Path(root_dir)
        if not path.exists():
            return []

        # Find all markdown and text files, sorted deterministically
        supported_files = sorted(
            [f for f in path.rglob("*") if f.is_file() and f.suffix.lower() in {".md", ".txt"}]
        )

        documents: list[ParsedDocument] = []
        for file_path in supported_files:
            try:
                doc = self.parser.parse_file(file_path, base_dir=path)
                chunks = self.chunker.chunk_document(doc)
                doc.chunks = chunks
                documents.append(doc)
            except Exception as e:
                print(f"Warning: Failed to parse {file_path}: {e}")

        return documents
