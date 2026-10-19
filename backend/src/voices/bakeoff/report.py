"""The bake-off's results page, in markdown: a summary per model, then every case."""

from datetime import date

from voices.bakeoff.runner import CaseResult, ModelResult
from voices.bakeoff.sample import CASES_FILE, Case, SampleData
from voices.bakeoff.scoring import Verdict

MISTAKES = [verdict for verdict in Verdict if verdict is not Verdict.RIGHT]


def render_report(results: list[ModelResult], sample: SampleData, run_on: date) -> str:
    return "\n".join(
        [
            "# Tagging model bake-off",
            "",
            f"Run on {run_on.isoformat()}: {len(sample.cases)} cases from "
            f"`backend/src/voices/bakeoff/{CASES_FILE.name}`, each decided once by each model "
            "through the production tagging decision (atlas plate 60). Cost is at OpenRouter's "
            "listed prices (`voices/bakeoff/pricing.py`).",
            "",
            *_summary(results),
            "",
            "## Case by case",
            "",
            *_case_table(results, sample),
            "",
        ]
    )


def _summary(results: list[ModelResult]) -> list[str]:
    rows = [
        ("Right", lambda r: f"{r.right} of {len(r.cases)} ({r.share_right:.0%})"),
        *[(verdict.capitalize(), _counter(verdict)) for verdict in MISTAKES],
        ("Look-ups per decision", lambda r: f"{r.mean(lambda c: c.meter.look_ups):.1f}"),
        ("Model calls per decision", lambda r: f"{r.mean(lambda c: c.meter.model_calls):.1f}"),
        ("Seconds per decision", lambda r: f"{r.mean(lambda c: c.seconds):.1f}"),
        ("Tokens read, written", lambda r: f"{r.tokens_in:,}, {r.tokens_out:,}"),
        ("Cost of the run", lambda r: f"${r.cost:.4f}"),
    ]
    return _table(
        ["", *(r.model_name for r in results)],
        [[label, *(measure(r) for r in results)] for label, measure in rows],
    )


def _counter(verdict: Verdict):
    return lambda result: str(result.count(verdict))


def _case_table(results: list[ModelResult], sample: SampleData) -> list[str]:
    header = ["Case", "Right answer", *(r.model_name for r in results)]
    rows = [
        [case.name, right_answer(case, sample), *(_marked(r.cases[n]) for r in results)]
        for n, case in enumerate(sample.cases)
    ]
    return _table(header, rows)


def right_answer(case: Case, sample: SampleData) -> str:
    if case.expected == "attach":
        labels = {topic.topic_id: topic.label for topic in sample.topics}
        return f"attach: {labels[case.topic_id]}"
    return case.expected


def _marked(result: CaseResult) -> str:
    mark = "✓" if result.verdict is Verdict.RIGHT else "✗"
    return f"{mark} {result.answer}".replace("|", "/")


def _table(header: list[str], rows: list[list[str]]) -> list[str]:
    lines = [header, ["---"] * len(header), *rows]
    return ["| " + " | ".join(cells) + " |" for cells in lines]
