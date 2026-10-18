"""Runs the catch-up as a worker job, at most one at a time (atlas plate 40).

Beat, a worker restart and a request can all ask for a catch-up; a lock makes the second
request do nothing while one is running, so two runs never fetch the same days.
"""

import logging
from collections.abc import Callable
from datetime import UTC, date, datetime
from functools import lru_cache, partial
from typing import Protocol

import redis

from voices.config import load_settings
from voices.db.store import connect_store
from voices.events import RedisEvents
from voices.ingestion.agreement import AgreementDetector
from voices.ingestion.arctic_shift import connect_to_archive
from voices.ingestion.catch_up import run_catch_up
from voices.ingestion.day import process_day
from voices.ingestion.embedder import load_embedder
from voices.log import log_event, tracing

CATCH_UP_LOCK = "lock:catch-up"
LOCK_SECONDS = 12 * 60 * 60  # longer than any first start; freed sooner when the run ends

logger = logging.getLogger(__name__)


class Lock(Protocol):
    def acquire(self, blocking: bool) -> bool: ...
    def release(self) -> None: ...


def catch_up_once(lock: Lock, run: Callable[[], None]) -> bool:
    """Run the catch-up unless one is already running. Says whether it ran."""
    if not lock.acquire(blocking=False):
        log_event(logger, "catch_up.already_running")
        return False
    try:
        run()
        return True
    finally:
        lock.release()


def forget_stale_catch_up(queue) -> None:
    """A worker that is just starting can't have a catch-up in progress, so a lock still held
    belongs to a run that died with its worker (out of memory, say). Clearing it lets the
    next catch-up start now instead of when the lock expires."""
    queue.delete(CATCH_UP_LOCK)
    log_event(logger, "catch_up.stale_lock_cleared")


def catch_up_now() -> bool:
    settings = load_settings()
    queue = redis.Redis.from_url(settings.redis_url)
    lock = queue.lock(CATCH_UP_LOCK, timeout=LOCK_SECONDS)
    store, process, emit = _ingestion(settings.redis_url, settings.database_url, settings.model_dir)
    return catch_up_once(lock, lambda: run_catch_up(datetime.now(UTC), store, process, emit))


@lru_cache(maxsize=1)
def _ingestion(redis_url: str, database_url: str, model_dir: str):
    """Built once per worker process: loading the embedding model takes a while."""
    store = connect_store(database_url)
    embedder = load_embedder(model_dir)
    process = partial(
        process_day,
        archive=connect_to_archive(),
        embedder=embedder,
        agreement=AgreementDetector(embedder),
        store=store,
    )
    emit = RedisEvents(redis.Redis.from_url(redis_url)).emit
    return store, partial(_traced_day, process), emit


def _traced_day(process: Callable[[date], dict[str, int]], day: date) -> dict[str, int]:
    with tracing(f"day-{day.isoformat()}"):
        return process(day)
