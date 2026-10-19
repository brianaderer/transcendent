"""python -m voices.bakeoff [model ...] runs the bake-off and prints the results page.

With no models named it compares Claude Haiku 5.5 and Claude Sonnet 5.5. It calls the real
models through OpenRouter, so it needs OPENROUTER_API_KEY and spends money (about $1).
"""

import sys
from datetime import date
from functools import partial

from voices.bakeoff.report import render_report
from voices.bakeoff.runner import run_bakeoff
from voices.bakeoff.sample import load_sample_data
from voices.bakeoff.sample_store import SampleStore
from voices.config import load_settings
from voices.ingestion.embedder import load_embedder
from voices.tagging.model import connect_model

DEFAULT_MODELS = ["anthropic/claude-haiku-5.5", "anthropic/claude-sonnet-5.5"]


def main(model_names: list[str]) -> None:
    settings = load_settings()
    embedder = load_embedder(settings.model_dir)
    store = SampleStore(load_sample_data(), embedder)
    connect = partial(connect_model, settings.openrouter_api_key)
    results = run_bakeoff(model_names, store, embedder, connect)
    print(render_report(results, store.sample, date.today()))


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT_MODELS)
