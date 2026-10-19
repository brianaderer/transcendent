from tests.bakeoff.conftest import AlwaysAttachesToTheft, NeverDecides
from voices.bakeoff.runner import run_bakeoff
from voices.bakeoff.sample_store import SampleStore
from voices.bakeoff.scoring import Verdict


def run(sample, embedder, model):
    store = SampleStore(sample, embedder)
    [result] = run_bakeoff(["anthropic/claude-haiku-5.5"], store, embedder, lambda name: model)
    return result


def test_each_case_is_judged_and_counted(sample, embedder):
    result = run(sample, embedder, AlwaysAttachesToTheft())

    assert [c.verdict for c in result.cases] == [Verdict.RIGHT, Verdict.WRONG_TOPIC]
    assert result.right == 1 and result.share_right == 0.5


def test_tokens_and_cost_add_up_over_the_cases(sample, embedder):
    result = run(sample, embedder, AlwaysAttachesToTheft())

    assert (result.tokens_in, result.tokens_out) == (2000, 200)
    assert result.cost == result.price.of(2000, 200)


def test_a_model_that_never_decides_is_judged_as_making_no_decision(sample, embedder):
    result = run(sample, embedder, NeverDecides())

    assert {c.verdict for c in result.cases} == {Verdict.NO_DECISION}
