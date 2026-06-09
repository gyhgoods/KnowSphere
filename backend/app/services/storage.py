from datetime import timedelta
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from minio import Minio
from minio.error import S3Error

from app.core.config import settings


class ObjectStorage:
    def __init__(self) -> None:
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
        self.bucket = settings.minio_bucket

    def ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)

    def upload(self, object_name: str, stream, length: int, content_type: str) -> None:
        self.ensure_bucket()
        self.client.put_object(
            self.bucket,
            object_name,
            stream,
            length=length,
            content_type=content_type,
        )

    def presigned_get(self, object_name: str, expires_seconds: int = 900) -> str:
        self.ensure_bucket()
        return self.client.presigned_get_object(
            self.bucket,
            object_name,
            expires=timedelta(seconds=expires_seconds),
        )

    def delete(self, object_name: str) -> None:
        try:
            self.client.remove_object(self.bucket, object_name)
        except S3Error:
            return

    def delete_many(self, object_names: list[str]) -> None:
        for object_name in object_names:
            self.delete(object_name)

    def download(self, object_name: str) -> bytes:
        response = self.client.get_object(self.bucket, object_name)
        try:
            buffer = BytesIO()
            for chunk in response.stream(1024 * 1024):
                buffer.write(chunk)
            return buffer.getvalue()
        finally:
            response.close()
            response.release_conn()


def safe_file_name(file_name: str) -> str:
    name = Path(file_name).name.replace("\x00", "").strip()
    return name[:255] or "unnamed-file"


@lru_cache
def get_storage() -> ObjectStorage:
    return ObjectStorage()
