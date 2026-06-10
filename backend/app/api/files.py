import hashlib
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy import func, select
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import DB, CurrentUser, has_permission
from app.api.knowledge import ensure_document_access, get_document
from app.common.exceptions import AppError
from app.core.config import settings
from app.knowledge_models import DocumentFile, FileParseStatus
from app.knowledge_schemas import FileAccess, FileParseRead, FileRead
from app.services.storage import ObjectStorage, get_storage, safe_file_name
from app.tasks.document_parse_task import enqueue_document_parse

router = APIRouter(prefix="/files", tags=["Files"])
Storage = Annotated[ObjectStorage, Depends(get_storage)]

PREVIEWABLE_MIME_PREFIXES = ("image/", "audio/", "video/", "text/")
PREVIEWABLE_MIME_TYPES = {"application/pdf", "application/json"}


def is_previewable(mime_type: str) -> bool:
    return mime_type in PREVIEWABLE_MIME_TYPES or mime_type.startswith(
        PREVIEWABLE_MIME_PREFIXES
    )


@router.get("/documents/{document_id}", response_model=list[FileRead])
async def list_document_files(document_id: int, db: DB, user: CurrentUser) -> list[DocumentFile]:
    document = await get_document(db, document_id)
    await ensure_document_access(db, user, document, "view")
    return document.files


@router.post(
    "/documents/{document_id}",
    response_model=FileRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document_file(
    document_id: int,
    file: Annotated[UploadFile, File()],
    db: DB,
    user: CurrentUser,
    storage: Storage,
) -> DocumentFile:
    if not has_permission(user, "file.manage"):
        raise AppError("permission_denied", "Permission 'file.manage' is required", 403)
    document = await get_document(db, document_id)
    await ensure_document_access(db, user, document, "edit")

    digest = hashlib.sha256()
    total = 0
    while chunk := await file.read(1024 * 1024):
        total += len(chunk)
        if total > settings.max_upload_size_mb * 1024 * 1024:
            raise AppError(
                "file_too_large",
                f"File exceeds the {settings.max_upload_size_mb} MB limit",
                413,
            )
        digest.update(chunk)
    await file.seek(0)

    file_name = safe_file_name(file.filename or "unnamed-file")
    suffix = Path(file_name).suffix.lower()
    object_name = f"documents/{document_id}/{uuid.uuid4().hex}{suffix}"
    mime_type = file.content_type or "application/octet-stream"
    await run_in_threadpool(storage.upload, object_name, file.file, total, mime_type)

    record = DocumentFile(
        document_id=document_id,
        file_name=file_name,
        object_name=object_name,
        mime_type=mime_type,
        file_size=total,
        checksum=digest.hexdigest(),
        uploaded_by=user.id,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    try:
        record.parse_task_id = await run_in_threadpool(enqueue_document_parse, record.id)
    except Exception as exc:
        record.parse_status = FileParseStatus.FAILED
        record.parse_error = f"Could not enqueue parser task: {exc}"[:2000]
    await db.commit()
    await db.refresh(record)
    return record


async def get_file_with_access(
    file_id: int, db: DB, user: CurrentUser, action: str
) -> DocumentFile:
    record = await db.get(DocumentFile, file_id)
    if not record:
        raise AppError("file_not_found", "File does not exist", 404)
    document = await get_document(db, record.document_id)
    await ensure_document_access(db, user, document, action)
    return record


@router.get("/{file_id}/download", response_model=FileAccess)
async def download_file(
    file_id: int, db: DB, user: CurrentUser, storage: Storage
) -> FileAccess:
    if not has_permission(user, "document.download"):
        raise AppError("permission_denied", "Permission 'document.download' is required", 403)
    record = await get_file_with_access(file_id, db, user, "download")
    url = await run_in_threadpool(storage.presigned_get, record.object_name, 900)
    return FileAccess(url=url, expires_in=900, previewable=is_previewable(record.mime_type))


@router.get("/{file_id}/preview", response_model=FileAccess)
async def preview_file(
    file_id: int, db: DB, user: CurrentUser, storage: Storage
) -> FileAccess:
    record = await get_file_with_access(file_id, db, user, "view")
    if not is_previewable(record.mime_type):
        raise AppError("preview_not_supported", "This file type cannot be previewed", 415)
    url = await run_in_threadpool(storage.presigned_get, record.object_name, 600)
    return FileAccess(url=url, expires_in=600, previewable=True)


@router.get("/{file_id}/parse", response_model=FileParseRead)
async def get_file_parse_result(
    file_id: int, db: DB, user: CurrentUser
) -> DocumentFile:
    return await get_file_with_access(file_id, db, user, "view")


@router.post("/{file_id}/parse", response_model=FileRead)
async def retry_file_parse(
    file_id: int, db: DB, user: CurrentUser
) -> DocumentFile:
    if not has_permission(user, "file.manage"):
        raise AppError("permission_denied", "Permission 'file.manage' is required", 403)
    record = await get_file_with_access(file_id, db, user, "edit")
    record.parse_status = FileParseStatus.QUEUED
    record.parse_error = None
    record.parsed_text = None
    record.parse_started_at = None
    record.parse_completed_at = None
    await db.commit()
    try:
        record.parse_task_id = await run_in_threadpool(enqueue_document_parse, record.id)
    except Exception as exc:
        record.parse_status = FileParseStatus.FAILED
        record.parse_error = f"Could not enqueue parser task: {exc}"[:2000]
    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: int, db: DB, user: CurrentUser, storage: Storage
) -> Response:
    if not has_permission(user, "file.manage"):
        raise AppError("permission_denied", "Permission 'file.manage' is required", 403)
    record = await get_file_with_access(file_id, db, user, "edit")
    lock_key = (record.document_id << 32) | record.id
    await db.execute(select(func.pg_advisory_xact_lock(lock_key)))
    await run_in_threadpool(storage.delete, record.object_name)
    await db.delete(record)
    await db.commit()
    return Response(status_code=204)
