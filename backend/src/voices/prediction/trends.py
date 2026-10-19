"""Each topic's trend as it stood the day before a range began (atlas plate 50, OPEN-11 and
OPEN-22): its engagement in the periods before the range, and a damped projection of that
history one period ahead, onto the range itself."""

import math
from collections.abc import Sequence
from datetime import date
from typing import Protocol

from pydantic import BaseModel

from voices.explore.day_range import DayRange
from voices.explore.direction import Direction, trend
from voices.explore.range_topics import TopicData, rows_by_topic
from voices.explore.shapes import TopicDay, TopicInfo

PERIODS_SHOWN = 4  # periods of history behind each projection, each as long as the range
LEVEL_SMOOTHING = 0.7  # how far each period moves the level towards what was measured
TREND_SMOOTHING = 0.5  # how far each period moves the trend towards the latest change
DAMPING = 0.8  # each period ahead keeps this share of the trend, so growth levels off
SMALLEST_SPREAD = 0.4  # on the log scale; never narrower than a third below to a half above


class TopicTrend(BaseModel):
    topic_id: int
    label: str
    description: str
    periods: list[int]  # engagement in each period before the range, oldest first
    expected: float  # projected engagement for the range itself
    low: float  # the projection's range: one typical fitting error either side
    high: float
    direction: Direction  # new, or how `expected` compares with the last period


class TrendData(TopicData, Protocol):
    """Topics' daily engagement and their labels; `ExploreStore` satisfies it."""


def topic_trends(data: TrendData, days: DayRange) -> list[TopicTrend]:
    """Every topic known the day before `days` began with engagement in the PERIODS_SHOWN
    periods before it, projected onto `days`, highest projection first (ties by id). Nothing
    from inside `days` is read."""
    periods = periods_before(days)
    rows = data.topic_days(periods[0].start, periods[-1].end)
    by_topic = rows_by_topic(rows)
    known = [t for t in data.topics(sorted(by_topic)) if t.first_seen < days.start]
    trends = [_trend(t, _engagement(by_topic[t.id], periods), periods) for t in known]
    active = [t for t in trends if any(t.periods)]
    return sorted(active, key=lambda t: (-t.expected, t.topic_id))


def periods_before(days: DayRange) -> list[DayRange]:
    """The PERIODS_SHOWN periods of the range's length just before it, oldest first."""
    periods = [days.period_before()]
    while len(periods) < PERIODS_SHOWN:
        periods.insert(0, periods[0].period_before())
    return periods


def _engagement(rows: list[TopicDay], periods: list[DayRange]) -> list[int]:
    return [sum(r.engagement for r in rows if r.day in period) for period in periods]


def _trend(info: TopicInfo, engagement: list[int], periods: list[DayRange]) -> TopicTrend:
    log_expected, spread = damped_projection([math.log1p(n) for n in engagement])
    expected = math.expm1(log_expected)
    return TopicTrend(
        topic_id=info.id,
        label=info.label,
        description=info.description,
        periods=engagement,
        expected=expected,
        low=max(0.0, math.expm1(log_expected - spread)),
        high=math.expm1(log_expected + spread),
        direction=_direction(info.first_seen, expected, engagement[-1], periods[-1]),
    )


def _direction(first_seen: date, expected: float, last: int, last_period: DayRange) -> Direction:
    if first_seen >= last_period.start:
        return "new"
    return trend(round(expected), last)


def damped_projection(series: Sequence[float]) -> tuple[float, float]:
    """Holt's linear method with a damped trend: the next value, and the typical one-step
    fitting error, never below SMALLEST_SPREAD. The fit starts at the first non-zero value
    (a topic's silence before it existed is not growth) with a flat trend, so one jump can't
    launch it; a history of zeros projects zero."""
    history = _from_first_activity(series)
    if not history:
        return 0.0, SMALLEST_SPREAD
    level, slope, errors = history[0], 0.0, []
    for value in history[1:]:
        errors.append(value - (level + DAMPING * slope))
        previous, level = level, _blend(LEVEL_SMOOTHING, value, level + DAMPING * slope)
        slope = _blend(TREND_SMOOTHING, level - previous, DAMPING * slope)
    projected = max(0.0, level + DAMPING * slope)
    return projected, max(SMALLEST_SPREAD, _typical(errors))


def _from_first_activity(series: Sequence[float]) -> list[float]:
    first = next((i for i, value in enumerate(series) if value > 0), len(series))
    return list(series[first:])


def _blend(weight: float, new: float, old: float) -> float:
    return weight * new + (1 - weight) * old


def _typical(errors: list[float]) -> float:
    return math.sqrt(sum(e * e for e in errors) / len(errors)) if errors else 0.0
