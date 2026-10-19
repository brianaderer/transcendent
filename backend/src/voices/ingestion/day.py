"""One day of r/sailing: fetch, filter, fold agreeing replies into upvotes, embed, store.

The unit of work for the catch-up (atlas plate 40). Everything is fetched and computed first,
then saved in one transaction, so a day that fails part-way leaves nothing behind.
"""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from typing import Protocol

from voices.ingestion.catch_up import Emit, announce_step
from voices.ingestion.filters import is_unwanted
from voices.ingestion.items import Item


class Archive(Protocol):
    def posts_created_between(self, start: datetime, end: datetime) -> list[Item]: ...
    def comments_created_between(self, start: datetime, end: datetime) -> list[Item]: ...
    def posts_by_id(self, ids: Sequence[str]) -> list[Item]: ...


class DocumentEmbedder(Protocol):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...


class Agreement(Protocol):
    def agreeing(self, texts: Sequence[str]) -> list[bool]: ...


@dataclass(frozen=True)
class NewThread:
    source_id: str
    title: str
    created_at: datetime


@dataclass(frozen=True)
class EmbeddedItem:
    item: Item
    embedding: list[float]


@dataclass
class DayBatch:
    """Everything one day adds to the database, saved together."""

    day: date
    threads: list[NewThread] = field(default_factory=list)
    posts: list[EmbeddedItem] = field(default_factory=list)
    upvotes: dict[str, int] = field(default_factory=dict)  # parent post id -> agreeing replies


class DayStore(Protocol):
    def known_post_ids(self, ids: Sequence[str]) -> set[str]: ...
    def known_thread_ids(self, ids: Sequence[str]) -> set[str]: ...
    def noise_thread_ids(self, ids: Sequence[str]) -> set[str]: ...
    def save_day(self, batch: DayBatch) -> None: ...


@dataclass(frozen=True)
class DaySteps:
    """What was left after each step of a day, kept so the day's counts can be read off it."""

    fetched: list[Item]
    wanted: list[Item]
    off_noise_threads: list[Item]
    threaded: list[Item]
    agreeing: list[Item]
    batch: DayBatch


class DayIngestion:
    def __init__(
        self,
        archive: Archive,
        embedder: DocumentEmbedder,
        agreement: Agreement,
        store: DayStore,
        emit: Emit,
    ):
        self.archive = archive
        self.embedder = embedder
        self.agreement = agreement
        self.store = store
        self.emit = emit

    def process(self, day: date) -> dict[str, int]:
        """Fetch, filter, fold and embed one day, save it, and say what happened. Fetching
        and embedding, the slow steps, are announced live as they begin."""
        announce_step(self.emit, day, "fetching")
        fetched = self._fetch(day)
        wanted = [item for item in fetched if not is_unwanted(item)]
        off_noise_threads = self._without_noise_threads(wanted)
        threads, threaded = self._attach_threads(off_noise_threads)
        agreeing, kept = self._split_agreeing(threaded)
        upvotes = self._upvotes_for_parents(agreeing, kept)
        announce_step(self.emit, day, "embedding", posts=len(kept))
        batch = DayBatch(day, threads, self._embed(kept), upvotes)
        self.store.save_day(batch)
        return _day_counts(DaySteps(fetched, wanted, off_noise_threads, threaded, agreeing, batch))

    def _fetch(self, day: date) -> list[Item]:
        start = datetime.combine(day, time(), UTC)
        end = start + timedelta(days=1)
        posts = self.archive.posts_created_between(start, end)
        return posts + self.archive.comments_created_between(start, end)

    def _without_noise_threads(self, items: list[Item]) -> list[Item]:
        """Drops whatever belongs to a thread already deleted as noise (atlas OPEN-31), so it
        isn't stored, embedded and decided again."""
        noise = self.store.noise_thread_ids(sorted({item.thread_source_id for item in items}))
        return [item for item in items if item.thread_source_id not in noise]

    def _attach_threads(self, items: list[Item]) -> tuple[list[NewThread], list[Item]]:
        """Threads started today come from today's posts; a comment on an older thread brings
        that thread's title from the archive. Comments whose thread can't be found are dropped."""
        started_today = {i.source_id: _thread_of(i) for i in items if i.kind == "post"}
        older_ids = {i.thread_source_id for i in items} - started_today.keys()
        in_store = self.store.known_thread_ids(sorted(older_ids))
        from_archive = self.archive.posts_by_id(sorted(older_ids - in_store))
        new_threads = started_today | {p.source_id: _thread_of(p) for p in from_archive}
        known = new_threads.keys() | in_store
        return list(new_threads.values()), [i for i in items if i.thread_source_id in known]

    def _split_agreeing(self, items: list[Item]) -> tuple[list[Item], list[Item]]:
        """Separates comments that only agree with their parent from everything else."""
        comments = [item for item in items if item.kind == "comment"]
        verdicts = self.agreement.agreeing([comment.body for comment in comments])
        agreeing_ids = {
            comment.source_id for comment, agrees in zip(comments, verdicts, strict=True) if agrees
        }
        agreeing = [item for item in items if item.source_id in agreeing_ids]
        kept = [item for item in items if item.source_id not in agreeing_ids]
        return agreeing, kept

    def _upvotes_for_parents(self, agreeing: list[Item], kept: list[Item]) -> dict[str, int]:
        """One upvote per agreeing reply, for parents we have; replies to others are dropped."""
        parents = [reply.parent_source_id for reply in agreeing]
        present = {i.source_id for i in kept} | self.store.known_post_ids(parents)
        return dict(Counter(parent for parent in parents if parent in present))

    def _embed(self, items: list[Item]) -> list[EmbeddedItem]:
        if not items:
            return []
        vectors = self.embedder.embed_documents([item.body for item in items])
        return [EmbeddedItem(item, vector) for item, vector in zip(items, vectors, strict=True)]


def _thread_of(post: Item) -> NewThread:
    return NewThread(post.source_id, post.title or "", post.created_at)


def _day_counts(steps: DaySteps) -> dict[str, int]:
    upvotes = sum(steps.batch.upvotes.values())
    return {
        "fetched": len(steps.fetched),
        "dropped_unwanted": len(steps.fetched) - len(steps.wanted),
        "dropped_as_noise": len(steps.wanted) - len(steps.off_noise_threads),
        "dropped_without_thread": len(steps.off_noise_threads) - len(steps.threaded),
        "upvotes": upvotes,
        "dropped_orphan_upvotes": len(steps.agreeing) - upvotes,
        "stored": len(steps.batch.posts),
        "threads_added": len(steps.batch.threads),
    }
