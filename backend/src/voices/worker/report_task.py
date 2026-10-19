"""Runs one comparison as a worker job (atlas plates 40 and 70), announcing it live on the
run's own stream and keeping its result for the page."""

import logging
from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from functools import lru_cache, partial

import redis
from sqlalchemy import Engine

from voices.config import load_settings
from voices.db.explore_store import ExploreStore
from voices.db.store import connect_store
from voices.db.tagging_store import TaggingStore
from voices.events import RedisEvents
from voices.explore.day_range import DayRange
from voices.ingestion.embedder import NomicEmbedder, load_embedder
from voices.log import log_event, tracing
from voices.report.comparison_run import ComparisonRun, RunParts, Version, VersionResult
from voices.report.runs import RunStore, stream_of
from voices.tagging.model import connect_model

logger = logging.getLogger(__name__)


class RunData(ExploreStore, TaggingStore):
    """The reads a run needs: the Explore page's topic reads, and the agents' search, lookup
    and retrieval counting. Both stores are built on the same engine."""


def compare_now(run_id: str, start: date, end: date) -> None:
    """Runs the comparison; on any failure the run is marked failed with the reason, which the
    page shows, and the error is raised for the worker's log."""
    client = redis.Redis.from_url(load_settings().redis_url)
    runs = RunStore(client)
    emit = partial(RedisEvents(client).emit, stream_of(run_id))
    with tracing(f"run-{run_id}"):
        try:
            result = ComparisonRun(_parts(), emit, in_parallel).run(run_id, DayRange(start, end))
        except Exception as error:
            log_event(logger, "run.failed", run_id=run_id, reason=str(error))
            emit("run.failed", reason=str(error))
            runs.mark_failed(run_id, str(error))
            raise
        runs.mark_finished(run_id, result)


def in_parallel(
    work: Callable[[Version], VersionResult], versions: Iterable[Version]
) -> Iterator[VersionResult]:
    """Both versions at once: each spends most of its time waiting for the model."""
    with ThreadPoolExecutor(max_workers=2) as pool:
        return iter(list(pool.map(work, versions)))


def _parts() -> RunParts:
    settings = load_settings()
    model = connect_model(settings.openrouter_api_key, settings.report_model_name)
    return RunParts(model, settings.report_model_name, RunData(_engine()), _embedder())


@lru_cache(maxsize=1)
def _engine() -> Engine:
    return connect_store(load_settings().database_url).engine


@lru_cache(maxsize=1)
def _embedder() -> NomicEmbedder:
    """Loaded once per worker process; loading the model takes a while."""
    return load_embedder(load_settings().model_dir)
