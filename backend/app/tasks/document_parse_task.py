import asyncio
from datetime import UTC, datetime

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.knowledge_models import DocumentFile, FileParseStatus
from app.services.document_parser import UnsupportedDocumentTypeError, parse_document
from app.services.storage import get_storage
from app.tasks.celery_app import celery_app


async def update_file(file_id: int, **values: object) -> DocumentFile | None:
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with session_factory() as session:
            record = await session.get(DocumentFile, file_id)
            if not record:
                return None
            for key, value in values.items():
                setattr(record, key, value)
            await session.commit()
            return record
    finally:
        await engine.dispose()


async def load_file(file_id: int) -> DocumentFile | None:
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with session_factory() as session:
            return await session.get(DocumentFile, file_id)
    finally:
        await engine.dispose()


@celery_app.task(
    bind=True,
    name="documents.parse",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 2},
)
def parse_document_file(self: Task, file_id: int) -> dict[str, object]:
    now = datetime.now(UTC)
    asyncio.run(
        update_file(
            file_id,
            parse_status=FileParseStatus.PROCESSING,
            parse_task_id=self.request.id,
            parse_error=None,
            parse_started_at=now,
            parse_completed_at=None,
        )
    )
    record = asyncio.run(load_file(file_id))
    if not record:
        return {"file_id": file_id, "status": "missing"}

    try:
        content = get_storage().download(record.object_name)
        parsed_text = parse_document(record.file_name, record.mime_type, content)
    except UnsupportedDocumentTypeError as exc:
        asyncio.run(
            update_file(
                file_id,
                parse_status=FileParseStatus.UNSUPPORTED,
                parse_error=str(exc),
                parse_completed_at=datetime.now(UTC),
            )
        )
        return {"file_id": file_id, "status": FileParseStatus.UNSUPPORTED.value}
    except Exception as exc:
        asyncio.run(
            update_file(
                file_id,
                parse_status=FileParseStatus.FAILED,
                parse_error=str(exc)[:2000],
                parse_completed_at=datetime.now(UTC),
            )
        )
        raise

    asyncio.run(
        update_file(
            file_id,
            parse_status=FileParseStatus.COMPLETED,
            parsed_text=parsed_text,
            parse_error=None,
            parse_completed_at=datetime.now(UTC),
        )
    )
    return {
        "file_id": file_id,
        "status": FileParseStatus.COMPLETED.value,
        "text_length": len(parsed_text),
    }


def enqueue_document_parse(file_id: int) -> str:
    result = parse_document_file.delay(file_id)
    return str(result.id)
