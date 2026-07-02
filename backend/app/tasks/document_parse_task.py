import asyncio
import uuid
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app import models  # noqa: F401
from app.core.config import settings
from app.knowledge_models import DocumentFile, FileParseStatus
from app.services.document_parser import UnsupportedDocumentTypeError, parse_document_assets
from app.services.ocr import OCRServiceError, get_ocr_service
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


def image_reference_block(
    *,
    index: int,
    object_name: str,
    image_name: str,
    mime_type: str,
    description: str,
) -> str:
    return (
        f"[[KNOWSPHERE_IMAGE index={index} object={object_name} "
        f"name={image_name} mime={mime_type}]]\n"
        f"Image {index}: {description}\n"
        "[[END_KNOWSPHERE_IMAGE]]"
    )


def image_description(*, base_description: str, ocr_text: str, ocr_error: str | None) -> str:
    parts = [base_description]
    if ocr_text:
        parts.append(f"OCR text recognized by qwen3.5-ocr:\n{ocr_text}")
    elif ocr_error:
        parts.append(f"OCR failed: {ocr_error}")
    else:
        parts.append("OCR text recognized by qwen3.5-ocr: No text was recognized.")
    return "\n".join(parts)


def append_extracted_images_text(record: DocumentFile, parsed_text: str, content: bytes) -> str:
    parsed = parse_document_assets(record.file_name, record.mime_type, content)
    parts = [parsed.text] if parsed.text else []
    storage = get_storage()
    ocr_service = get_ocr_service()
    for image in parsed.images:
        suffix = Path(image.file_name).suffix.lower() or ".bin"
        object_name = (
            f"documents/{record.document_id}/extracted-images/"
            f"{record.id}/{uuid.uuid4().hex}{suffix}"
        )
        storage.upload(
            object_name,
            BytesIO(image.content),
            len(image.content),
            image.mime_type,
        )
        ocr_text = ""
        ocr_error = None
        try:
            ocr_text = ocr_service.recognize(image.content, image.mime_type)
        except OCRServiceError as exc:
            ocr_error = str(exc)
        parts.append(
            image_reference_block(
                index=image.index,
                object_name=object_name,
                image_name=image.file_name,
                mime_type=image.mime_type,
                description=image_description(
                    base_description=image.description,
                    ocr_text=ocr_text,
                    ocr_error=ocr_error,
                ),
            )
        )
    return "\n\n".join(parts) if parts else parsed_text


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
        parsed_text = append_extracted_images_text(record, "", content)
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
    from app.tasks.document_index_task import enqueue_document_index

    enqueue_document_index(record.document_id, record.id)
    return {
        "file_id": file_id,
        "status": FileParseStatus.COMPLETED.value,
        "text_length": len(parsed_text),
    }


def enqueue_document_parse(file_id: int) -> str:
    result = parse_document_file.delay(file_id)
    return str(result.id)
