from datetime import datetime
from enum import StrEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base, TimestampMixin


class SpaceVisibility(StrEnum):
    PRIVATE = "private"
    DEPARTMENT = "department"
    PUBLIC = "public"


class DocumentStatus(StrEnum):
    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class FileParseStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    UNSUPPORTED = "unsupported"


document_tags = Table(
    "kb_document_tag",
    Base.metadata,
    Column("document_id", ForeignKey("kb_document.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("kb_tag.id", ondelete="CASCADE"), primary_key=True),
)


class KnowledgeSpace(Base, TimestampMixin):
    __tablename__ = "kb_space"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    visibility: Mapped[SpaceVisibility] = mapped_column(
        Enum(SpaceVisibility, native_enum=False), default=SpaceVisibility.PRIVATE
    )
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_department.id", ondelete="SET NULL"), index=True
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="RESTRICT"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    categories: Mapped[list["Category"]] = relationship(
        back_populates="space", cascade="all, delete-orphan", passive_deletes=True
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="space", passive_deletes=True
    )


class Category(Base, TimestampMixin):
    __tablename__ = "kb_category"
    __table_args__ = (
        UniqueConstraint("space_id", "parent_id", "name", name="uq_category_sibling_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    space_id: Mapped[int] = mapped_column(
        ForeignKey("kb_space.id", ondelete="CASCADE"), index=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("kb_category.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(100))
    sort: Mapped[int] = mapped_column(Integer, default=0)

    space: Mapped[KnowledgeSpace] = relationship(back_populates="categories")
    parent: Mapped["Category | None"] = relationship(
        remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Category"]] = relationship(
        back_populates="parent", passive_deletes=True
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="category", passive_deletes=True
    )


class Tag(Base, TimestampMixin):
    __tablename__ = "kb_tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    color: Mapped[str] = mapped_column(String(16), default="#087f61")
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    documents: Mapped[list["Document"]] = relationship(
        secondary=document_tags, back_populates="tags"
    )


class Document(Base, TimestampMixin):
    __tablename__ = "kb_document"

    id: Mapped[int] = mapped_column(primary_key=True)
    space_id: Mapped[int] = mapped_column(
        ForeignKey("kb_space.id", ondelete="CASCADE"), index=True
    )
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("kb_category.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255), index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    content_format: Mapped[str] = mapped_column(String(20), default="markdown")
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, native_enum=False), default=DocumentStatus.DRAFT, index=True
    )
    author_id: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="RESTRICT"))
    reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("sys_user.id", ondelete="SET NULL")
    )
    review_comment: Mapped[str | None] = mapped_column(Text)
    version_no: Mapped[int] = mapped_column(Integer, default=1)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    space: Mapped[KnowledgeSpace] = relationship(back_populates="documents")
    category: Mapped[Category | None] = relationship(back_populates="documents")
    tags: Mapped[list[Tag]] = relationship(
        secondary=document_tags, back_populates="documents", lazy="selectin"
    )
    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    files: Mapped[list["DocumentFile"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True
    )


class DocumentVersion(Base):
    __tablename__ = "kb_document_version"
    __table_args__ = (
        UniqueConstraint("document_id", "version_no", name="uq_document_version"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("kb_document.id", ondelete="CASCADE"), index=True
    )
    version_no: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    content_format: Mapped[str] = mapped_column(String(20))
    created_by: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    document: Mapped[Document] = relationship(back_populates="versions")


class DocumentFile(Base, TimestampMixin):
    __tablename__ = "kb_document_file"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("kb_document.id", ondelete="CASCADE"), index=True
    )
    file_name: Mapped[str] = mapped_column(String(255))
    object_name: Mapped[str] = mapped_column(String(512), unique=True)
    mime_type: Mapped[str] = mapped_column(String(128))
    file_size: Mapped[int] = mapped_column(BigInteger)
    checksum: Mapped[str] = mapped_column(String(64))
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("sys_user.id", ondelete="RESTRICT"))
    parse_status: Mapped[FileParseStatus] = mapped_column(
        Enum(FileParseStatus, native_enum=False),
        default=FileParseStatus.QUEUED,
        index=True,
    )
    parse_task_id: Mapped[str | None] = mapped_column(String(64), index=True)
    parsed_text: Mapped[str | None] = mapped_column(Text)
    parse_error: Mapped[str | None] = mapped_column(Text)
    parse_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    parse_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    document: Mapped[Document] = relationship(back_populates="files")
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="file", cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def parsed_text_length(self) -> int:
        return len(self.parsed_text or "")


class KnowledgeChunk(Base, TimestampMixin):
    __tablename__ = "kb_chunk"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "source_key",
            "chunk_index",
            name="uq_chunk_document_source_index",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("kb_document.id", ondelete="CASCADE"), index=True
    )
    file_id: Mapped[int | None] = mapped_column(
        ForeignKey("kb_document_file.id", ondelete="CASCADE"), index=True
    )
    source_key: Mapped[str] = mapped_column(String(64), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    chunk_metadata: Mapped[dict[str, object]] = mapped_column(
        "metadata", JSON, default=dict
    )

    document: Mapped[Document] = relationship(back_populates="chunks")
    file: Mapped[DocumentFile | None] = relationship(back_populates="chunks")
    embedding: Mapped["KnowledgeEmbedding | None"] = relationship(
        back_populates="chunk", cascade="all, delete-orphan", uselist=False
    )


class KnowledgeEmbedding(Base, TimestampMixin):
    __tablename__ = "kb_embedding"

    id: Mapped[int] = mapped_column(primary_key=True)
    chunk_id: Mapped[int] = mapped_column(
        ForeignKey("kb_chunk.id", ondelete="CASCADE"), unique=True, index=True
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(1024))
    model_name: Mapped[str] = mapped_column(String(100), index=True)

    chunk: Mapped[KnowledgeChunk] = relationship(back_populates="embedding")
