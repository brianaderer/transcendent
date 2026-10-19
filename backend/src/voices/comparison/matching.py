"""Matching the topics a report names to our topics by meaning (atlas plate 70): "winter
prep" should find the topic "Winterizing and haul-out". Pure code, no model call."""

from collections.abc import Sequence
from typing import Protocol

import numpy as np

# How alike a name and a topic must be, by cosine similarity of their embeddings, to count as
# the same topic. A starting default, to be tuned against names real reports produce.
MATCH_SIMILARITY = 0.7


class ComparisonEmbedder(Protocol):
    def embed_for_comparison(self, texts: Sequence[str]) -> list[list[float]]: ...


class DescribedTopic(Protocol):
    """Anything with a topic's id, label and description: `TopicInfo`, `KeyTopic`."""

    @property
    def id(self) -> int: ...
    @property
    def label(self) -> str: ...
    @property
    def description(self) -> str: ...


Matches = dict[str, int | None]  # each name to the id of the topic it matched, or None


def match_names(
    names: list[str], topics: Sequence[DescribedTopic], embedder: ComparisonEmbedder
) -> Matches:
    """Each distinct name to its most similar topic, compared as "label: description", when
    the similarity is at least MATCH_SIMILARITY. A topic is claimed by one name only: when
    several names' best match is the same topic, the most similar keeps it and the others
    match nothing."""
    distinct = list(dict.fromkeys(names))
    if not distinct or not topics:
        return dict.fromkeys(distinct)
    similarity = _similarities(distinct, topics, embedder)
    return _claim(distinct, [t.id for t in topics], similarity)


def _similarities(
    names: list[str], topics: Sequence[DescribedTopic], embedder: ComparisonEmbedder
) -> np.ndarray:
    """Cosine similarity of every name (rows) with every topic (columns)."""
    texts = names + [f"{t.label}: {t.description}" for t in topics]
    vectors = _unit_rows(np.asarray(embedder.embed_for_comparison(texts), dtype=float))
    return vectors[: len(names)] @ vectors[len(names) :].T


def _unit_rows(vectors: np.ndarray) -> np.ndarray:
    lengths = np.linalg.norm(vectors, axis=1, keepdims=True)
    return np.divide(vectors, lengths, out=np.zeros_like(vectors), where=lengths > 0)


def _claim(names: list[str], topic_ids: list[int], similarity: np.ndarray) -> Matches:
    best = [int(column) for column in similarity.argmax(axis=1)]
    strongest_first = sorted(range(len(names)), key=lambda n: -similarity[n, best[n]])
    matches: Matches = dict.fromkeys(names)
    claimed: set[int] = set()
    for n in strongest_first:
        if similarity[n, best[n]] >= MATCH_SIMILARITY and best[n] not in claimed:
            claimed.add(best[n])
            matches[names[n]] = topic_ids[best[n]]
    return matches
