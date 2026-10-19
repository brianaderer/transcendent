"""One comparison run (atlas plate 70): versions A (no tools) and B (tools that read our store)
each write the report for a range and predict it from the day before; both are then scored
against the same answer key. Everything is streamed live; nothing is kept but the result,
briefly, so the page can show it (atlas OPEN-24)."""

from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal, Protocol

from pydantic import BaseModel

from voices.comparison.answer_key import KeyTopic, active_topics, main_topics
from voices.comparison.commitment import Commitment, NamedTopic, PredictedTopic
from voices.comparison.scoring import Marking, Scores, mark, score
from voices.explore.day_range import DayRange
from voices.explore.range_topics import TopicData, topics_in_range
from voices.ingestion.embedder import ComparisonEmbedder
from voices.prediction.trends import topic_trends
from voices.report.tasks import Prediction, Report, Task, predict_task, write_task
from voices.report.tools import QueryEmbedder, ReportStore, ReportTools
from voices.report.writer import ChatModel, Emit, ReportWriter, Written

Version = Literal["A", "B"]
VERSIONS: tuple[Version, ...] = ("A", "B")
DAYS_SEEN_BEFORE_A_PREDICTION = 28  # what version B may search when predicting a range


class VersionResult(BaseModel):
    version: Version
    document: str
    topics: list[NamedTopic]
    predicted: list[PredictedTopic]
    prediction_reasoning: str
    scores: Scores
    report_matches: dict[str, int | None]  # each named topic to the real topic it matched
    prediction_matches: dict[str, int | None]
    tool_calls: int
    posts_seen: list[str]
    input_tokens: int
    output_tokens: int
    seconds: float


class RunResult(BaseModel):
    run_id: str
    start: date
    end: date
    model: str
    main_topics: list[KeyTopic]
    instructions: dict[str, str]  # each task's words, identical for both versions
    versions: list[VersionResult]


class Embedder(QueryEmbedder, ComparisonEmbedder, Protocol): ...


class RunData(TopicData, ReportStore, Protocol): ...


@dataclass(frozen=True)
class RunParts:
    """What a run works with: the model, our data, and the embedder."""

    model: ChatModel
    model_name: str
    data: RunData
    embedder: Embedder


Parallel = Callable[
    [Callable[[Version], VersionResult], Iterable[Version]], Iterator[VersionResult]
]


class ComparisonRun:
    def __init__(self, parts: RunParts, emit: Emit, parallel: Parallel = map):
        self.parts = parts
        self.emit = emit
        self.parallel = parallel

    def run(self, run_id: str, days: DayRange) -> RunResult:
        self.emit("run.started", start=days.start, end=days.end, model=self.parts.model_name)
        one_run = _OneRun(self.parts, run_id, days)
        versions = list(self.parallel(lambda v: one_run.version(v, self.emit), VERSIONS))
        self._announce_measurements(versions)
        self.emit("run.finished")
        return RunResult(
            run_id=run_id,
            start=days.start,
            end=days.end,
            model=self.parts.model_name,
            main_topics=main_topics(one_run.active),
            instructions={t.phase: t.instructions for t in (write_task(days), predict_task(days))},
            versions=versions,
        )

    def _announce_measurements(self, versions: list[VersionResult]) -> None:
        by_version = {v.version: v.scores.model_dump() for v in versions}
        for name in Scores.model_fields:
            self.emit("measurement.done", name=name, **{v: s[name] for v, s in by_version.items()})


class _OneRun:
    """One run's range and answer key, shared by both versions."""

    def __init__(self, parts: RunParts, run_id: str, days: DayRange):
        self.parts = parts
        self.run_name = f"report-{run_id}"  # how its retrievals are counted (atlas OPEN-12)
        self.days = days
        self.active = active_topics(parts.data, days)

    def version(self, version: Version, emit: Emit) -> VersionResult:
        emit = _for_version(emit, version)
        tools = self._tools_for if version == "B" else _no_tools
        written = self._phase(write_task(self.days), tools("write"), emit)
        predicted = self._phase(predict_task(self.days), tools("predict"), emit)
        report: Report = written.answer  # type: ignore[assignment]
        prediction: Prediction = predicted.answer  # type: ignore[assignment]
        marking, scores = self._marked(
            Commitment(topics=report.topics, predicted=[]),
            Commitment(topics=[], predicted=prediction.predicted),
        )
        return _version_result(
            version, (report, prediction), (scores, marking), (written, predicted)
        )

    def _phase(self, task: Task, tools: ReportTools | None, emit: Emit) -> Written:
        emit("step.started", phase=task.phase)
        written = ReportWriter(self.parts.model, tools, emit).write(task)
        emit(
            "step.finished",
            phase=task.phase,
            seconds=written.seconds,
            tool_calls=written.tool_calls,
        )
        emit(
            "usage",
            phase=task.phase,
            input_tokens=written.input_tokens,
            output_tokens=written.output_tokens,
        )
        return written

    def _tools_for(self, phase: str) -> ReportTools:
        """The report sees its own range; the prediction only the days before it (OPEN-22)."""
        data, embedder = self.parts.data, self.parts.embedder
        if phase == "write":
            measured = lambda: [t.model_dump() for t in topics_in_range(data, self.days)]  # noqa: E731
            return ReportTools(data, embedder, self.days, self.run_name, measured)
        projected = lambda: [t.model_dump() for t in topic_trends(data, self.days)]  # noqa: E731
        return ReportTools(data, embedder, _days_before(self.days), self.run_name, projected)

    def _marked(self, report: Commitment, prediction: Commitment) -> tuple[Marking, Scores]:
        marking = mark(self.active, report, prediction, self.parts.embedder)
        return marking, score(report, prediction, marking)


def _no_tools(_phase: str) -> None:
    """Version A: the model on its own, with no way to reach our store (CLAUDE.md §7)."""
    return None


def _days_before(days: DayRange) -> DayRange:
    last = days.start - timedelta(days=1)
    return DayRange(last - timedelta(days=DAYS_SEEN_BEFORE_A_PREDICTION - 1), last)


def _version_result(
    version: Version,
    answers: tuple[Report, Prediction],
    marked: tuple[Scores, Marking],
    calls: tuple[Written, Written],
) -> VersionResult:
    report, prediction = answers
    scores, marking = marked
    return VersionResult(
        version=version,
        document=report.document,
        topics=report.topics,
        predicted=prediction.predicted,
        prediction_reasoning=prediction.reasoning,
        scores=scores,
        report_matches=marking.report_matches,
        prediction_matches=marking.prediction_matches,
        tool_calls=sum(c.tool_calls for c in calls),
        posts_seen=list(dict.fromkeys(p for c in calls for p in c.posts_seen)),
        input_tokens=sum(c.input_tokens for c in calls),
        output_tokens=sum(c.output_tokens for c in calls),
        seconds=round(sum(c.seconds for c in calls), 1),
    )


def _for_version(emit: Emit, version: Version) -> Emit:
    def emit_for_version(event_type: str, **body: object) -> None:
        emit(event_type, version=version, **body)

    return emit_for_version
