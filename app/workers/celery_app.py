from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "whatsapp_agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Jakarta",
    enable_utc=True,
)
