from datetime import date

from tests.stand_ins import RecordingTopicData, topic_day, topic_info
from voices.comparison.answer_key import MAIN_TOPICS, active_topics, answer_key
from voices.explore.day_range import DayRange
from voices.explore.explore import Explore

DAYS = DayRange(date(2026, 10, 12), date(2026, 10, 18))
BEFORE = date(2026, 10, 5)


def data_with(engagement_in_range, before=None, first_seen=None):
    """Topic n+1 has engagement_in_range[n] on the range's first day."""
    before, first_seen = before or {}, first_seen or {}
    ids = range(1, len(engagement_in_range) + 1)
    rows = [topic_day(i, DAYS.start, n) for i, n in zip(ids, engagement_in_range, strict=True)]
    rows += [topic_day(i, BEFORE, n) for i, n in before.items()]
    infos = [topic_info(i, first_seen.get(i, date(2026, 8, 1))) for i in ids]
    return RecordingTopicData(rows, infos)


def test_no_topics_give_an_empty_key():
    assert answer_key(data_with([]), DAYS) == []


def test_topics_are_ranked_by_engagement_biggest_first():
    key = answer_key(data_with([3, 9, 5]), DAYS)

    assert [(t.topic_id, t.rank, t.engagement) for t in key] == [(2, 1, 9), (3, 2, 5), (1, 3, 3)]


def test_equal_engagement_shares_a_rank_and_the_next_rank_skips():
    key = answer_key(data_with([9, 5, 5, 1]), DAYS)

    assert [t.rank for t in key] == [1, 2, 2, 4]


def test_the_key_keeps_the_main_topics_only():
    key = answer_key(data_with(list(range(100, 100 - MAIN_TOPICS - 3, -1))), DAYS)

    assert len(key) == MAIN_TOPICS


def test_a_tie_at_the_cut_keeps_every_tied_topic():
    engagement = list(range(100, 100 - MAIN_TOPICS + 1, -1)) + [1, 1]

    assert len(answer_key(data_with(engagement), DAYS)) == MAIN_TOPICS + 1


def test_the_active_topics_include_those_below_the_cut():
    engagement = list(range(100, 100 - MAIN_TOPICS - 3, -1))

    assert len(active_topics(data_with(engagement), DAYS)) == MAIN_TOPICS + 3


def test_a_topic_quiet_in_the_range_is_not_active():
    data = data_with([0, 4], before={1: 50})

    assert [t.topic_id for t in active_topics(data, DAYS)] == [2]


def test_directions_are_the_momentum_within_the_range():
    first, last = DAYS.start, DAYS.end
    rows = [
        topic_day(1, last, 9),  # building toward the end
        topic_day(2, first, 9),  # a burst at the start that died away
        topic_day(3, first, 5),
        topic_day(3, last, 5),  # holding
        topic_day(4, last, 9),
    ]
    infos = [topic_info(1), topic_info(2), topic_info(3), topic_info(4, first_seen=first)]

    key = answer_key(RecordingTopicData(rows, infos), DAYS)

    assert {t.topic_id: t.direction for t in key} == {
        1: "rising",
        2: "fading",
        3: "steady",
        4: "new",
    }


def test_the_key_says_what_the_explore_page_says():
    data = data_with([20, 5, 10, 3], before={1: 10, 2: 10, 3: 10}, first_seen={4: DAYS.start})
    page = Explore(data, cache=None, flatten=None).topics(DAYS)

    key = answer_key(data, DAYS)

    assert [(t.topic_id, t.engagement, t.direction) for t in key] == [
        (t.id, t.engagement, t.direction) for t in page
    ]
