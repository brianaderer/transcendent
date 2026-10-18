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
# Memory grows with batch size times the longest text in the batch; 8 keeps a day of posts
# under about 2 GB, where the library's default of 256 runs a laptop's Docker out of memory.
EMBED_BATCH_SIZE = 8


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
        """Embeds texts shortest first, so each batch pads to a similar length, then puts the
        results back in the order the texts came in."""
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
        prompts = [purpose + texts[i] for i in order]
        vectors = self.model.embed(prompts, batch_size=EMBED_BATCH_SIZE)
        by_position = dict(zip(order, vectors, strict=True))
        return [list(map(float, by_position[i])) for i in range(len(texts))]


def load_embedder(cache_dir: str) -> NomicEmbedder:
    """Loads the model, downloading it into the cache volume the first time."""
    from fastembed import TextEmbedding  # imported here: loading it is slow and tests don't need it

    return NomicEmbedder(TextEmbedding(MODEL_NAME, cache_dir=cache_dir))
