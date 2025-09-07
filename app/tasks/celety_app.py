from celery import Celery
from app.core.config import settings

celery = Celery("filesvc")

celery.conf.update(
    broker_url=settings.REDIS_BROKER,
    result_backend=settings.REDIS_BACKEND,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
