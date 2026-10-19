import pytest

from tests.bakeoff.stand_ins import Answers, NeverDecides, always_attaches_to_theft
from voices.bakeoff.pricing import UnknownPrice
from voices.bakeoff.runner import run_bakeoff
from voices.bakeoff.sample_store import SampleStore
from voices.bakeoff.scoring import Verdict


def run(sample, embedder, model):
    store = SampleStore(sample, embedder)
    [result] = run_bakeoff(["anthropic/claude-haiku-5.5"], store, lambda name: model)
    return result


def test_each_case_is_judged_and_counted(sample, embedder):
    result = run(sample, embedder, always_attaches_to_theft())

    assert [c.verdict for c in result.cases] == [Verdict.RIGHT, Verdict.WRONG_TOPIC]
    assert result.right == 1 and result.share_right == 0.5


def test_tokens_and_cost_add_up_over_the_cases(sample, embedder):
    result = run(sample, embedder, always_attaches_to_theft())

    assert (result.tokens_in, result.tokens_out) == (2000, 200)
    assert result.cost == pytest.approx((2000 * 0.10 + 200 * 0.50) / 1_000_000)


def test_a_model_that_never_decides_is_judged_as_making_no_decision(sample, embedder):
    result = run(sample, embedder, NeverDecides())

    assert {c.verdict for c in result.cases} == {Verdict.NO_DECISION}


def test_an_unpriced_model_stops_the_run_before_any_model_is_connected(sample, embedder):
    connected = []
    names = ["anthropic/claude-haiku-5.5", "someone/else"]
    store = SampleStore(sample, embedder)

    with pytest.raises(UnknownPrice):
        run_bakeoff(names, store, connected.append)

    assert connected == []


@pytest.mark.parametrize(
    ("arguments", "readable"),
    [
        ({"action": "mint", "label": "Docking"}, "mint: Docking"),
        ({"action": "noise"}, "noise"),
        ({"action": "attach", "topic_id": 99}, "attach: topic 99, which does not exist"),
    ],
    ids=["mint", "noise", "unknown topic"],
)
def test_each_answer_reads_as_its_action_and_topic_or_label(sample, embedder, arguments, readable):
    assert run(sample, embedder, Answers(**arguments)).cases[0].answer == readable
