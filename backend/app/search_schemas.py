from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.knowledge_models import DocumentStatus


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


class SearchMode(StrEnum):
    HYBRID = "hybrid"
    SEMANTIC = "semantic"
    LEXICAL = "lexical"


class SourceType(StrEnum):
    ALL = "all"
    DOCUMENT = "document"
    FILE = "file"


class HybridSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    mode: SearchMode = SearchMode.HYBRID
    space_id: int | None = None
    category_id: int | None = None
    status: DocumentStatus | None = None
    tag_ids: list[int] = Field(default_factory=list, max_length=20)
    source_type: SourceType = SourceType.ALL
    updated_from: datetime | None = None
    updated_to: datetime | None = None
    semantic_weight: float = Field(default=0.65, ge=0, le=1)
    limit: int = Field(default=10, ge=1, le=50)


class SearchScore(BaseModel):
    semantic: float
    lexical: float
    fused: float
    rerank: float


class HybridSearchItem(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    space_id: int
    category_id: int | None
    status: DocumentStatus
    tag_ids: list[int]
    tag_names: list[str]
    file_id: int | None
    source_name: str
    source_type: SourceType
    content: str
    updated_at: datetime
    score: SearchScore
    explanations: list[str]


class HybridSearchResponse(BaseModel):
    query: str
    mode: SearchMode
    model: str
    total_candidates: int
    took_ms: int
    items: list[HybridSearchItem]
