"""Calls the real model and spends money, so it never runs with the other tests:
docker compose run --rm api pytest -m bakeoff"""

from datetime import date

import pytest

from voices.bakeoff.live import run_live_bakeoff
from voices.bakeoff.report import render_report
from voices.bakeoff.sample import load_sample_data
from voices.config import load_settings

pytestmark = pytest.mark.bakeoff

FLOOR = 0.8  # proposed in atlas plate 60: eight cases in ten


def test_the_configured_tagging_model_gets_at_least_eight_cases_in_ten_right():
    sample = load_sample_data()

    [result] = run_live_bakeoff([load_settings().tagging_model_name], sample)

    assert result.share_right >= FLOOR, render_report([result], sample, date.today())
