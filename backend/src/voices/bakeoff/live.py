"""The bake-off against the real models: the committed sample, the real embedding model, and
the chat models through OpenRouter with the key from the settings."""

from functools import partial

from voices.bakeoff.runner import ModelResult, run_bakeoff
from voices.bakeoff.sample import load_sample_data
from voices.bakeoff.sample_store import SampleStore
from voices.config import load_settings
from voices.ingestion.embedder import load_embedder
from voices.tagging.model import connect_model


def run_live_bakeoff(model_names: list[str]) -> list[ModelResult]:
    settings = load_settings()
    store = SampleStore(load_sample_data(), load_embedder(settings.model_dir))
    return run_bakeoff(model_names, store, partial(connect_model, settings.openrouter_api_key))
