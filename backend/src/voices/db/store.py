"""Reads and writes for ingestion: the day's posts, threads and upvotes, and the ledger of
which days are done (atlas plates 21 and 40)."""

from collections.abc import Sequence
from datetime import UTC, date, datetime

from sqlalchemy import (
    Connection,
    Delete,
    Engine,
    Select,
    Update,
    create_engine,
    delete,
    func,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import Insert, insert
from sqlalchemy.orm import InstrumentedAttribute

from voices.db.address import sqlalchemy_url
from voices.db.day_ledger import latest_day_with_status
from voices.db.models import (
    DAY_DONE,
    DAY_FAILED,
    DAY_RUNNING,
    Base,
    IngestedDay,
    NoiseThread,
    Post,
    PostUpvotesDaily,
    Thread,
)
from voices.ingestion.day import DayBatch, EmbeddedItem, NewThread


class Store:
    def __init__(self, engine: Engine):
        self.engine = engine

    def known_post_ids(self, ids: Sequence[str]) -> set[str]:
        return self._existing(Post.source_id, ids)

    def known_thread_ids(self, ids: Sequence[str]) -> set[str]:
        return self._existing(Thread.source_id, ids)

    def noise_thread_ids(self, ids: Sequence[str]) -> set[str]:
        """Those of these threads that were deleted as noise (atlas OPEN-31)."""
        return self._existing(NoiseThread.source_id, ids)

    def save_day(self, batch: DayBatch) -> None:
        """Everything the day adds, in one transaction. Saving the same day again changes
        nothing: posts and threads already there are skipped, the day's upvote rows are
        replaced as a whole, and every post they touch, before or after, is recounted."""
        with self.engine.begin() as connection:
            if batch.threads:
                rows = [_thread_row(t, batch.day) for t in batch.threads]
                connection.execute(_insert_new(Thread, rows))
            if batch.posts:
                connection.execute(_insert_new(Post, [_post_row(p) for p in batch.posts]))
            self._replace_days_upvotes(connection, batch)

    def _replace_days_upvotes(self, connection: Connection, batch: DayBatch) -> None:
        cleared = connection.scalars(_clear_daily_upvotes(batch.day)).all()
        if batch.upvotes:
            connection.execute(insert(PostUpvotesDaily).values(_upvote_rows(batch)))
        for post_id in set(cleared) | batch.upvotes.keys():
            connection.execute(_recount_upvotes(post_id))

    def done_days(self) -> set[date]:
        with self.engine.connect() as connection:
            return set(
                connection.scalars(select(IngestedDay.day).where(IngestedDay.status == DAY_DONE))
            )

    def mark_running(self, day: date) -> None:
        self._record_day(day, status=DAY_RUNNING, started_at=_now(), finished_at=None, error=None)

    def mark_done(self, day: date, counts: dict[str, int]) -> None:
        self._record_day(day, status=DAY_DONE, counts=counts, finished_at=_now())

    def mark_failed(self, day: date, error: str) -> None:
        self._record_day(day, status=DAY_FAILED, error=error, finished_at=_now())

    def ingestion_status(self) -> dict:
        """Days done, posts stored (comments included), and the latest day in each state."""
        with self.engine.connect() as connection:
            return {
                "days_done": connection.scalar(_count_days(DAY_DONE)),
                "posts": connection.scalar(select(func.count()).select_from(Post)),
                "latest_day": _iso(connection.scalar(latest_day_with_status(DAY_DONE))),
                "running_day": _iso(connection.scalar(latest_day_with_status(DAY_RUNNING))),
                "failed_day": _iso(connection.scalar(latest_day_with_status(DAY_FAILED))),
                "failed_reason": connection.scalar(_latest_failure_reason()),
            }

    def _existing(self, column: InstrumentedAttribute[str], ids: Sequence[str]) -> set[str]:
        if not ids:
            return set()
        with self.engine.connect() as connection:
            return set(connection.scalars(select(column).where(column.in_(ids))))

    def _record_day(self, day: date, **fields) -> None:
        statement = insert(IngestedDay).values(day=day, **fields)
        with self.engine.begin() as connection:
            connection.execute(statement.on_conflict_do_update(index_elements=["day"], set_=fields))


def connect_store(database_url: str) -> Store:
    return Store(create_engine(sqlalchemy_url(database_url), pool_pre_ping=True))


def _insert_new(table: type[Base], rows: list[dict]) -> Insert:
    return insert(table).values(rows).on_conflict_do_nothing()


def _thread_row(thread: NewThread, day: date) -> dict:
    return {
        "source_id": thread.source_id,
        "title": thread.title,
        "created_at": thread.created_at,
        "first_seen_on": day,
    }


def _post_row(embedded: EmbeddedItem) -> dict:
    item = embedded.item
    return {
        "source_id": item.source_id,
        "thread_source_id": item.thread_source_id,
        "kind": item.kind,
        "author": item.author,
        "created_at": item.created_at,
        "body": item.body,
        "reddit_score": item.reddit_score,
        "parent_source_id": item.parent_source_id,
        "embedding": embedded.embedding,
    }


def _clear_daily_upvotes(day: date) -> Delete:
    return (
        delete(PostUpvotesDaily)
        .where(PostUpvotesDaily.day == day)
        .returning(PostUpvotesDaily.post_source_id)
    )


def _upvote_rows(batch: DayBatch) -> list[dict]:
    return [
        {"post_source_id": post_id, "day": batch.day, "count": count}
        for post_id, count in batch.upvotes.items()
    ]


def _recount_upvotes(post_id: str) -> Update:
    total = (
        select(func.coalesce(func.sum(PostUpvotesDaily.count), 0))
        .where(PostUpvotesDaily.post_source_id == post_id)
        .scalar_subquery()
    )
    return update(Post).where(Post.source_id == post_id).values(upvotes=total)


def _count_days(status: str) -> Select:
    return select(func.count()).select_from(IngestedDay).where(IngestedDay.status == status)


def _latest_failure_reason() -> Select:
    failed = IngestedDay.status == DAY_FAILED
    return select(IngestedDay.error).where(failed).order_by(IngestedDay.day.desc()).limit(1)


def _iso(day: date | None) -> str | None:
    return day.isoformat() if day else None


def _now() -> datetime:
    return datetime.now(UTC)
