"""Groups the last three days of posts by meaning (atlas plate 21).

HDBSCAN finds groups of any number and leaves stragglers out of every group, which is what
the three-day noise rule needs: a post that joins no group for three days is deleted.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from sklearn.cluster import HDBSCAN

MIN_CLUSTER_SIZE = 5  # the smallest group worth a decision; to be tuned against real data
NOT_IN_ANY_CLUSTER = -1  # HDBSCAN's label for a straggler


@dataclass(frozen=True)
class WindowPost:
    source_id: str
    embedding: Sequence[float]
    topic_id: int | None  # None while the post is still waiting for a tag


@dataclass(frozen=True)
class Cluster:
    members: list[WindowPost]
    centroid: list[float]

    @property
    def pending(self) -> list[WindowPost]:
        return [post for post in self.members if post.topic_id is None]

    @property
    def has_pending(self) -> bool:
        return bool(self.pending)


def find_clusters(posts: Sequence[WindowPost], min_cluster_size: int) -> list[Cluster]:
    if len(posts) < min_cluster_size:
        return []
    directions = _unit_length(np.array([post.embedding for post in posts], dtype=float))
    # A quiet three days about one subject is still one conversation, not all noise.
    clusterer = HDBSCAN(min_cluster_size=min_cluster_size, allow_single_cluster=True)
    labels = clusterer.fit_predict(directions)
    return [
        _cluster(posts, directions, labels == label)
        for label in sorted(set(labels) - {NOT_IN_ANY_CLUSTER})
    ]


def _cluster(posts: Sequence[WindowPost], directions: np.ndarray, chosen: np.ndarray) -> Cluster:
    members = [post for post, is_member in zip(posts, chosen, strict=True) if is_member]
    return Cluster(members, _unit_length(directions[chosen].mean(axis=0)).tolist())


def _unit_length(vectors: np.ndarray) -> np.ndarray:
    """Scaled to length one, so closeness by distance is closeness in meaning (cosine)."""
    lengths = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return vectors / np.where(lengths == 0, 1, lengths)
