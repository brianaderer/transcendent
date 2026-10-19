"""Rebuilds every vector the boot seed left behind, before the catch-up runs (atlas plate 07).

Posts first, each embedded whole as at intake; then threads, each encoded as the text it had
when it was last decided, exactly as tagging encodes it; then each topic's centre, the
average of its threads. Work goes in batches, each saved before the next, and every step
picks up whatever still has no vector, so a restart carries on where it stopped.
"""

from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from voices.ingestion.catch_up import Emit
from voices.tagging.threads import DueThread, thread_text
from voices.tagging.window import third_day

ROWS_PER_BATCH = 256  # each batch is saved before the next, so a restart loses at most one
SETTLED = "settled"  # a thread decided on its third day, for the last time


@dataclass(frozen=True)
class Tally:
    """How many rows have their vector, of how many."""

    done: int
    total: int

    @property
    def missing(self) -> int:
        return self.total - self.done


@dataclass(frozen=True)
class PostText:
    source_id: str
    body: str


@dataclass(frozen=True)
class UnencodedThread:
    source_id: str
    first_seen_on: date
    stage: str


class BackfillStore(Protocol):
    def posts_tally(self) -> Tally: ...
    def threads_tally(self) -> Tally: ...
    def topics_tally(self) -> Tally: ...
    def posts_without_embeddings(self, limit: int) -> list[PostText]: ...
    def save_post_embeddings(self, embeddings: dict[str, list[float]]) -> None: ...
    def threads_without_embeddings(self, limit: int) -> list[UnencodedThread]: ...
    def threads_as_of(self, day: date, ids: Sequence[str]) -> list[DueThread]: ...
    def save_thread_embeddings(self, embeddings: dict[str, list[float]]) -> None: ...
    def rebuild_missing_centres(self) -> None: ...


class DocumentEmbedder(Protocol):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...


class Progress(Protocol):
    """Where the backfill's progress is kept for the API to read (`GET /api/ingestion`)."""

    def record(self, what: str, done: int, total: int) -> None: ...
    def recorded(self) -> bool: ...
    def clear(self) -> None: ...


class Backfill:
    def __init__(
        self,
        store: BackfillStore,
        embedder: DocumentEmbedder,
        progress: Progress,
        emit: Emit,
        forget_maps: Callable[[], None],
        batch_size: int = ROWS_PER_BATCH,
    ):
        self.store = store
        self.embedder = embedder
        self.progress = progress
        self.emit = emit
        self.forget_maps = forget_maps
        self.batch_size = batch_size

    def run(self) -> None:
        """Fills every missing vector, then forgets the maps drawn without them. Does nothing
        at all when no vector is missing and no earlier backfill was left unfinished."""
        if self._nothing_missing() and not self.progress.recorded():
            return
        self._fill("posts", self.store.posts_tally(), self._embed_next_posts)
        self._fill("threads", self.store.threads_tally(), self._encode_next_threads)
        self._rebuild_centres()
        self._finish()

    def _nothing_missing(self) -> bool:
        tallies = (self.store.posts_tally(), self.store.threads_tally(), self.store.topics_tally())
        return all(tally.missing == 0 for tally in tallies)

    def _fill(self, what: str, tally: Tally, fill_next_batch: Callable[[], int]) -> None:
        if tally.missing == 0:
            return
        done = tally.done
        self._report(what, done, tally.total)
        while filled := fill_next_batch():
            done += filled
            self._report(what, done, tally.total)

    def _embed_next_posts(self) -> int:
        posts = self.store.posts_without_embeddings(self.batch_size)
        if posts:
            vectors = self.embedder.embed_documents([post.body for post in posts])
            self.store.save_post_embeddings(_by_id([p.source_id for p in posts], vectors))
        return len(posts)

    def _encode_next_threads(self) -> int:
        """Encodes each thread from the text tagging last gave it: as it stood on its third
        day once settled, or on its first while it waits for its third."""
        unencoded = self.store.threads_without_embeddings(self.batch_size)
        for day, ids in _ids_by_day_last_decided(unencoded).items():
            threads = self.store.threads_as_of(day, ids)
            texts = [thread_text(thread.post, thread.replies) for thread in threads]
            vectors = self.embedder.embed_documents(texts)
            self.store.save_thread_embeddings(_by_id([t.source_id for t in threads], vectors))
        return len(unencoded)

    def _rebuild_centres(self) -> None:
        before = self.store.topics_tally()
        if before.missing == 0:
            return
        self._report("topics", before.done, before.total)
        self.store.rebuild_missing_centres()
        after = self.store.topics_tally()
        self._report("topics", after.done, after.total)

    def _finish(self) -> None:
        self.forget_maps()
        self.progress.clear()
        self.emit("backfill.finished")

    def _report(self, what: str, done: int, total: int) -> None:
        self.progress.record(what, done, total)
        self.emit("backfill.progress", what=what, done=done, total=total)


def _ids_by_day_last_decided(threads: list[UnencodedThread]) -> dict[date, list[str]]:
    by_day: dict[date, list[str]] = defaultdict(list)
    for thread in threads:
        by_day[_day_last_decided(thread)].append(thread.source_id)
    return by_day


def _day_last_decided(thread: UnencodedThread) -> date:
    return third_day(thread.first_seen_on) if thread.stage == SETTLED else thread.first_seen_on


def _by_id(ids: list[str], vectors: list[list[float]]) -> dict[str, list[float]]:
    return dict(zip(ids, vectors, strict=True))
