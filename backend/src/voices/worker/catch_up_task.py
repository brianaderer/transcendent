"""Runs the catch-up as a worker job, at most one at a time (atlas plate 40).

Beat, a starting worker, the page's Sync now button (POST /api/catch-up) or someone queuing
`voices.catch_up` by hand can all ask for a catch-up; a lock makes the second request do
nothing while one is running, so two runs never fetch the same days.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from functools import lru_cache, partial
from typing import Protocol

import redis

from voices.backfill.backfill import Backfill
from voices.backfill.progress import RedisBackfillProgress
from voices.config import Settings, load_settings
from voices.db.backfill_store import BackfillStore
from voices.db.store import Store, connect_store
from voices.db.tagging_store import TaggingStore
from voices.events import RedisEvents
from voices.explore.cache import RedisMapCache
from voices.ingestion.agreement import AgreementDetector
from voices.ingestion.arctic_shift import connect_to_archive
from voices.ingestion.catch_up import CatchUp
from voices.ingestion.day import DayIngestion
from voices.ingestion.embedder import NomicEmbedder, load_embedder
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


class Backfills(Protocol):
    def run(self) -> None: ...


class CatchesUp(Protocol):
    def run(self, now: datetime) -> None: ...


def backfill_then_catch_up(backfill: Backfills, catch_up: CatchesUp, now: datetime) -> None:
    """The vectors the boot seed left behind come back before any day is tagged, so tagging
    never meets a store without them (atlas plate 07). Both run under the catch-up's lock."""
    with tracing("backfill"):
        backfill.run()
    catch_up.run(now)


@dataclass(frozen=True)
class _Shared:
    """What the backfill, the loading and the tagging all use."""

    settings: Settings
    store: Store
    embedder: NomicEmbedder
    redis_client: redis.Redis
    emit: Callable[..., None]


@lru_cache(maxsize=1)
def _catch_up_runner() -> Callable[[datetime], None]:
    """Built once per worker process: loading the embedding model takes a while. Any missing
    vectors are backfilled first; then each day is loaded, then tagged, and a day is done
    only when both have happened."""
    shared = _connect_shared()
    load_and_tag = partial(_load_and_tag, _ingestion_for(shared), _tagging_for(shared))
    catch_up = CatchUp(shared.store, load_and_tag, shared.emit)
    return partial(backfill_then_catch_up, _backfill_for(shared), catch_up)


def _connect_shared() -> _Shared:
    settings = load_settings()
    redis_client = redis.Redis.from_url(settings.redis_url)
    return _Shared(
        settings,
        connect_store(settings.database_url),
        load_embedder(settings.model_dir),
        redis_client,
        partial(RedisEvents(redis_client).emit, INGESTION_STREAM),
    )


def _ingestion_for(shared: _Shared) -> DayIngestion:
    embedder = shared.embedder
    agreement = AgreementDetector(embedder)
    return DayIngestion(connect_to_archive(), embedder, agreement, shared.store, shared.emit)


def _tagging_for(shared: _Shared) -> DayTagging:
    tagging_store = TaggingStore(shared.store.engine)
    agent = TaggingAgent(
        tagging_store,
        shared.embedder,
        api_key=shared.settings.openrouter_api_key,
        model_name=shared.settings.tagging_model_name,
    )
    return DayTagging(tagging_store, shared.embedder, agent.decide, shared.emit)


def _backfill_for(shared: _Shared) -> Backfill:
    return Backfill(
        BackfillStore(shared.store.engine),
        shared.embedder,
        RedisBackfillProgress(shared.redis_client),
        shared.emit,
        RedisMapCache(shared.redis_client).forget_all,
    )


def _load_and_tag(ingestion: DayIngestion, tagging: DayTagging, day: date) -> dict[str, int]:
    with tracing(f"day-{day.isoformat()}"):
        return {**ingestion.process(day), **tagging.tag(day)}
