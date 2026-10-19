import pytest

from voices.bakeoff.sample import Case
from voices.bakeoff.scoring import Verdict, judge
from voices.tagging.decisions import Decision


def decision(action, topic_id=None):
    return Decision(action=action, topic_id=topic_id, label="x", reason="r")


ATTACH = Case("a", ["t"], "attach", 1)
MINT = Case("m", ["t"], "mint", None)
NOISE = Case("n", ["t"], "noise", None)


@pytest.mark.parametrize(
    ("case", "answer", "verdict"),
    [
        (ATTACH, decision("attach", 1), Verdict.RIGHT),
        (ATTACH, decision("attach", 2), Verdict.WRONG_TOPIC),
        (ATTACH, decision("mint"), Verdict.DUPLICATE_TOPIC),
        (ATTACH, decision("noise"), Verdict.REAL_CALLED_NOISE),
        (MINT, decision("mint"), Verdict.RIGHT),
        (MINT, decision("attach", 1), Verdict.NEW_SUBJECT_ATTACHED),
        (MINT, decision("noise"), Verdict.REAL_CALLED_NOISE),
        (NOISE, decision("noise"), Verdict.RIGHT),
        (NOISE, decision("mint"), Verdict.NOISE_KEPT),
        (NOISE, decision("attach", 1), Verdict.NOISE_KEPT),
    ],
)
def test_each_answer_is_judged_against_the_right_answer(case, answer, verdict):
    assert judge(case, answer) is verdict
