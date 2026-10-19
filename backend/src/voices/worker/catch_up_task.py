"""Runs the catch-up as a worker job, at most one at a time (atlas plate 40).

Beat, a starting worker, or someone queuing `voices.catch_up` by hand can all ask for a
catch-up; a lock makes the second request do nothing while one is running, so two runs
never fetch the same days.
"""

import logging
from collections.abc import Callable
from datetime import UTC, date, datetime
from functools import lru_cache, partial
from typing import Protocol

import redis

from voices.backfill.backfill import Backfill
from voices.backfill.progress import RedisBackfillProgress
from voices.config import load_settings
from voices.db.backfill_store import BackfillStore
from voices.db.store import connect_store
from voices.db.tagging_store import TaggingStore
from voices.events import RedisEvents
from voices.explore.cache import RedisMapCache
from voices.ingestion.agreement import AgreementDetector
from voices.ingestion.arctic_shift import connect_to_archive
from voices.ingestion.catch_up import CatchUp
from voices.ingestion.day import DayIngestion
from voices.ingestion.embedder import load_embedder
from voices.log import log_event, tracing
from voices.tagging.agent import TaggingAgent
from voices.tagging.day_tagging import DayTagging

CATCH_UP_LOCK = "lock:catch-up"
LOCK_SECONDS = 12 * 60 * 60  # longer than any first start; freed sooner when the run ends
INGESTION_STREAM = "ingestion"

logger = logging.getLogger(__name__)


class Lock(Protocol):
    def acquire(self, blocking: bool) -> bool: ...
    def release(self) -> None: ...


class KeyDeleter(Protocol):
    def delete(self, key: str) -> object: ...


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


def forget_stale_catch_up(redis_client: KeyDeleter) -> None:
    """A worker that is just starting can't have a catch-up in progress, so a lock still held
    belongs to a run that died with its worker (out of memory, say). Clearing it lets the
    next catch-up start now instead of when the lock expires.

    This holds while there is exactly one worker container. With several, a starting worker
    could clear the lock of a catch-up another worker is running."""
    redis_client.delete(CATCH_UP_LOCK)
    log_event(logger, "catch_up.stale_lock_cleared")


def catch_up_now() -> bool:
    settings = load_settings()
    lock = redis.Redis.from_url(settings.redis_url).lock(CATCH_UP_LOCK, timeout=LOCK_SECONDS)
    run = _catch_up_runner()
    return catch_up_once(lock, lambda: run(datetime.now(UTC)))


class Runs(Protocol):
    def run(self, *args: object) -> None: ...


def backfill_then_catch_up(backfill: Runs, catch_up: Runs, now: datetime) -> None:
    """The vectors the boot seed left behind come back before any day is tagged, so tagging
    never meets a store without them (atlas plate 07). Both run under the catch-up's lock."""
    with tracing("backfill"):
        backfill.run()
    catch_up.run(now)


@lru_cache(maxsize=1)
def _catch_up_runner() -> Callable[[datetime], None]:
    """Built once per worker process: loading the embedding model takes a while. Any missing
    vectors are backfilled first; then each day is loaded, then tagged, and a day is done
    only when both have happened."""
    settings = load_settings()
    store = connect_store(settings.database_url)
    embedder = load_embedder(settings.model_dir)
    ingestion = DayIngestion(connect_to_archive(), embedder, AgreementDetector(embedder), store)
    redis_client = redis.Redis.from_url(settings.redis_url)
    emit = partial(RedisEvents(redis_client).emit, INGESTION_STREAM)
    tagging_store = TaggingStore(store.engine)
    agent = TaggingAgent(
        tagging_store,
        embedder,
        api_key=settings.openrouter_api_key,
        model_name=settings.tagging_model_name,
    )
    tagging = DayTagging(tagging_store, embedder, agent.decide, emit)
    backfill = Backfill(
        BackfillStore(store.engine),
        embedder,
        RedisBackfillProgress(redis_client),
        emit,
        RedisMapCache(redis_client).forget_all,
    )
    catch_up = CatchUp(store, partial(_load_and_tag, ingestion, tagging), emit)
    return partial(backfill_then_catch_up, backfill, catch_up)


def _load_and_tag(ingestion: DayIngestion, tagging: DayTagging, day: date) -> dict[str, int]:
    with tracing(f"day-{day.isoformat()}"):
        return {**ingestion.process(day), **tagging.tag(day)}
