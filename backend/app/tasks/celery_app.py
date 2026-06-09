from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "knowsphere",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
    include=["app.tasks.document_parse_task"],
)
celery_app.conf.update(
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.document_parse_timeout_seconds,
)
