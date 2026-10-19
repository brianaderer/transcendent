"""Matching the topics a report names to our topics by meaning (atlas plate 70): "winter
prep" should find the topic "Winterizing and haul-out". Pure code, no model call."""

from collections.abc import Mapping, Sequence

import numpy as np

from voices.comparison.answer_key import KeyTopic
from voices.ingestion.embedder import ComparisonEmbedder

# How alike a name and a topic must be, by cosine similarity of their embeddings, to count as
# the same topic (Brian, atlas OPEN-42). The first real run measured right matches at
# 0.83-0.91 and wrong ones at 0.73-0.79, but 0.80 missed a right match at 0.77.
MATCH_SIMILARITY = 0.70


Matches = dict[str, int | None]  # each name to the id of the topic it matched, or None


def topic_texts(topics: Sequence[KeyTopic]) -> dict[int, str]:
    """Each topic's id to the text a name is compared with: "label: description"."""
    return {t.topic_id: f"{t.label}: {t.description}" for t in topics}


def match_names(
    names: list[str], topics: Mapping[int, str], embedder: ComparisonEmbedder
) -> Matches:
    """Each distinct name to the id of the topic whose text (`topic_texts`) is most similar,
    when the similarity is at least MATCH_SIMILARITY. A topic is claimed by one name only:
    when several names' best match is the same topic, the most similar keeps it and the
    others match nothing."""
    distinct = list(dict.fromkeys(names))
    if not distinct or not topics:
        return dict.fromkeys(distinct)
    similarity = _similarities(distinct, list(topics.values()), embedder)
    return _claim(distinct, list(topics), similarity)


def _similarities(
    names: list[str], topic_texts: list[str], embedder: ComparisonEmbedder
) -> np.ndarray:
    """Cosine similarity of every name (rows) with every topic text (columns)."""
    texts = names + topic_texts
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
