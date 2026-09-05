"""Create RAG documents and chunks tables with pgvector extension.

Revision ID: 0001_rag_tables
Revises:
Create Date: 2026-09-05 07:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_rag_tables"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Enable pgvector extension if available in PostgreSQL
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Create rag_documents table
    op.create_table(
        "rag_documents",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("source_path", sa.String(length=512), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_rag_documents_document_type", "rag_documents", ["document_type"])
    op.create_index("ix_rag_documents_category", "rag_documents", ["category"])

    # 3. Create rag_document_chunks table
    op.create_table(
        "rag_document_chunks",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column(
            "document_id",
            sa.String(length=64),
            sa.ForeignKey("rag_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_rag_document_chunks_document_id", "rag_document_chunks", ["document_id"])

    # Attempt to add pgvector column (384 dimensions matching default provider)
    try:
        op.execute(
            "ALTER TABLE rag_document_chunks ADD COLUMN IF NOT EXISTS embedding vector(384);"
        )
        # Add vector cosine distance index for production similarity search
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_rag_document_chunks_embedding_cosine "
            "ON rag_document_chunks USING hnsw (embedding vector_cosine_ops);"
        )
    except Exception:
        # Fallback for environments where pgvector extension cannot be loaded directly
        pass


def downgrade() -> None:
    op.drop_index("ix_rag_document_chunks_document_id", table_name="rag_document_chunks")
    op.drop_table("rag_document_chunks")
    op.drop_index("ix_rag_documents_category", table_name="rag_documents")
    op.drop_index("ix_rag_documents_document_type", table_name="rag_documents")
    op.drop_table("rag_documents")
