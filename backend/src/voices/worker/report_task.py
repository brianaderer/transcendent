"""Runs one comparison as a worker job (atlas plates 40 and 70), announcing it live on the
run's own stream and keeping its result for the page."""

import logging
from dataclasses import dataclass
from datetime import date
from functools import lru_cache, partial
from typing import Protocol

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
from voices.report.comparison_run import ComparisonRun, RunParts, RunResult
from voices.report.runs import RunStore, stream_of
from voices.report.writer import Emit
from voices.tagging.model import connect_model

logger = logging.getLogger(__name__)


class RunData(ExploreStore, TaggingStore):
    """The reads a run needs: the Explore page's topic reads, and the agents' search, lookup
    and retrieval counting. Both stores are built on the same engine."""


@dataclass(frozen=True)
class RunJob:
    """Which run this is and the range it reports on."""

    run_id: str
    days: DayRange


@dataclass(frozen=True)
class RunRecord:
    """Where a run's outcome goes: its state in the run store, and its own live stream."""

    runs: RunStore
    emit: Emit


class Comparison(Protocol):
    def run(self, run_id: str, days: DayRange) -> RunResult: ...


def compare_now(run_id: str, start: date, end: date) -> None:
    """Runs the comparison for the range and keeps its outcome for the page."""
    client = redis.Redis.from_url(load_settings().redis_url)
    emit = partial(RedisEvents(client).emit, stream_of(run_id))
    with tracing(f"run-{run_id}"):
        run_and_keep_result(
            ComparisonRun(_parts(), emit),
            RunRecord(RunStore(client), emit),
            RunJob(run_id, DayRange(start, end)),
        )


def run_and_keep_result(comparison: Comparison, record: RunRecord, job: RunJob) -> None:
    """Marks the run finished with its result, then announces `run.finished`, so the page,
    once told, can read the result at once. On any failure logs `run.failed`, marks the run
    failed with the reason, which the page shows, then announces it the same way, and raises
    for the worker's log."""
    try:
        result = comparison.run(job.run_id, job.days)
    except Exception as error:
        _record_failure(record, job.run_id, str(error))
        raise
    record.runs.mark_finished(job.run_id, result)
    record.emit("run.finished")


def _record_failure(record: RunRecord, run_id: str, reason: str) -> None:
    log_event(logger, "run.failed", run_id=run_id, reason=reason)
    record.runs.mark_failed(run_id, reason)
    record.emit("run.failed", reason=reason)


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
