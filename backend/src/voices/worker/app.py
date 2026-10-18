"""The Celery worker and its Beat schedule (atlas plate 40)."""

import redis
from celery import Celery
from celery.schedules import crontab
from celery.signals import setup_logging, worker_ready

from voices.config import load_settings
from voices.log import configure_logging
from voices.worker.catch_up_task import catch_up_now, forget_stale_catch_up

settings = load_settings()
celery_app = Celery("voices", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    timezone="UTC",
    broker_connection_retry_on_startup=True,
    beat_schedule={
        "daily-catch-up": {"task": "voices.catch_up", "schedule": crontab(hour=6, minute=0)}
    },
)


@setup_logging.connect
def use_json_logging(**_: object) -> None:
    configure_logging(settings.service_name, settings.log_dir)


@worker_ready.connect
def catch_up_on_start(**_: object) -> None:
    """First start and every restart catch up on whatever days are missing."""
    forget_stale_catch_up(redis.Redis.from_url(settings.redis_url))
    catch_up.delay()


@celery_app.task(name="voices.catch_up")
def catch_up() -> bool:
    """Process every complete day not yet done. Says whether it ran (another may be running)."""
    return catch_up_now()


@celery_app.task(name="voices.ping")
def ping() -> str:
    """Answer, so a check can prove the worker is consuming jobs."""
    return "pong"
