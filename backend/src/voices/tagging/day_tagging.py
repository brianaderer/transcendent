"""Tags one day's threads (atlas plate 21): each thread on its first or third day is encoded
as one text, the threads are grouped by meaning, the agent decides each group, the decisions
are applied, threads past their third day with no topic are expired as noise, and daily
engagement is rebuilt."""

from collections.abc import Callable, Sequence
from datetime import date
from typing import Protocol

from voices.ingestion.catch_up import Emit
from voices.tagging.decisions import (
    CandidateTopic,
    ClusterBrief,
    DecidedCluster,
    TypicalPost,
    settle_mints,
)
from voices.tagging.grouping import EncodedThread, Group, group_by_meaning
from voices.tagging.keywords import distinctive_keywords
from voices.tagging.threads import DueThread, thread_text
from voices.tagging.window import window_start

TYPICAL_POSTS_SHOWN = 6
CANDIDATE_TOPICS_SHOWN = 5
KEYWORDS_PER_TOPIC = 8


class DayTaggingStore(Protocol):
    def threads_due(self, day: date) -> list[DueThread]: ...
    def save_thread_embeddings(self, embeddings: dict[str, list[float]]) -> None: ...
    def typical_threads(
        self, ids: Sequence[str], centroid: Sequence[float], limit: int
    ) -> list[TypicalPost]: ...
    def nearest_topics(self, centroid: Sequence[float], limit: int) -> list[CandidateTopic]: ...
    def apply_decisions(
        self, day: date, settled: list[DecidedCluster], keywords: dict[str, list[str]]
    ) -> dict[str, int]: ...
    def expire_noise(self, day: date) -> int: ...
    def rebuild_engagement(self, first_day: date, last_day: date) -> None: ...


class DocumentEmbedder(Protocol):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...


DecideAll = Callable[[date, list[ClusterBrief]], list[DecidedCluster]]
GroupsOf = Callable[[Sequence[EncodedThread]], list[Group]]


class DayTagging:
    def __init__(
        self,
        store: DayTaggingStore,
        embedder: DocumentEmbedder,
        decide_all: DecideAll,
        emit: Emit,
        groups_of: GroupsOf = group_by_meaning,
    ):
        self.store = store
        self.embedder = embedder
        self.decide_all = decide_all
        self.emit = emit
        self.groups_of = groups_of

    def tag(self, day: date) -> dict[str, int]:
        texts = {t.source_id: thread_text(t.post, t.replies) for t in self.store.threads_due(day)}
        groups = self.groups_of(self._encoded_and_kept(texts))
        briefs = [self._brief(day, f"group-{n}", g) for n, g in enumerate(groups, start=1)]
        settled = settle_mints(self.decide_all(day, briefs))
        self._announce(settled)
        counts = self.store.apply_decisions(day, settled, self._keywords(settled, texts))
        expired = self.store.expire_noise(day)
        self.store.rebuild_engagement(window_start(day), day)
        return {"threads": len(texts), "groups": len(briefs), **counts, "noise_expired": expired}

    def _encoded_and_kept(self, texts: dict[str, str]) -> list[EncodedThread]:
        """Embeds each thread's text and saves the embedding with the thread."""
        ids = list(texts)
        vectors = self.embedder.embed_documents([texts[i] for i in ids])
        self.store.save_thread_embeddings(dict(zip(ids, vectors, strict=True)))
        return [EncodedThread(i, v) for i, v in zip(ids, vectors, strict=True)]

    def _brief(self, day: date, name: str, group: Group) -> ClusterBrief:
        ids = [thread.source_id for thread in group.members]
        return ClusterBrief(
            name=name,
            day=day.isoformat(),
            centroid=group.centroid,
            typical_posts=self.store.typical_threads(ids, group.centroid, TYPICAL_POSTS_SHOWN),
            candidates=self.store.nearest_topics(group.centroid, CANDIDATE_TOPICS_SHOWN),
            member_ids=ids,
        )

    def _keywords(
        self, settled: list[DecidedCluster], texts: dict[str, str]
    ) -> dict[str, list[str]]:
        """Keywords for each newly minted topic, against every thread decided today."""
        mints = [d for d in settled if d.decision.action == "mint" and not d.merged_into]
        return {
            m.brief.name: distinctive_keywords(
                [texts[i] for i in m.brief.member_ids], list(texts.values()), KEYWORDS_PER_TOPIC
            )
            for m in mints
        }

    def _announce(self, settled: list[DecidedCluster]) -> None:
        for item in settled:
            self.emit(
                "decision.made",
                group=item.brief.name,
                threads=len(item.brief.member_ids),
                action=item.decision.action,
                topic_id=item.decision.topic_id,
                label=item.decision.label,
                merged_into=item.merged_into,
                reason=item.decision.reason,
            )
