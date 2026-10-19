"""Runs every sample case through the production tagging decision, once per model."""

import time
from collections.abc import Callable
from dataclasses import dataclass

from voices.bakeoff.metering import CountingTools, Meter, MeteredModel
from voices.bakeoff.pricing import Price, price_of
from voices.bakeoff.sample import Case
from voices.bakeoff.sample_store import SampleStore
from voices.bakeoff.scoring import Verdict, judge
from voices.tagging.decider import ChatModel, NoDecision, ToolLoopDecider
from voices.tagging.decisions import Decision
from voices.tagging.tools import QueryEmbedder, TaggingTools


@dataclass(frozen=True)
class CaseResult:
    case: Case
    verdict: Verdict
    answer: str  # what the model decided, readable: "attach: Stolen boats", "mint: Docking"
    reason: str
    seconds: float
    meter: Meter


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

    def mean(self, measure: Callable[[CaseResult], float]) -> float:
        return sum(measure(result) for result in self.cases) / len(self.cases)


def run_bakeoff(
    model_names: list[str],
    store: SampleStore,
    embedder: QueryEmbedder,
    connect: Callable[[str], ChatModel],
) -> list[ModelResult]:
    """Every model's prices are checked before any model is called, so nothing is spent on a
    run that can't be costed."""
    prices = {name: price_of(name) for name in model_names}
    return [
        ModelResult(name, prices[name], _run_cases(name, connect(name), store, embedder))
        for name in model_names
    ]


def _run_cases(name: str, model: ChatModel, store: SampleStore, embedder: QueryEmbedder):
    return [_run_case(case, name, model, store, embedder) for case in store.sample.cases]


def _run_case(
    case: Case, name: str, model: ChatModel, store: SampleStore, embedder: QueryEmbedder
) -> CaseResult:
    meter = Meter()
    tools = CountingTools(TaggingTools(store, embedder, store.case_day(case)), meter)
    decider = ToolLoopDecider(MeteredModel(model, meter), name, tools)
    started = time.monotonic()
    verdict, answer, reason = _judged_decision(case, decider, store)
    return CaseResult(case, verdict, answer, reason, time.monotonic() - started, meter)


def _judged_decision(case: Case, decider: ToolLoopDecider, store: SampleStore) -> tuple:
    try:
        decision = decider.decide(store.brief(case)).decision
    except NoDecision as error:
        return Verdict.NO_DECISION, "none", str(error)
    return judge(case, decision), _readable(decision, store), decision.reason


def _readable(decision: Decision, store: SampleStore) -> str:
    if decision.action == "attach":
        return f"attach: {store.topic_label(decision.topic_id)}"
    if decision.action == "mint":
        return f"mint: {decision.label}"
    return "noise"
