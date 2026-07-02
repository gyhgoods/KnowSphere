import json
from dataclasses import dataclass
from typing import Protocol

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.api.knowledge import ensure_document_access
from app.common.exceptions import AppError
from app.core.config import settings
from app.knowledge_models import Document, KnowledgeChunk, KnowledgeEmbedding
from app.models import User
from app.services.embedding import EmbeddingServiceError, get_embedding_service


@dataclass(frozen=True, slots=True)
class RAGContext:
    chunk_id: int
    document_id: int
    document_title: str
    source_name: str
    content: str
    score: float
    source_type: str = "text"
    image_object_name: str | None = None
    image_name: str | None = None
    image_mime_type: str | None = None
    image_document_title: str | None = None


@dataclass(frozen=True, slots=True)
class RAGAnswer:
    answer: str
    confidence: float
    model: str
    contexts: list[RAGContext]


class RAGProviderError(RuntimeError):
    pass


class RAGProvider(Protocol):
    model_name: str

    def answer(self, question: str, contexts: list[RAGContext]) -> RAGAnswer: ...


class OpenAIRAGProvider:
    def __init__(
        self,
        *,
        api_key: str | None = settings.openai_api_key,
        base_url: str = settings.openai_base_url,
        model_name: str = settings.openai_model,
        timeout_seconds: int = settings.openai_timeout_seconds,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    def answer(self, question: str, contexts: list[RAGContext]) -> RAGAnswer:
        if not self.api_key:
            raise RAGProviderError("OPENAI_API_KEY is not configured")

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role":"user",
                    "content":self._build_prompt(question, contexts)
                 }
            ]
        }
        try:
            response = httpx.post(
                f"{self.base_url}",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RAGProviderError(f"OpenAI request failed: {exc}") from exc

        data = response.json()
        answer = self._extract_output_text(data)
        if not answer:
            raise RAGProviderError("OpenAI returned an empty response")
        confidence = self._confidence(contexts)
        return RAGAnswer(
            answer=answer,
            confidence=confidence,
            model=self.model_name,
            contexts=contexts,
        )

    def stream_answer(self, question: str, contexts: list[RAGContext]):
        if not self.api_key:
            raise RAGProviderError("OPENAI_API_KEY is not configured")

        payload = {
            "model": self.model_name,
            "stream": True,
            "messages": [
                {
                    "role": "user",
                    "content": self._build_prompt(question, contexts),
                }
            ],
        }
        try:
            with httpx.stream(
                "POST",
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout_seconds,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        line = line[5:].strip()
                    if line == "[DONE]":
                        break
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    delta = self._extract_stream_delta(data)
                    if delta:
                        yield delta
        except httpx.HTTPError as exc:
            raise RAGProviderError(f"OpenAI request failed: {exc}") from exc

    def _build_prompt(self, question: str, contexts: list[RAGContext]) -> str:
        if not contexts:
            return (
                "You are KnowSphere's enterprise AI assistant. No authorized "
                "knowledge-base vector context was found for this question. "
                "Answer directly from general knowledge, be concise, and do not "
                "invent file citations.\n\n"
                f"User question:\n{question}"
            )

        context_blocks = "\n\n".join(
            (
                f"[{index}] Title: {context.document_title}\n"
                f"Source: {context.source_name}\n"
                f"Similarity: {context.score:.3f}\n"
                f"Content:\n{context.content}"
            )
            for index, context in enumerate(contexts, start=1)
        )
        return (
            "You are KnowSphere's enterprise RAG assistant. Use the authorized "
            "context snippets below as the primary source. Integrate the top "
            "matching snippets into a clear answer. Cite facts from the snippets "
            "only with the exact bracketed references listed below, like [1] or [2]. "
            "Do not cite a reference number that is not present in the context list. "
            "If a context is an extracted image, mention that the related image is "
            "available below the answer. If the snippets do "
            "not fully answer the question, say what is missing before adding any "
            "general knowledge.\n\n"
            f"User question:\n{question}\n\n"
            f"Authorized context snippets:\n{context_blocks}"
        )

    def _extract_output_text(self, data: dict[str, object]) -> str:
        choices = data.get("choices")
        if isinstance(choices, list):
            parts: list[str] = []
            for choice in choices:
                if not isinstance(choice, dict):
                    continue
                message = choice.get("message")
                if isinstance(message, dict) and isinstance(message.get("content"), str):
                    parts.append(message["content"])
                    continue
                delta = choice.get("delta")
                if isinstance(delta, dict) and isinstance(delta.get("content"), str):
                    parts.append(delta["content"])
                    continue
                text = choice.get("text")
                if isinstance(text, str):
                    parts.append(text)
            if parts:
                return "\n".join(parts).strip()

        output_text = data.get("output_text")
        if isinstance(output_text, str):
            return output_text.strip()
        parts: list[str] = []
        output = data.get("output")
        if isinstance(output, list):
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if isinstance(block, dict) and isinstance(block.get("text"), str):
                        parts.append(block["text"])
        return "\n".join(parts).strip()

    def _extract_stream_delta(self, data: dict[str, object]) -> str:
        choices = data.get("choices")
        if isinstance(choices, list):
            parts: list[str] = []
            for choice in choices:
                if not isinstance(choice, dict):
                    continue
                delta = choice.get("delta")
                if isinstance(delta, dict) and isinstance(delta.get("content"), str):
                    parts.append(delta["content"])
                    continue
                message = choice.get("message")
                if isinstance(message, dict) and isinstance(message.get("content"), str):
                    parts.append(message["content"])
                    continue
                text = choice.get("text")
                if isinstance(text, str):
                    parts.append(text)
            return "".join(parts)
        return self._extract_output_text(data)

    def _confidence(self, contexts: list[RAGContext]) -> float:
        if not contexts:
            return 0.0
        return round(sum(context.score for context in contexts) / len(contexts), 3)


def get_rag_provider() -> RAGProvider:
    if settings.rag_provider != "openai":
        raise RAGProviderError(f"Unsupported RAG provider: {settings.rag_provider}")
    return OpenAIRAGProvider()


IMAGE_QUERY_TERMS = (
    "image",
    "picture",
    "screenshot",
    "diagram",
    "chart",
    "photo",
    "图片",
    "图像",
    "截图",
    "图表",
    "照片",
)


def is_image_question(question: str) -> bool:
    lowered = question.lower()
    return any(term in lowered for term in IMAGE_QUERY_TERMS)


def coalesce_contexts(contexts: list[RAGContext]) -> list[RAGContext]:
    grouped: dict[tuple[int, str], RAGContext] = {}
    for context in contexts:
        key = (context.document_id, context.image_object_name or context.source_name)
        existing = grouped.get(key)
        if not existing:
            grouped[key] = context
            continue
        merged_content = f"{existing.content}\n\n{context.content}"
        grouped[key] = RAGContext(
            chunk_id=existing.chunk_id,
            document_id=existing.document_id,
            document_title=existing.document_title,
            source_name=existing.source_name,
            content=merged_content[:2400],
            score=max(existing.score, context.score),
            source_type=existing.source_type,
            image_object_name=existing.image_object_name,
            image_name=existing.image_name,
            image_mime_type=existing.image_mime_type,
            image_document_title=existing.image_document_title,
        )
    return list(grouped.values())[:3]


async def retrieve_contexts(
    db: AsyncSession,
    user: User,
    question: str,
    *,
    space_id: int | None = None,
    limit: int | None = None,
) -> list[RAGContext]:
    try:
        query_vector = await run_in_threadpool(get_embedding_service().embed, [question])
    except EmbeddingServiceError:
        return []

    if not query_vector:
        return []

    requested_limit = min(limit or settings.rag_context_limit, 3)
    image_question = is_image_question(question)
    distance = KnowledgeEmbedding.embedding.cosine_distance(query_vector[0]).label("distance")
    filters = [
        Document.id == KnowledgeChunk.document_id,
        Document.is_deleted.is_(False),
        KnowledgeEmbedding.model_name == settings.embedding_model,
    ]
    if space_id is not None:
        filters.append(Document.space_id == space_id)

    rows = (
        await db.execute(
            select(KnowledgeChunk, Document, distance)
            .join(KnowledgeEmbedding, KnowledgeEmbedding.chunk_id == KnowledgeChunk.id)
            .join(Document, Document.id == KnowledgeChunk.document_id)
            .where(*filters)
            .order_by(distance)
            .limit(60)
        )
    ).all()

    contexts: list[RAGContext] = []
    for chunk, document, candidate_distance in rows:
        try:
            await ensure_document_access(db, user, document, "view")
        except AppError:
            continue

        similarity = max(0.0, min(1.0, 1.0 - float(candidate_distance)))
        if similarity < settings.rag_min_similarity:
            continue

        metadata = chunk.chunk_metadata or {}
        source_type = str(metadata.get("source_type", "text"))
        if image_question and source_type == "image":
            similarity = min(1.0, similarity + 0.25)
        contexts.append(
            RAGContext(
                chunk_id=chunk.id,
                document_id=document.id,
                document_title=document.title,
                source_name=str(metadata.get("source_name", document.title)),
                content=chunk.content,
                score=round(similarity, 4),
                source_type=source_type,
                image_object_name=(
                    str(metadata["image_object_name"])
                    if metadata.get("image_object_name")
                    else None
                ),
                image_name=str(metadata["image_name"]) if metadata.get("image_name") else None,
                image_mime_type=(
                    str(metadata["image_mime_type"])
                    if metadata.get("image_mime_type")
                    else None
                ),
                image_document_title=(
                    str(metadata["image_document_title"])
                    if metadata.get("image_document_title")
                    else None
                ),
            )
        )

    contexts.sort(key=lambda item: item.score, reverse=True)
    return contexts[:requested_limit]
