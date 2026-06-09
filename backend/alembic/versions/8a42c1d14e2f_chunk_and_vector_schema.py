"""chunk and vector schema

Revision ID: 8a42c1d14e2f
Revises: 781b7ac940fe
Create Date: 2026-06-09 18:00:00
"""

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa

from alembic import op

revision: str = "8a42c1d14e2f"
down_revision: str | None = "781b7ac940fe"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "kb_chunk",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=True),
        sa.Column("source_key", sa.String(length=64), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"], ["kb_document.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["file_id"], ["kb_document_file.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "source_key",
            "chunk_index",
            name="uq_chunk_document_source_index",
        ),
    )
    op.create_index(op.f("ix_kb_chunk_document_id"), "kb_chunk", ["document_id"])
    op.create_index(op.f("ix_kb_chunk_file_id"), "kb_chunk", ["file_id"])
    op.create_index(op.f("ix_kb_chunk_source_key"), "kb_chunk", ["source_key"])
    op.create_index(op.f("ix_kb_chunk_content_hash"), "kb_chunk", ["content_hash"])
    op.create_table(
        "kb_embedding",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=False),
        sa.Column(
            "embedding", pgvector.sqlalchemy.Vector(dim=1024), nullable=False
        ),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["chunk_id"], ["kb_chunk.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chunk_id"),
    )
    op.create_index(op.f("ix_kb_embedding_chunk_id"), "kb_embedding", ["chunk_id"])
    op.create_index(
        op.f("ix_kb_embedding_model_name"), "kb_embedding", ["model_name"]
    )
    op.execute(
        "CREATE INDEX ix_kb_embedding_hnsw ON kb_embedding "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_kb_embedding_hnsw")
    op.drop_table("kb_embedding")
    op.drop_table("kb_chunk")
