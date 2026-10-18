"""Tags one day's posts: cluster the last three days, decide each cluster, apply the decisions,
delete what stayed unclustered for three days, rebuild daily engagement (atlas plate 21)."""

from collections.abc import Callable, Sequence
from datetime import date, timedelta
from typing import Protocol

from voices.ingestion.catch_up import Emit
from voices.tagging.clustering import MIN_CLUSTER_SIZE, Cluster, WindowPost, find_clusters
from voices.tagging.decisions import (
    CandidateTopic,
    ClusterBrief,
    DecidedCluster,
    TypicalPost,
    settle_mints,
)
from voices.tagging.keywords import distinctive_keywords

LOOKAHEAD_DAYS = 3  # a post has this many days to fall into a cluster (atlas OPEN-14)
TYPICAL_POSTS_SHOWN = 6
CANDIDATE_TOPICS_SHOWN = 5
KEYWORDS_PER_TOPIC = 8


class TaggingStore(Protocol):
    def window_posts(self, first_day: date, last_day: date) -> list[WindowPost]: ...
    def typical_posts(
        self, ids: Sequence[str], centroid: Sequence[float], limit: int
    ) -> list[TypicalPost]: ...
    def nearest_topics(self, centroid: Sequence[float], limit: int) -> list[CandidateTopic]: ...
    def texts(self, ids: Sequence[str]) -> list[str]: ...
    def apply_decisions(
        self, day: date, settled: list[DecidedCluster], keywords: dict[str, list[str]]
    ) -> dict[str, int]: ...
    def delete_expired_pending(self, before: date) -> int: ...
    def rebuild_engagement(self, first_day: date, last_day: date) -> None: ...


DecideAll = Callable[[date, list[ClusterBrief]], list[DecidedCluster]]


def _clusters_at_standard_size(posts: list[WindowPost]) -> list[Cluster]:
    return find_clusters(posts, min_cluster_size=MIN_CLUSTER_SIZE)


class DayTagging:
    def __init__(
        self,
        store: TaggingStore,
        decide_all: DecideAll,
        emit: Emit,
        clusters_of: Callable[[list[WindowPost]], list[Cluster]] = _clusters_at_standard_size,
    ):
        self.store = store
        self.decide_all = decide_all
        self.emit = emit
        self.clusters_of = clusters_of

    def tag(self, day: date) -> dict[str, int]:
        first_day = day - timedelta(days=LOOKAHEAD_DAYS - 1)
        window = self.store.window_posts(first_day, day)
        waiting = [c for c in self.clusters_of(window) if c.has_pending]
        briefs = [self._brief(day, f"cluster-{n}", c) for n, c in enumerate(waiting, start=1)]
        settled = settle_mints(self.decide_all(day, briefs))
        self._announce(settled)
        counts = self.store.apply_decisions(day, settled, self._keywords(settled, window))
        counts["expired"] = self.store.delete_expired_pending(before=first_day)
        self.store.rebuild_engagement(first_day, day)
        return {"clusters": len(briefs), **counts}

    def _brief(self, day: date, name: str, cluster: Cluster) -> ClusterBrief:
        ids = [post.source_id for post in cluster.members]
        return ClusterBrief(
            name=name,
            day=day.isoformat(),
            centroid=cluster.centroid,
            typical_posts=self.store.typical_posts(ids, cluster.centroid, TYPICAL_POSTS_SHOWN),
            candidates=self.store.nearest_topics(cluster.centroid, CANDIDATE_TOPICS_SHOWN),
            member_ids=ids,
        )

    def _keywords(
        self, settled: list[DecidedCluster], window: list[WindowPost]
    ) -> dict[str, list[str]]:
        """Keywords for each newly minted topic, against everything in the window."""
        mints = [d for d in settled if d.decision.action == "mint" and not d.merged_into]
        if not mints:
            return {}
        everything = self.store.texts([post.source_id for post in window])
        return {
            m.brief.name: distinctive_keywords(
                self.store.texts(m.brief.member_ids), everything, KEYWORDS_PER_TOPIC
            )
            for m in mints
        }

    def _announce(self, settled: list[DecidedCluster]) -> None:
        for item in settled:
            self.emit(
                "decision.made",
                cluster=item.brief.name,
                posts=len(item.brief.member_ids),
                action=item.decision.action,
                topic_id=item.decision.topic_id,
                label=item.decision.label,
                merged_into=item.merged_into,
                reason=item.decision.reason,
            )
