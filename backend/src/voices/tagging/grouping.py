"""Groups the threads being decided today by meaning (atlas plate 21).

Every thread lands in a group, even one of its own, so every thread gets a decision.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from sklearn.cluster import AgglomerativeClustering

# Threads closer than this (cosine distance) on average join one group; measured on three
# real days of r/sailing, it grouped real subjects together (atlas OPEN-29).
GROUPING_DISTANCE = 0.3


@dataclass(frozen=True)
class EncodedThread:
    source_id: str
    embedding: Sequence[float]


@dataclass(frozen=True)
class Group:
    members: list[EncodedThread]
    centroid: list[float]


def group_by_meaning(threads: Sequence[EncodedThread]) -> list[Group]:
    if not threads:
        return []
    if len(threads) == 1:  # the clustering needs at least two threads to compare
        return [_group(list(threads))]
    directions = _unit_length(np.array([thread.embedding for thread in threads], dtype=float))
    labels = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=GROUPING_DISTANCE,
        metric="cosine",
        linkage="average",
    ).fit_predict(directions)
    return [
        _group([t for t, n in zip(threads, labels, strict=True) if n == label])
        for label in _in_order(labels)
    ]


def _group(members: list[EncodedThread]) -> Group:
    directions = _unit_length(np.array([thread.embedding for thread in members], dtype=float))
    return Group(members, _unit_length(directions.mean(axis=0)).tolist())


def _in_order(labels: np.ndarray) -> list[int]:
    """Group labels in the order their first thread came, so results are repeatable."""
    return list(dict.fromkeys(labels.tolist()))


def _unit_length(vectors: np.ndarray) -> np.ndarray:
    """Scaled to length one, so closeness by distance is closeness in meaning (cosine)."""
    lengths = np.linalg.norm(vectors, axis=-1, keepdims=True)
    return vectors / np.where(lengths == 0, 1, lengths)
