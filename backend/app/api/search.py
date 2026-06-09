from fastapi import APIRouter, Depends, Response
from sqlalchemy import delete, select
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import DB, CurrentUser, require_permission
from app.api.knowledge import ensure_document_access, get_document
from app.common.exceptions import AppError
from app.core.config import settings
from app.knowledge_models import (
    Document,
    KnowledgeChunk,
    KnowledgeEmbedding,
)
from app.search_schemas import (
    ChunkRead,
    IndexTaskRead,
    SemanticSearchItem,
    SemanticSearchRequest,
    SemanticSearchResponse,
)
from app.services.embedding import EmbeddingServiceError, get_embedding_service
from app.tasks.document_index_task import enqueue_document_index

router = APIRouter(tags=["Search"])


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
