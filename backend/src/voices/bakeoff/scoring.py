"""Judges one decision against its case's right answer."""

from enum import StrEnum

from voices.bakeoff.sample import Case
from voices.tagging.decisions import Decision


class Verdict(StrEnum):
    RIGHT = "right"
    WRONG_TOPIC = "attached to the wrong topic"
    DUPLICATE_TOPIC = "started a topic that already exists"
    REAL_CALLED_NOISE = "called a real conversation noise"
    NEW_SUBJECT_ATTACHED = "attached a new subject to an old topic"
    NOISE_KEPT = "kept noise as a topic"
    NO_DECISION = "made no decision"


# (right answer, given answer) for every way of giving the wrong action.
_WRONG_ACTION_VERDICTS = {
    ("attach", "mint"): Verdict.DUPLICATE_TOPIC,
    ("attach", "noise"): Verdict.REAL_CALLED_NOISE,
    ("mint", "noise"): Verdict.REAL_CALLED_NOISE,
    ("mint", "attach"): Verdict.NEW_SUBJECT_ATTACHED,
    ("noise", "attach"): Verdict.NOISE_KEPT,
    ("noise", "mint"): Verdict.NOISE_KEPT,
}


def judge(case: Case, decision: Decision) -> Verdict:
    if decision.action != case.expected:
        return _WRONG_ACTION_VERDICTS[(case.expected, decision.action)]
    if case.expected == "attach" and decision.topic_id != case.topic_id:
        return Verdict.WRONG_TOPIC
    return Verdict.RIGHT
