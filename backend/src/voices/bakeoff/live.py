"""The bake-off against the real models: a sample, the real embedding model, and
the chat models through OpenRouter with the key from the settings."""

from functools import partial

from voices.bakeoff.runner import ModelResult, run_bakeoff
from voices.bakeoff.sample import SampleData
from voices.bakeoff.sample_store import SampleStore
from voices.config import load_settings
from voices.ingestion.embedder import load_embedder
from voices.tagging.model import connect_model


def run_live_bakeoff(model_names: list[str], sample: SampleData) -> list[ModelResult]:
    settings = load_settings()
    store = SampleStore(sample, load_embedder(settings.model_dir))
    return run_bakeoff(model_names, store, partial(connect_model, settings.openrouter_api_key))
