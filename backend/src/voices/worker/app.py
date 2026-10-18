"""The Celery worker and its Beat schedule. Ingestion jobs arrive in build step 2."""

from celery import Celery
from celery.signals import setup_logging

from voices.config import load_settings
from voices.log import configure_logging

settings = load_settings()
celery_app = Celery("voices", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(timezone="UTC", beat_schedule={})


@setup_logging.connect
def use_json_logging(**_: object) -> None:
    configure_logging("worker", settings.log_dir)


@celery_app.task(name="voices.ping")
def ping() -> str:
    """Answer, so a check can prove the worker is consuming jobs."""
    return "pong"
