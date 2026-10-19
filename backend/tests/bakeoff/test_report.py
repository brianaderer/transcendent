from datetime import date

from tests.bakeoff.stand_ins import Answers, always_attaches_to_theft
from voices.bakeoff.report import render_report
from voices.bakeoff.runner import run_bakeoff
from voices.bakeoff.sample import Case
from voices.bakeoff.sample_store import SampleStore


def test_the_report_shows_each_model_its_score_and_every_case(sample, embedder):
    store = SampleStore(sample, embedder)
    names = ["anthropic/claude-haiku-5.5", "anthropic/claude-sonnet-5.5"]
    results = run_bakeoff(names, store, lambda name: always_attaches_to_theft())

    page = render_report(results, sample, date(2026, 10, 18))

    assert "anthropic/claude-sonnet-5.5" in page and "2026-10-18" in page
    assert "1 of 2 (50%)" in page
    assert "| theft | attach: Stolen boats |" in page


def page_for_one_more_case(sample, embedder, case, model):
    sample.cases.append(case)
    store = SampleStore(sample, embedder)
    results = run_bakeoff(["anthropic/claude-haiku-5.5"], store, lambda name: model)
    return render_report(results, sample, date(2026, 10, 18))


def test_a_minted_answer_shows_the_label_it_mints(sample, embedder):
    case = Case("new-subject", ["t3"], "mint", None)

    page = page_for_one_more_case(sample, embedder, case, Answers(action="mint", label="Docking"))

    assert "| new-subject | mint | ✓ mint: Docking |" in page


def test_a_noise_case_shows_noise_as_its_right_answer(sample, embedder):
    page = page_for_one_more_case(
        sample, embedder, Case("chatter", ["t2"], "noise", None), Answers(action="noise")
    )

    assert "| chatter | noise | ✓ noise |" in page


def test_a_bar_in_an_answer_cannot_break_the_table(sample, embedder):
    model = Answers(action="mint", label="Docking | mooring")

    page = page_for_one_more_case(sample, embedder, Case("bar", ["t3"], "mint", None), model)

    assert "✓ mint: Docking / mooring |" in page
