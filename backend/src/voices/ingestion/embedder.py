"""Turns text into embeddings with nomic-embed-text, run inside the container (atlas OPEN-5).

nomic-embed-text is trained with a short instruction in front of each text saying what the
embedding is for; using the right one keeps searches and comparisons accurate.
"""

from collections.abc import Iterable, Sequence
from typing import Protocol

MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5-Q"  # the compact build: same 768 numbers, 130 MB
DOCUMENT = "search_document: "
QUERY = "search_query: "
COMPARISON = "classification: "
# The model's working memory grows with batch size times the square of the longest text, and
# the library keeps its high point. Batches capped by total characters keep the worker under
# 1 GB over many days (measured: fixed batches of 8 climbed past 3.7 GB, and 8 GB in a boot
# test); short comments still go 32 at a time, which is faster too.
BATCH_TEXT_BUDGET = 4000
MAX_BATCH = 32


class TextModel(Protocol):
    def embed(self, texts: list[str], batch_size: int) -> Iterable[Sequence[float]]: ...


class NomicEmbedder:
    def __init__(self, model: TextModel):
        self.model = model

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed(DOCUMENT, texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed(QUERY, [text])[0]

    def embed_for_comparison(self, texts: Sequence[str]) -> list[list[float]]:
        return self._embed(COMPARISON, texts)

    def _embed(self, purpose: str, texts: Sequence[str]) -> list[list[float]]:
        """Embeds texts shortest first in batches sized by length, then puts the results back
        in the order the texts came in."""
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
        prompts = [purpose + texts[i] for i in order]
        vectors = [v for batch in _batches(prompts) for v in self.model.embed(batch, len(batch))]
        by_position = dict(zip(order, vectors, strict=True))
        return [list(map(float, by_position[i])) for i in range(len(texts))]


def _batches(prompts: list[str]) -> list[list[str]]:
    """Consecutive groups holding at most BATCH_TEXT_BUDGET characters and MAX_BATCH texts; a
    single text longer than the budget goes alone."""
    batches: list[list[str]] = [[]]
    for prompt in prompts:
        current = batches[-1]
        if current and (
            len(current) == MAX_BATCH or _size(current) + len(prompt) > BATCH_TEXT_BUDGET
        ):
            batches.append(current := [])
        current.append(prompt)
    return [batch for batch in batches if batch]


def _size(batch: list[str]) -> int:
    return sum(len(text) for text in batch)


def load_embedder(cache_dir: str) -> NomicEmbedder:
    """Loads the model, downloading it into the cache volume the first time."""
    from fastembed import TextEmbedding  # imported here: loading it is slow and tests don't need it

    return NomicEmbedder(TextEmbedding(MODEL_NAME, cache_dir=cache_dir))
