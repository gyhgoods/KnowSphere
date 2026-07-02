"""AI RAG and knowledge graph schema

Revision ID: a9d8b4f2c731
Revises: 8a42c1d14e2f
Create Date: 2026-07-02 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a9d8b4f2c731"
down_revision: str | None = "8a42c1d14e2f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "kg_entity",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_kg_entity")),
        sa.UniqueConstraint("name", "entity_type", name="uq_kg_entity_name_type"),
    )
    op.create_index(op.f("ix_kg_entity_name"), "kg_entity", ["name"])
    op.create_index(op.f("ix_kg_entity_entity_type"), "kg_entity", ["entity_type"])

    op.create_table(
        "ai_conversation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("ACTIVE", "ARCHIVED", native_enum=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["sys_user.id"], ondelete="CASCADE", name=op.f("fk_ai_conversation_user_id_sys_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_conversation")),
    )
    op.create_index(op.f("ix_ai_conversation_user_id"), "ai_conversation", ["user_id"])

    op.create_table(
        "kg_relation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_entity_id", sa.Integer(), nullable=False),
        sa.Column("target_entity_id", sa.Integer(), nullable=False),
        sa.Column("relation_type", sa.String(length=64), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["kb_document.id"], ondelete="CASCADE", name=op.f("fk_kg_relation_document_id_kb_document")),
        sa.ForeignKeyConstraint(["source_entity_id"], ["kg_entity.id"], ondelete="CASCADE", name=op.f("fk_kg_relation_source_entity_id_kg_entity")),
        sa.ForeignKeyConstraint(["target_entity_id"], ["kg_entity.id"], ondelete="CASCADE", name=op.f("fk_kg_relation_target_entity_id_kg_entity")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_kg_relation")),
        sa.UniqueConstraint("source_entity_id", "target_entity_id", "relation_type", "document_id", name="uq_kg_relation_document"),
    )
    op.create_index(op.f("ix_kg_relation_document_id"), "kg_relation", ["document_id"])
    op.create_index(op.f("ix_kg_relation_relation_type"), "kg_relation", ["relation_type"])
    op.create_index(op.f("ix_kg_relation_source_entity_id"), "kg_relation", ["source_entity_id"])
    op.create_index(op.f("ix_kg_relation_target_entity_id"), "kg_relation", ["target_entity_id"])

    op.create_table(
        "ai_message",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.Enum("USER", "ASSISTANT", native_enum=False), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversation.id"], ondelete="CASCADE", name=op.f("fk_ai_message_conversation_id_ai_conversation")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_message")),
    )
    op.create_index(op.f("ix_ai_message_conversation_id"), "ai_message", ["conversation_id"])

    op.create_table(
        "ai_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("rating", sa.Enum("HELPFUL", "UNHELPFUL", native_enum=False), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["ai_message.id"], ondelete="CASCADE", name=op.f("fk_ai_feedback_message_id_ai_message")),
        sa.ForeignKeyConstraint(["user_id"], ["sys_user.id"], ondelete="CASCADE", name=op.f("fk_ai_feedback_user_id_sys_user")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_feedback")),
        sa.UniqueConstraint("message_id", "user_id", name="uq_ai_feedback_message_user"),
    )
    op.create_index(op.f("ix_ai_feedback_message_id"), "ai_feedback", ["message_id"])
    op.create_index(op.f("ix_ai_feedback_user_id"), "ai_feedback", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_feedback_user_id"), table_name="ai_feedback")
    op.drop_index(op.f("ix_ai_feedback_message_id"), table_name="ai_feedback")
    op.drop_table("ai_feedback")
    op.drop_index(op.f("ix_ai_message_conversation_id"), table_name="ai_message")
    op.drop_table("ai_message")
    op.drop_index(op.f("ix_kg_relation_target_entity_id"), table_name="kg_relation")
    op.drop_index(op.f("ix_kg_relation_source_entity_id"), table_name="kg_relation")
    op.drop_index(op.f("ix_kg_relation_relation_type"), table_name="kg_relation")
    op.drop_index(op.f("ix_kg_relation_document_id"), table_name="kg_relation")
    op.drop_table("kg_relation")
    op.drop_index(op.f("ix_ai_conversation_user_id"), table_name="ai_conversation")
    op.drop_table("ai_conversation")
    op.drop_index(op.f("ix_kg_entity_entity_type"), table_name="kg_entity")
    op.drop_index(op.f("ix_kg_entity_name"), table_name="kg_entity")
    op.drop_table("kg_entity")
