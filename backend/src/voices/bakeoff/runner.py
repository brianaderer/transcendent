"""Runs every sample case through the production tagging decision, once per model."""

import time
from collections.abc import Callable
from dataclasses import dataclass

from voices.bakeoff.metering import CountingTools, Meter, MeteredModel
from voices.bakeoff.pricing import Price, price_of
from voices.bakeoff.sample import Case, topic_label
from voices.bakeoff.sample_store import SampleStore
from voices.bakeoff.scoring import Verdict, judge
from voices.tagging.decider import ChatModel, NoDecision, ToolLoopDecider
from voices.tagging.decisions import Decision


@dataclass(frozen=True)
class Contender:
    model_name: str
    model: ChatModel


@dataclass(frozen=True)
class JudgedAnswer:
    verdict: Verdict
    answer: str  # what the model decided, readable: "attach: Stolen boats", "mint: Docking"
    reason: str


@dataclass(frozen=True)
class CaseResult:
    case: Case
    judged: JudgedAnswer
    seconds: float
    meter: Meter

    @property
    def verdict(self) -> Verdict:
        return self.judged.verdict

    @property
    def answer(self) -> str:
        return self.judged.answer


@dataclass(frozen=True)
class ModelResult:
    model_name: str
    price: Price
    cases: list[CaseResult]

    @property
    def right(self) -> int:
        return self.count(Verdict.RIGHT)

    @property
    def share_right(self) -> float:
        return self.right / len(self.cases)

    def count(self, verdict: Verdict) -> int:
        return sum(1 for result in self.cases if result.verdict is verdict)

    @property
    def tokens_in(self) -> int:
        return sum(result.meter.tokens_in for result in self.cases)

    @property
    def tokens_out(self) -> int:
        return sum(result.meter.tokens_out for result in self.cases)

    @property
    def cost(self) -> float:
        return self.price.of(self.tokens_in, self.tokens_out)

    @property
    def look_ups_per_decision(self) -> float:
        return self._mean([result.meter.look_ups for result in self.cases])

    @property
    def model_calls_per_decision(self) -> float:
        return self._mean([result.meter.model_calls for result in self.cases])

    @property
    def seconds_per_decision(self) -> float:
        return self._mean([result.seconds for result in self.cases])

    def _mean(self, values: list[float]) -> float:
        return sum(values) / len(values)


def run_bakeoff(
    model_names: list[str], store: SampleStore, connect: Callable[[str], ChatModel]
) -> list[ModelResult]:
    """Every model's prices are checked before any model is called, so nothing is spent on a
    run that can't be costed."""
    prices = {name: price_of(name) for name in model_names}
    return [
        ModelResult(name, prices[name], _run_cases(Contender(name, connect(name)), store))
        for name in model_names
    ]


def _run_cases(contender: Contender, store: SampleStore) -> list[CaseResult]:
    return [_run_case(case, contender, store) for case in store.sample.cases]


def _run_case(case: Case, contender: Contender, store: SampleStore) -> CaseResult:
    meter = Meter()
    model = MeteredModel(contender.model, meter)
    decider = ToolLoopDecider(
        model, contender.model_name, CountingTools(store.tools_for(case), meter)
    )
    started = time.monotonic()
    judged = _judged_answer(case, decider, store)
    return CaseResult(case, judged, time.monotonic() - started, meter)


def _judged_answer(case: Case, decider: ToolLoopDecider, store: SampleStore) -> JudgedAnswer:
    try:
        decision = decider.decide(store.brief(case)).decision
    except NoDecision as error:
        return JudgedAnswer(Verdict.NO_DECISION, "none", str(error))
    return JudgedAnswer(judge(case, decision), _readable(decision, store), decision.reason)


def _readable(decision: Decision, store: SampleStore) -> str:
    if decision.action == "attach":
        return f"attach: {topic_label(store.sample, decision.topic_id)}"
    if decision.action == "mint":
        return f"mint: {decision.label}"
    return "noise"
