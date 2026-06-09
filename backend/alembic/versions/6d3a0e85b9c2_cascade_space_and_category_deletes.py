"""cascade space and category deletes

Revision ID: 6d3a0e85b9c2
Revises: 41ef9067fd7f
Create Date: 2026-06-09 12:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "6d3a0e85b9c2"
down_revision: str | None = "41ef9067fd7f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(
        "fk_kb_document_category_id_kb_category", "kb_document", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_kb_document_category_id_kb_category"),
        "kb_document",
        "kb_category",
        ["category_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "fk_kb_category_parent_id_kb_category", "kb_category", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_kb_category_parent_id_kb_category"),
        "kb_category",
        "kb_category",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_kb_category_parent_id_kb_category", "kb_category", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_kb_category_parent_id_kb_category"),
        "kb_category",
        "kb_category",
        ["parent_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.drop_constraint(
        "fk_kb_document_category_id_kb_category", "kb_document", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_kb_document_category_id_kb_category"),
        "kb_document",
        "kb_category",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )
