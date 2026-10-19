import pytest

from voices.comparison.answer_key import MAIN_TOPICS, KeyTopic
from voices.comparison.commitment import Commitment, NamedTopic, PredictedTopic
from voices.comparison.scoring import Marking, rank_agreement, score

NOTHING = Commitment(topics=[], predicted=[])


def key_topic(topic_id, rank, direction="steady"):
    return KeyTopic(
        topic_id=topic_id,
        label=f"t{topic_id}",
        description="d",
        rank=rank,
        engagement=100 - rank,
        direction=direction,
    )


# Topics 1-3 are main topics; 99 is active in the range but below the cut.
ACTIVE = [key_topic(1, 1, "rising"), key_topic(2, 2, "fading"), key_topic(3, 3)]
ACTIVE += [key_topic(99, MAIN_TOPICS + 1)]


def report(*named):
    """Each entry is (name, rank, direction)."""
    return Commitment(
        topics=[NamedTopic(name=n, rank=r, direction=d) for n, r, d in named], predicted=[]
    )


def prediction(*predicted):
    return Commitment(
        topics=[], predicted=[PredictedTopic(name=n, direction=d) for n, d in predicted]
    )


def scores_of(report_=NOTHING, prediction_=NOTHING, report_matches=None, prediction_matches=None):
    marking = Marking(
        active=ACTIVE,
        report_matches=report_matches or {},
        prediction_matches=prediction_matches or {},
    )
    return score(report_, prediction_, marking)


def test_an_empty_report_finds_nothing_and_scores_zero():
    scores = scores_of()

    assert scores.main_topics == 3
    assert (scores.topics_found, scores.topics_invented, scores.order_agreement) == (0, 0, None)
    assert (scores.predicted_named, scores.prediction_score) == (0, 0.0)


def test_found_counts_distinct_main_topics_named():
    named = report(("a", 1, "rising"), ("b", 2, "fading"), ("c", 3, "steady"))

    scores = scores_of(named, report_matches={"a": 1, "b": 2, "c": None})

    assert scores.topics_found == 2


def test_an_active_topic_below_the_cut_is_neither_found_nor_invented():
    scores = scores_of(report(("a", 1, "steady")), report_matches={"a": 99})

    assert (scores.topics_found, scores.topics_invented) == (0, 0)


def test_a_name_matching_no_active_topic_is_invented():
    scores = scores_of(report(("a", 1, "steady")), report_matches={"a": None})

    assert scores.topics_invented == 1


def test_a_name_matching_a_topic_quiet_in_the_range_is_invented():
    scores = scores_of(report(("a", 1, "steady")), report_matches={"a": 42})

    assert scores.topics_invented == 1


def test_the_same_order_agrees_fully():
    named = report(("a", 1, "rising"), ("b", 2, "fading"), ("c", 3, "steady"))

    scores = scores_of(named, report_matches={"a": 1, "b": 2, "c": 3})

    assert scores.order_agreement == pytest.approx(1.0)


def test_the_reverse_order_disagrees_fully():
    named = report(("a", 3, "rising"), ("b", 2, "fading"), ("c", 1, "steady"))

    scores = scores_of(named, report_matches={"a": 1, "b": 2, "c": 3})

    assert scores.order_agreement == pytest.approx(-1.0)


def test_order_is_compared_by_rank_not_by_rank_number():
    named = report(("a", 4, "rising"), ("b", 7, "fading"))

    scores = scores_of(named, report_matches={"a": 1, "b": 2})

    assert scores.order_agreement == pytest.approx(1.0)


def test_one_found_topic_has_no_order_to_compare():
    scores = scores_of(report(("a", 1, "rising")), report_matches={"a": 1})

    assert scores.order_agreement is None


def test_ranks_all_tied_have_no_order_to_compare():
    assert rank_agreement([1, 1, 1], [1, 2, 3]) is None


def test_tied_ranks_share_their_average_rank():
    assert rank_agreement([1, 2, 2, 4], [1, 2, 3, 4]) == pytest.approx(0.9486833)


def test_directions_are_checked_for_found_topics_only():
    named = report(("a", 1, "rising"), ("b", 2, "rising"), ("c", 3, "rising"))

    scores = scores_of(named, report_matches={"a": 1, "b": 2, "c": None})

    assert (scores.directions_named, scores.directions_right) == (2, 1)


def test_a_main_topic_named_only_once_counts_its_first_entry():
    named = report(("a", 1, "rising"), ("a", 5, "fading"))

    scores = scores_of(named, report_matches={"a": 1})

    assert (scores.topics_found, scores.directions_right) == (1, 1)


def test_predictions_are_counted_prominent_unseen_and_right():
    predicted = prediction(("a", "rising"), ("b", "rising"), ("c", "steady"), ("d", "steady"))
    matches = {"a": 1, "b": 2, "c": 99, "d": None}

    scores = scores_of(prediction_=predicted, prediction_matches=matches)

    assert scores.predicted_named == 4
    assert scores.predicted_prominent == 2
    assert scores.predicted_never_came_up == 1
    assert scores.predicted_direction_right == 1
    assert scores.prediction_score == pytest.approx(0.25)


def test_a_perfect_prediction_scores_one():
    predicted = prediction(("a", "rising"), ("b", "fading"))

    scores = scores_of(prediction_=predicted, prediction_matches={"a": 1, "b": 2})

    assert scores.prediction_score == 1.0


def test_the_reports_own_prediction_is_not_scored():
    both = Commitment(topics=[], predicted=[PredictedTopic(name="a", direction="rising")])

    scores = scores_of(report_=both)

    assert scores.predicted_named == 0


def test_the_prediction_and_the_report_may_claim_the_same_topic():
    scores = scores_of(
        report(("a", 1, "rising")),
        prediction(("a", "rising")),
        report_matches={"a": 1},
        prediction_matches={"a": 1},
    )

    assert (scores.topics_found, scores.predicted_prominent) == (1, 1)
