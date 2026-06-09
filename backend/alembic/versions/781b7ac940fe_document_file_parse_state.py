"""document file parse state

Revision ID: 781b7ac940fe
Revises: 6d3a0e85b9c2
Create Date: 2026-06-09 15:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "781b7ac940fe"
down_revision: str | None = "6d3a0e85b9c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "kb_document_file",
        sa.Column(
            "parse_status",
            sa.Enum(
                "QUEUED",
                "PROCESSING",
                "COMPLETED",
                "FAILED",
                "UNSUPPORTED",
                name="fileparsestatus",
                native_enum=False,
            ),
            server_default="QUEUED",
            nullable=False,
        ),
    )
    op.add_column("kb_document_file", sa.Column("parse_task_id", sa.String(64)))
    op.add_column("kb_document_file", sa.Column("parsed_text", sa.Text()))
    op.add_column("kb_document_file", sa.Column("parse_error", sa.Text()))
    op.add_column(
        "kb_document_file", sa.Column("parse_started_at", sa.DateTime(timezone=True))
    )
    op.add_column(
        "kb_document_file", sa.Column("parse_completed_at", sa.DateTime(timezone=True))
    )
    op.create_index(
        op.f("ix_kb_document_file_parse_status"),
        "kb_document_file",
        ["parse_status"],
    )
    op.create_index(
        op.f("ix_kb_document_file_parse_task_id"),
        "kb_document_file",
        ["parse_task_id"],
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_kb_document_file_parse_task_id"), table_name="kb_document_file"
    )
    op.drop_index(
        op.f("ix_kb_document_file_parse_status"), table_name="kb_document_file"
    )
    op.drop_column("kb_document_file", "parse_completed_at")
    op.drop_column("kb_document_file", "parse_started_at")
    op.drop_column("kb_document_file", "parse_error")
    op.drop_column("kb_document_file", "parsed_text")
    op.drop_column("kb_document_file", "parse_task_id")
    op.drop_column("kb_document_file", "parse_status")
