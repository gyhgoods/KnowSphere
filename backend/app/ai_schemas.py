from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.knowledge_models import ConversationStatus, FeedbackRating, MessageRole


class CitationRead(BaseModel):
    index: int
    document_id: int
    document_title: str
    chunk_id: int
    source_name: str
    excerpt: str
    score: float
    source_type: str = "text"
    image_url: str | None = None
    image_name: str | None = None
    image_mime_type: str | None = None
    image_document_title: str | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    conversation_id: int | None = None
    space_id: int | None = None
    limit: int = Field(default=3, ge=1, le=3)


class AskResponse(BaseModel):
    conversation_id: int
    question_message_id: int
    answer_message_id: int
    answer: str
    confidence: float
    model: str
    citations: list[CitationRead]


class ConversationRead(BaseModel):
    id: int
    title: str
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime


class MessageRead(BaseModel):
    id: int
    role: MessageRole
    content: str
    citations: list[dict[str, object]]
    confidence: float | None
    model_name: str | None
    created_at: datetime


class FeedbackRequest(BaseModel):
    rating: FeedbackRating
    comment: str | None = Field(default=None, max_length=1000)


class FeedbackRead(BaseModel):
    id: int
    message_id: int
    rating: FeedbackRating
    comment: str | None
    created_at: datetime


class GraphEntityRead(BaseModel):
    id: int
    name: str
    entity_type: str
    description: str | None


class GraphRelationRead(BaseModel):
    id: int
    source_entity_id: int
    source_name: str
    target_entity_id: int
    target_name: str
    relation_type: str
    document_id: int
    document_title: str
    confidence: float
    evidence: str | None


class GraphResponse(BaseModel):
    entities: list[GraphEntityRead]
    relations: list[GraphRelationRead]


class GraphExtractRequest(BaseModel):
    document_id: int


class GraphExtractResponse(BaseModel):
    document_id: int
    entity_count: int
    relation_count: int


class GraphRelationFilter(StrEnum):
    ALL = "all"
    STRONG = "strong"
