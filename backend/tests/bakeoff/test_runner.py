import pytest

from tests.bakeoff.stand_ins import AlwaysAttachesToTheft, Answers, NeverDecides
from voices.bakeoff.pricing import UnknownPrice
from voices.bakeoff.runner import run_bakeoff
from voices.bakeoff.sample_store import SampleStore
from voices.bakeoff.scoring import Verdict


def run(sample, embedder, model):
    store = SampleStore(sample, embedder)
    [result] = run_bakeoff(["anthropic/claude-haiku-5.5"], store, lambda name: model)
    return result


def test_each_case_is_judged_and_counted(sample, embedder):
    result = run(sample, embedder, AlwaysAttachesToTheft())

    assert [c.verdict for c in result.cases] == [Verdict.RIGHT, Verdict.WRONG_TOPIC]
    assert result.right == 1 and result.share_right == 0.5


def test_tokens_and_cost_add_up_over_the_cases(sample, embedder):
    result = run(sample, embedder, AlwaysAttachesToTheft())

    assert (result.tokens_in, result.tokens_out) == (2000, 200)
    assert result.cost == pytest.approx((2000 * 0.10 + 200 * 0.50) / 1_000_000)


def test_a_model_that_never_decides_is_judged_as_making_no_decision(sample, embedder):
    result = run(sample, embedder, NeverDecides())

    assert {c.verdict for c in result.cases} == {Verdict.NO_DECISION}


def test_an_unpriced_model_stops_the_run_before_any_model_is_connected(sample, embedder):
    connected = []

    with pytest.raises(UnknownPrice):
        names = ["anthropic/claude-haiku-5.5", "someone/else"]
        run_bakeoff(names, SampleStore(sample, embedder), connected.append)

    assert connected == []


def test_answers_read_as_the_topic_they_attach_to_or_the_label_they_mint(sample, embedder):
    assert run(sample, embedder, Answers(action="mint", label="Docking")).cases[0].answer == (
        "mint: Docking"
    )
    assert run(sample, embedder, Answers(action="noise")).cases[0].answer == "noise"
    assert run(sample, embedder, Answers(action="attach", topic_id=99)).cases[0].answer == (
        "attach: topic 99, which does not exist"
    )
