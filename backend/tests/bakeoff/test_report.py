from datetime import date

from tests.bakeoff.stand_ins import AlwaysAttachesToTheft, Answers
from voices.bakeoff.report import render_report
from voices.bakeoff.runner import run_bakeoff
from voices.bakeoff.sample import Case
from voices.bakeoff.sample_store import SampleStore


def test_the_report_shows_each_model_its_score_and_every_case(sample, embedder):
    store = SampleStore(sample, embedder)
    names = ["anthropic/claude-haiku-5.5", "anthropic/claude-sonnet-5.5"]
    results = run_bakeoff(names, store, lambda name: AlwaysAttachesToTheft())

    page = render_report(results, sample, date(2026, 10, 18))

    assert "anthropic/claude-sonnet-5.5" in page and "2026-10-18" in page
    assert "1 of 2 (50%)" in page
    assert "| theft | attach: Stolen boats |" in page


def test_cases_that_mint_or_are_noise_show_their_action_and_bars_cannot_break_the_table(
    sample, embedder
):
    sample.cases.append(Case("new-subject", ["t3"], "mint", None))
    store = SampleStore(sample, embedder)
    model = Answers(action="mint", label="Docking | mooring")
    results = run_bakeoff(["anthropic/claude-haiku-5.5"], store, lambda name: model)

    page = render_report(results, sample, date(2026, 10, 18))

    assert "| new-subject | mint | ✓ mint: Docking / mooring |" in page
