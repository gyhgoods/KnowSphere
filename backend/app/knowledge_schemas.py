from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.knowledge_models import DocumentStatus, FileParseStatus, SpaceVisibility


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SpaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    code: str = Field(pattern=r"^[a-z0-9_-]+$", min_length=1, max_length=64)
    description: str | None = None
    visibility: SpaceVisibility = SpaceVisibility.PRIVATE
    department_id: int | None = None


class SpaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    visibility: SpaceVisibility | None = None
    department_id: int | None = None
    is_active: bool | None = None


class SpaceRead(ORMModel):
    id: int
    name: str
    code: str
    description: str | None
    visibility: SpaceVisibility
    department_id: int | None
    created_by: int
    is_active: bool
    created_at: datetime


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    parent_id: int | None = None
    sort: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    parent_id: int | None = None
    sort: int | None = None


class CategoryRead(ORMModel):
    id: int
    space_id: int
    parent_id: int | None
    name: str
    sort: int
    children: list["CategoryRead"] = Field(default_factory=list)


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    color: str = Field(default="#087f61", pattern=r"^#[0-9a-fA-F]{6}$")


class TagRead(ORMModel):
    id: int
    name: str
    color: str
    usage_count: int


class DocumentCreate(BaseModel):
    space_id: int
    category_id: int | None = None
    title: str = Field(min_length=1, max_length=255)
    content: str = ""
    content_format: str = Field(default="markdown", pattern=r"^(markdown|plain|html)$")
    tag_ids: list[int] = Field(default_factory=list)


class DocumentUpdate(BaseModel):
    category_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = None
    content_format: str | None = Field(default=None, pattern=r"^(markdown|plain|html)$")
    tag_ids: list[int] | None = None


class ReviewRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)


class VersionRead(ORMModel):
    id: int
    document_id: int
    version_no: int
    title: str
    content: str
    content_format: str
    created_by: int
    created_at: datetime


class FileRead(ORMModel):
    id: int
    document_id: int
    file_name: str
    mime_type: str
    file_size: int
    checksum: str
    uploaded_by: int
    parse_status: FileParseStatus
    parse_task_id: str | None
    parse_error: str | None
    parsed_text_length: int = 0
    created_at: datetime


class FileParseRead(BaseModel):
    id: int
    parse_status: FileParseStatus
    parse_task_id: str | None
    parse_error: str | None
    parsed_text: str | None
    parse_started_at: datetime | None
    parse_completed_at: datetime | None


class FileAccess(BaseModel):
    url: str
    expires_in: int
    previewable: bool


class DocumentRead(ORMModel):
    id: int
    space_id: int
    category_id: int | None
    title: str
    content: str
    content_format: str
    status: DocumentStatus
    author_id: int
    reviewer_id: int | None
    review_comment: str | None
    version_no: int
    tags: list[TagRead]
    created_at: datetime
    updated_at: datetime
