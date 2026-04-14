"""Celery worker configuration for ProjeX Suite background tasks."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "projex",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Jakarta",
    enable_utc=True,
    task_track_started=True,
    worker_hijack_root_logger=False,
)


# Task stubs — will be populated as features are built
@celery_app.task(name="projex.health_check")
def health_check() -> dict:
    """Simple health check task."""
    return {"status": "ok", "worker": "projex"}
