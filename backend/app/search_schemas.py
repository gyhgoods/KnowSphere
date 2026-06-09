from datetime import datetime

from pydantic import BaseModel, Field


class ChunkRead(BaseModel):
    id: int
    document_id: int
    file_id: int | None
    source_key: str
    chunk_index: int
    content: str
    token_count: int
    content_hash: str
    metadata: dict[str, object]
    created_at: datetime


class IndexTaskRead(BaseModel):
    task_id: str


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    space_id: int | None = None
    limit: int = Field(default=10, ge=1, le=50)


class SemanticSearchItem(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    file_id: int | None
    source_name: str
    content: str
    score: float


class SemanticSearchResponse(BaseModel):
    query: str
    model: str
    items: list[SemanticSearchItem]
