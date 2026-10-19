"""Calls the real model and spends money, so it never runs with the other tests:
docker compose run --rm api pytest -m bakeoff"""

from datetime import date
from functools import partial

import pytest

from voices.bakeoff.report import render_report
from voices.bakeoff.runner import run_bakeoff
from voices.bakeoff.sample import load_sample_data
from voices.bakeoff.sample_store import SampleStore
from voices.config import load_settings
from voices.ingestion.embedder import load_embedder
from voices.tagging.model import connect_model

pytestmark = pytest.mark.bakeoff

FLOOR = 0.8  # proposed in atlas plate 60: eight cases in ten


def test_the_configured_tagging_model_gets_at_least_eight_cases_in_ten_right():
    settings = load_settings()
    embedder = load_embedder(settings.model_dir)
    store = SampleStore(load_sample_data(), embedder)
    connect = partial(connect_model, settings.openrouter_api_key)

    [result] = run_bakeoff([settings.tagging_model_name], store, embedder, connect)

    assert result.share_right >= FLOOR, render_report([result], store.sample, date.today())
