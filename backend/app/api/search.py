from time import perf_counter

from fastapi import APIRouter, Depends, Response
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import selectinload
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import DB, CurrentUser, require_permission
from app.api.knowledge import ensure_document_access, get_document
from app.common.exceptions import AppError
from app.core.config import settings
from app.knowledge_models import (
    Document,
    KnowledgeChunk,
    KnowledgeEmbedding,
    Tag,
)
from app.search_schemas import (
    ChunkRead,
    HybridSearchItem,
    HybridSearchRequest,
    HybridSearchResponse,
    IndexTaskRead,
    SearchMode,
    SearchScore,
    SemanticSearchItem,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SourceType,
)
from app.services.embedding import EmbeddingServiceError, get_embedding_service
from app.services.search_ranking import fuse_and_rerank, lexical_relevance
from app.services.text_processing import normalize_text, tokenize_text
from app.tasks.document_index_task import enqueue_document_index

router = APIRouter(tags=["Search"])


def search_filters(payload: HybridSearchRequest) -> list:
    filters = [
        Document.id == KnowledgeChunk.document_id,
        Document.is_deleted.is_(False),
    ]
    if payload.space_id is not None:
        filters.append(Document.space_id == payload.space_id)
    if payload.category_id is not None:
        filters.append(Document.category_id == payload.category_id)
    if payload.status is not None:
        filters.append(Document.status == payload.status)
    if payload.tag_ids:
        filters.append(Document.tags.any(Tag.id.in_(payload.tag_ids)))
    if payload.source_type == SourceType.DOCUMENT:
        filters.append(KnowledgeChunk.file_id.is_(None))
    elif payload.source_type == SourceType.FILE:
        filters.append(KnowledgeChunk.file_id.is_not(None))
    if payload.updated_from is not None:
        filters.append(Document.updated_at >= payload.updated_from)
    if payload.updated_to is not None:
        filters.append(Document.updated_at <= payload.updated_to)
    return filters


def chunk_read(chunk: KnowledgeChunk) -> ChunkRead:
    return ChunkRead(
        id=chunk.id,
        document_id=chunk.document_id,
        file_id=chunk.file_id,
        source_key=chunk.source_key,
        chunk_index=chunk.chunk_index,
        content=chunk.content,
        token_count=chunk.token_count,
        content_hash=chunk.content_hash,
        metadata=chunk.chunk_metadata,
        created_at=chunk.created_at,
    )


@router.get("/documents/{document_id}/chunks", response_model=list[ChunkRead])
async def list_document_chunks(
    document_id: int, db: DB, user: CurrentUser
) -> list[ChunkRead]:
    document = await get_document(db, document_id)
    await ensure_document_access(db, user, document, "view")
    chunks = list(
        (
            await db.execute(
                select(KnowledgeChunk)
                .where(KnowledgeChunk.document_id == document_id)
                .order_by(KnowledgeChunk.source_key, KnowledgeChunk.chunk_index)
            )
        ).scalars()
    )
    return [chunk_read(chunk) for chunk in chunks]


@router.post(
    "/documents/{document_id}/chunks/rebuild",
    response_model=IndexTaskRead,
    dependencies=[Depends(require_permission("document.edit"))],
)
async def rebuild_document_chunks(
    document_id: int, db: DB, user: CurrentUser
) -> IndexTaskRead:
    document = await get_document(db, document_id)
    await ensure_document_access(db, user, document, "edit")
    task_id = await run_in_threadpool(enqueue_document_index, document_id)
    return IndexTaskRead(task_id=task_id)


@router.delete(
    "/chunks/{chunk_id}",
    status_code=204,
    dependencies=[Depends(require_permission("document.edit"))],
)
async def delete_chunk(chunk_id: int, db: DB, user: CurrentUser) -> Response:
    chunk = await db.get(KnowledgeChunk, chunk_id)
    if not chunk:
        raise AppError("chunk_not_found", "Knowledge chunk does not exist", 404)
    document = await get_document(db, chunk.document_id)
    await ensure_document_access(db, user, document, "edit")
    await db.execute(delete(KnowledgeChunk).where(KnowledgeChunk.id == chunk_id))
    await db.commit()
    return Response(status_code=204)


@router.post("/search/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    payload: SemanticSearchRequest, db: DB, user: CurrentUser
) -> SemanticSearchResponse:
    try:
        query_vector = await run_in_threadpool(
            get_embedding_service().embed, [payload.query]
        )
    except EmbeddingServiceError as exc:
        raise AppError("embedding_unavailable", str(exc), 503) from exc

    distance = KnowledgeEmbedding.embedding.cosine_distance(query_vector[0]).label(
        "distance"
    )
    filters = [
        Document.id == KnowledgeChunk.document_id,
        Document.is_deleted.is_(False),
        KnowledgeEmbedding.model_name == settings.embedding_model,
    ]
    if payload.space_id is not None:
        filters.append(Document.space_id == payload.space_id)
    candidates = (
        await db.execute(
            select(KnowledgeChunk, Document, distance)
            .join(
                KnowledgeEmbedding,
                KnowledgeEmbedding.chunk_id == KnowledgeChunk.id,
            )
            .join(Document, Document.id == KnowledgeChunk.document_id)
            .where(*filters)
            .order_by(distance)
            .limit(min(payload.limit * 10, 200))
        )
    ).all()

    items: list[SemanticSearchItem] = []
    for chunk, document, candidate_distance in candidates:
        try:
            await ensure_document_access(db, user, document, "view")
        except AppError:
            continue
        metadata = chunk.chunk_metadata or {}
        items.append(
            SemanticSearchItem(
                chunk_id=chunk.id,
                document_id=document.id,
                document_title=document.title,
                file_id=chunk.file_id,
                source_name=str(metadata.get("source_name", document.title)),
                content=chunk.content,
                score=max(0.0, min(1.0, 1.0 - float(candidate_distance))),
            )
        )
        if len(items) >= payload.limit:
            break

    return SemanticSearchResponse(
        query=payload.query,
        model=settings.embedding_model,
        items=items,
    )


@router.post("/search/hybrid", response_model=HybridSearchResponse)
async def hybrid_search(
    payload: HybridSearchRequest, db: DB, user: CurrentUser
) -> HybridSearchResponse:
    started_at = perf_counter()
    filters = search_filters(payload)
    candidate_limit = min(max(payload.limit * 12, 60), 300)
    candidates: dict[int, dict[str, object]] = {}

    if payload.mode in (SearchMode.HYBRID, SearchMode.SEMANTIC):
        try:
            query_vector = await run_in_threadpool(
                get_embedding_service().embed, [payload.query]
            )
        except EmbeddingServiceError as exc:
            raise AppError("embedding_unavailable", str(exc), 503) from exc
        distance = KnowledgeEmbedding.embedding.cosine_distance(query_vector[0]).label(
            "distance"
        )
        semantic_rows = (
            await db.execute(
                select(KnowledgeChunk, Document, distance)
                .join(
                    KnowledgeEmbedding,
                    KnowledgeEmbedding.chunk_id == KnowledgeChunk.id,
                )
                .join(Document, Document.id == KnowledgeChunk.document_id)
                .where(
                    *filters,
                    KnowledgeEmbedding.model_name == settings.embedding_model,
                )
                .options(selectinload(Document.tags))
                .order_by(distance)
                .limit(candidate_limit)
            )
        ).all()
        for chunk, document, candidate_distance in semantic_rows:
            candidates[chunk.id] = {
                "chunk": chunk,
                "document": document,
                "semantic": max(0.0, min(1.0, 1.0 - float(candidate_distance))),
            }

    if payload.mode in (SearchMode.HYBRID, SearchMode.LEXICAL):
        normalized_query = normalize_text(payload.query)
        query_tokens = [
            token
            for token in dict.fromkeys(tokenize_text(normalized_query))
            if len(token) > 1
        ][:12]
        lexical_terms = [normalized_query, *query_tokens]
        lexical_conditions = []
        for term in lexical_terms:
            pattern = f"%{term}%"
            lexical_conditions.extend(
                (
                    Document.title.ilike(pattern),
                    Document.content.ilike(pattern),
                    KnowledgeChunk.content.ilike(pattern),
                )
            )
        lexical_rows = (
            await db.execute(
                select(KnowledgeChunk, Document)
                .join(Document, Document.id == KnowledgeChunk.document_id)
                .where(*filters, or_(*lexical_conditions))
                .options(selectinload(Document.tags))
                .order_by(Document.updated_at.desc())
                .limit(candidate_limit)
            )
        ).all()
        for chunk, document in lexical_rows:
            entry = candidates.setdefault(
                chunk.id,
                {"chunk": chunk, "document": document, "semantic": 0.0},
            )
            entry["document"] = document

    ranked: list[tuple[float, HybridSearchItem]] = []
    for entry in candidates.values():
        chunk = entry["chunk"]
        document = entry["document"]
        assert isinstance(chunk, KnowledgeChunk)
        assert isinstance(document, Document)
        try:
            await ensure_document_access(db, user, document, "view")
        except AppError:
            continue

        semantic_score = float(entry["semantic"])
        lexical_score, lexical_reasons = lexical_relevance(
            payload.query, document.title, chunk.content
        )
        if payload.mode == SearchMode.SEMANTIC:
            lexical_score = 0.0
            lexical_reasons = []
            semantic_weight = 1.0
        elif payload.mode == SearchMode.LEXICAL:
            semantic_score = 0.0
            semantic_weight = 0.0
        else:
            semantic_weight = payload.semantic_weight
        score = fuse_and_rerank(
            semantic_score=semantic_score,
            lexical_score=lexical_score,
            semantic_weight=semantic_weight,
            lexical_reasons=lexical_reasons,
            is_document_source=chunk.file_id is None,
        )
        if score.rerank <= 0:
            continue
        metadata = chunk.chunk_metadata or {}
        item = HybridSearchItem(
            chunk_id=chunk.id,
            document_id=document.id,
            document_title=document.title,
            space_id=document.space_id,
            category_id=document.category_id,
            status=document.status,
            tag_ids=[tag.id for tag in document.tags],
            tag_names=[tag.name for tag in document.tags],
            file_id=chunk.file_id,
            source_name=str(metadata.get("source_name", document.title)),
            source_type=(
                SourceType.FILE if chunk.file_id is not None else SourceType.DOCUMENT
            ),
            content=chunk.content,
            updated_at=document.updated_at,
            score=SearchScore(
                semantic=round(semantic_score, 6),
                lexical=score.lexical,
                fused=score.fused,
                rerank=score.rerank,
            ),
            explanations=list(score.explanations),
        )
        ranked.append((score.rerank, item))

    ranked.sort(key=lambda value: (value[0], value[1].updated_at), reverse=True)
    return HybridSearchResponse(
        query=payload.query,
        mode=payload.mode,
        model=settings.embedding_model,
        total_candidates=len(ranked),
        took_ms=round((perf_counter() - started_at) * 1000),
        items=[item for _, item in ranked[: payload.limit]],
    )
