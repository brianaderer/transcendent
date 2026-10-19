import math
from datetime import date, timedelta

import pytest

from tests.stand_ins import RecordingTopicData, topic_day, topic_info
from voices.explore.day_range import DayRange
from voices.prediction.trends import (
    PERIODS_SHOWN,
    SMALLEST_SPREAD,
    damped_projection,
    periods_before,
    topic_trends,
)

DAYS = DayRange(date(2026, 10, 12), date(2026, 10, 18))  # a week
PERIODS = periods_before(DAYS)


def history(topic_id, engagement_by_period):
    """One day of engagement at the start of each period before DAYS, oldest first."""
    return [
        topic_day(topic_id, period.start, n)
        for period, n in zip(PERIODS, engagement_by_period, strict=True)
        if n
    ]


def trends_of(*histories, topics=None):
    rows = [row for h in histories for row in h]
    ids = sorted({row.topic_id for row in rows})
    return topic_trends(RecordingTopicData(rows, topics or [topic_info(i) for i in ids]), DAYS)


def projected(series):
    log_value, _ = damped_projection([math.log1p(n) for n in series])
    return math.expm1(log_value)


def test_the_periods_are_as_long_as_the_range_and_end_the_day_before_it():
    assert len(PERIODS) == PERIODS_SHOWN
    assert PERIODS[-1].end == DAYS.start - timedelta(days=1)
    assert PERIODS[0] == DayRange(date(2026, 9, 14), date(2026, 9, 20))
    assert all(p.length == DAYS.length for p in PERIODS)


def test_only_days_before_the_range_are_read():
    data = RecordingTopicData()

    topic_trends(data, DAYS)

    assert data.asked == [(date(2026, 9, 14), date(2026, 10, 11))]


def test_engagement_inside_the_range_changes_nothing():
    before = history(1, [5, 5, 5, 5])
    inside = [topic_day(1, DAYS.start, 1000)]

    assert trends_of(before) == trends_of(before + inside)


def test_a_topic_first_seen_inside_the_range_was_not_known_and_is_left_out():
    rows = history(1, [0, 0, 0, 4])

    assert trends_of(rows, topics=[topic_info(1, first_seen=DAYS.start)]) == []


def test_engagement_is_summed_per_period_oldest_first():
    rows = history(1, [1, 2, 3, 4]) + [topic_day(1, PERIODS[3].end, 6)]

    [only] = trends_of(rows)

    assert only.periods == [1, 2, 3, 10]


def test_a_topic_quiet_in_every_period_is_left_out():
    assert trends_of([topic_day(1, PERIODS[0].start, 0)]) == []


def test_no_topics_give_no_trends():
    assert trends_of() == []


def test_a_steady_topic_is_projected_where_it_is_and_reads_steady():
    [only] = trends_of(history(1, [100, 100, 100, 100]))

    assert only.expected == pytest.approx(100)
    assert only.direction == "steady"


def test_the_range_brackets_the_projection_and_never_goes_below_zero():
    [only] = trends_of(history(1, [100, 100, 100, 100]))

    assert 0 <= only.low < only.expected < only.high
    assert math.log1p(only.high) - math.log1p(only.expected) == pytest.approx(SMALLEST_SPREAD)


def test_an_erratic_history_gets_a_wider_range_than_a_steady_one():
    [steady] = trends_of(history(1, [100, 100, 100, 100]))
    [erratic] = trends_of(history(1, [10, 300, 20, 100]))

    assert erratic.high / erratic.expected > steady.high / steady.expected


def test_a_topic_doubling_every_period_reads_rising():
    [only] = trends_of(history(1, [10, 20, 40, 80]))

    assert only.direction == "rising"
    assert only.expected > 80


def test_a_topic_halving_every_period_reads_fading():
    [only] = trends_of(history(1, [80, 40, 20, 10]))

    assert only.direction == "fading"


def test_damping_keeps_a_viral_spike_from_being_projected_past_itself():
    assert projected([10, 10, 10, 1000]) < 1000


def test_one_jump_from_a_short_history_does_not_launch_the_trend():
    assert projected([0, 0, 10, 1000]) <= 1000


def test_silence_before_a_topic_existed_is_not_counted_as_growth():
    assert projected([0, 0, 0, 50]) == pytest.approx(50)


def test_a_history_of_zeros_projects_zero():
    assert damped_projection([0.0, 0.0]) == (0.0, SMALLEST_SPREAD)


def test_a_topic_first_seen_in_the_last_period_reads_new():
    topic = topic_info(1, first_seen=PERIODS[-1].start)

    [only] = trends_of(history(1, [0, 0, 0, 7]), topics=[topic])

    assert only.direction == "new"


def test_a_topic_first_seen_the_day_before_the_last_period_is_not_new():
    topic = topic_info(1, first_seen=PERIODS[-1].start - timedelta(days=1))

    [only] = trends_of(history(1, [0, 0, 0, 7]), topics=[topic])

    assert only.direction != "new"


def test_topics_come_highest_projection_first_ties_by_id():
    big, small = history(3, [50, 50, 50, 50]), history(1, [5, 5, 5, 5])
    tie = history(2, [5, 5, 5, 5])

    assert [t.topic_id for t in trends_of(small, big, tie)] == [3, 1, 2]


def test_a_trend_carries_its_topic_label_and_description():
    [only] = trends_of(history(1, [1, 1, 1, 1]), topics=[topic_info(1, label="Impellers")])

    assert (only.label, only.description) == ("Impellers", "d")
