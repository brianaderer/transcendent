"""Scoring one version's report against the answer key (atlas plate 70, OPEN-21, OPEN-22):
which main topics it found, which it invented, whether its order and directions agree with
the data, and how its prediction for the range turned out. Code, not judgment."""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from pydantic import BaseModel

from voices.comparison.answer_key import KeyTopic, main_topics
from voices.comparison.commitment import Commitment, NamedTopic, PredictedTopic
from voices.comparison.matching import Matches, match_names, topic_texts
from voices.ingestion.embedder import ComparisonEmbedder


class Marking(BaseModel):
    """What a report is marked against, for one range: the range's active topics, and the
    topic each name matched. Made by `mark`."""

    active: list[KeyTopic]
    report_matches: Matches
    prediction_matches: Matches


class Scores(BaseModel):
    main_topics: int  # how many main topics the range had (the answer key's length)
    topics_found: int  # distinct main topics the report named
    topics_invented: int  # names that matched no topic active in the range
    order_agreement: float | None  # Spearman's rank correlation over the found topics
    directions_named: int  # found topics, each named with a direction
    directions_right: int  # of those, the ones whose direction matches the key's
    predicted_named: int  # distinct names in the prediction
    predicted_prominent: int  # predicted names that matched a main topic
    predicted_never_came_up: int  # predicted names that matched no active topic
    predicted_direction_right: int  # prominent, and moving the way predicted
    prediction_score: float  # predicted_direction_right / predicted_named; 0 if none named


def mark(
    active: list[KeyTopic],
    report: Commitment,
    prediction: Commitment,
    embedder: ComparisonEmbedder,
) -> Marking:
    """Matches `report.topics` and `prediction.predicted` against `active` (from
    `answer_key.active_topics`), each list separately, so the report's topics and the
    prediction's may each claim the same topic. `report.predicted` isn't scored, so isn't
    matched."""
    texts = topic_texts(active)
    return Marking(
        active=active,
        report_matches=match_names(report.topic_names(), texts, embedder),
        prediction_matches=match_names(prediction.predicted_names(), texts, embedder),
    )


def score(report: Commitment, prediction: Commitment, marking: Marking) -> Scores:
    """Scores `report.topics` against the range's main topics, and `prediction.predicted`
    (made from what was known the day before the range) against what happened in it.
    `report.predicted` is about a period that hasn't happened, so it isn't scored."""
    key = _Key.of(marking.active)
    return Scores(
        main_topics=len(key.main),
        **_report_scores(report.topics, marking.report_matches, key),
        **_prediction_scores(prediction.predicted, marking.prediction_matches, key),
    )


@dataclass(frozen=True)
class _Key:
    main: dict[int, KeyTopic]  # the main topics by id
    active_ids: set[int]

    @classmethod
    def of(cls, active: list[KeyTopic]) -> "_Key":
        main = {t.topic_id: t for t in main_topics(active)}
        return cls(main, {t.topic_id for t in active})

    def unmatched(self, names: set[str], matches: Matches) -> int:
        """Names that matched no topic active in the range."""
        return sum(matches.get(name) not in self.active_ids for name in names)


def _report_scores(named: list[NamedTopic], matches: Matches, key: _Key) -> dict:
    found = _found(named, matches, key)
    pairs = [(found[i], key.main[i]) for i in found]
    return {
        "topics_found": len(found),
        "topics_invented": key.unmatched({n.name for n in named}, matches),
        "order_agreement": rank_agreement([n.rank for n, _ in pairs], [k.rank for _, k in pairs]),
        "directions_named": len(pairs),
        "directions_right": sum(n.direction == k.direction for n, k in pairs),
    }


def _prediction_scores(predicted: list[PredictedTopic], matches: Matches, key: _Key) -> dict:
    prominent = _found(predicted, matches, key)
    right = sum(p.direction == key.main[i].direction for i, p in prominent.items())
    names = {p.name for p in predicted}
    return {
        "predicted_named": len(names),
        "predicted_prominent": len(prominent),
        "predicted_never_came_up": key.unmatched(names, matches),
        "predicted_direction_right": right,
        "prediction_score": right / len(names) if names else 0.0,
    }


def _found[T: (NamedTopic, PredictedTopic)](
    named: list[T], matches: Matches, key: _Key
) -> dict[int, T]:
    """Each main topic a name matched, with the first entry that named it."""
    found: dict[int, T] = {}
    for entry in named:
        topic_id = matches.get(entry.name)
        if topic_id in key.main and topic_id not in found:
            found[topic_id] = entry
    return found


def rank_agreement(ours: Sequence[float], theirs: Sequence[float]) -> float | None:
    """Spearman's rank correlation, from 1 (same order) to -1 (reversed); ties share their
    average rank. None when it can't be measured: fewer than two pairs, or one side giving
    every pair the same rank."""
    if len(ours) < 2 or len(set(ours)) < 2 or len(set(theirs)) < 2:
        return None
    return float(np.corrcoef(_average_ranks(ours), _average_ranks(theirs))[0, 1])


def _average_ranks(values: Sequence[float]) -> list[float]:
    """1 for the smallest value upwards; equal values share the average of their places."""
    ordered = sorted(values)
    return [ordered.index(v) + (ordered.count(v) + 1) / 2 for v in values]
