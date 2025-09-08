# app/tasks/celery_app.py
from __future__ import annotations

from celery import Celery
from app.core.config import settings

celery = Celery("filesvc")

celery.conf.update(
    broker_url=settings.REDIS_BROKER,        # напр. redis://redis:6379/0
    result_backend=settings.REDIS_BACKEND,   # напр. redis://redis:6379/1
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=getattr(settings, "CELERY_TIMEZONE", "UTC"),
    enable_utc=True,
)

# 1) автопоиск задач в пакете app.tasks
celery.autodiscover_tasks(["app.tasks"])

# (опционально) роутинг задач по очередям
# celery.conf.task_routes = {
#     "extract_metadata_task": {"queue": "default"},
# }
