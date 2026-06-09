import asyncio
import hashlib

from celery import Task
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.knowledge_models import (
    Document,
    DocumentFile,
    KnowledgeChunk,
    KnowledgeEmbedding,
)
from app.services.embedding import get_embedding_service
from app.services.text_processing import split_text
from app.tasks.celery_app import celery_app


async def index_document_source(document_id: int, file_id: int | None = None) -> int:
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with session_factory() as session:
            document = await session.get(Document, document_id)
            if not document or document.is_deleted:
                return 0

            if file_id is None:
                source_key = "document"
                source_name = document.title
                text = f"{document.title}\n\n{document.content}"
            else:
                file = await session.get(DocumentFile, file_id)
                if not file or file.document_id != document_id or not file.parsed_text:
                    return 0
                source_key = f"file:{file.id}"
                source_name = file.file_name
                text = file.parsed_text

            await session.execute(
                delete(KnowledgeChunk).where(
                    KnowledgeChunk.document_id == document_id,
                    KnowledgeChunk.source_key == source_key,
                )
            )
            chunks = split_text(
                text,
                chunk_size=settings.document_chunk_size,
                chunk_overlap=settings.document_chunk_overlap,
            )
            if not chunks:
                await session.commit()
                return 0

            records = [
                KnowledgeChunk(
                    document_id=document_id,
                    file_id=file_id,
                    source_key=source_key,
                    chunk_index=chunk.index,
                    content=chunk.content,
                    token_count=chunk.token_count,
                    content_hash=hashlib.sha256(chunk.content.encode("utf-8")).hexdigest(),
                    chunk_metadata={
                        "source_name": source_name,
                        "start_offset": chunk.start_offset,
                        "end_offset": chunk.end_offset,
                    },
                )
                for chunk in chunks
            ]
            session.add_all(records)
            await session.flush()

            vectors = get_embedding_service().embed([record.content for record in records])
            session.add_all(
                KnowledgeEmbedding(
                    chunk_id=record.id,
                    embedding=vector,
                    model_name=settings.embedding_model,
                )
                for record, vector in zip(records, vectors, strict=True)
            )
            await session.commit()
            return len(records)
    finally:
        await engine.dispose()


@celery_app.task(
    bind=True,
    name="documents.index",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 2},
)
def index_document(
    self: Task, document_id: int, file_id: int | None = None
) -> dict[str, object]:
    chunk_count = asyncio.run(index_document_source(document_id, file_id))
    return {
        "task_id": self.request.id,
        "document_id": document_id,
        "file_id": file_id,
        "chunk_count": chunk_count,
    }


def enqueue_document_index(document_id: int, file_id: int | None = None) -> str:
    result = index_document.delay(document_id, file_id)
    return str(result.id)
