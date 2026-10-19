"""Finds short replies that only agree with their parent, like "+1" or "same here".

They aren't stored; each one counts as an upvote for the post it replies to (atlas OPEN-19).
"""

import math
from collections.abc import Sequence

from voices.ingestion.embedder import ComparisonEmbedder

MAX_AGREEMENT_WORDS = 8
AGREEMENT_SIMILARITY = 0.80  # to be tuned against real r/sailing replies
AGREEMENT_EXAMPLES = [
    "+1",
    "this",
    "same here",
    "agreed",
    "exactly",
    "so true",
    "I agree",
    "came here to say this",
    "100% this",
    "yes, this",
    "this is the answer",
    "good point",
    "well said",
    "nice summary",
]


class AgreementDetector:
    def __init__(self, embedder: ComparisonEmbedder):
        self.embedder = embedder
        self.examples = embedder.embed_for_comparison(AGREEMENT_EXAMPLES)

    def agreeing(self, texts: Sequence[str]) -> list[bool]:
        """For each reply, whether it only agrees with what it replies to."""
        short = [_could_be_agreement(text) for text in texts]
        candidates = [text for text, is_short in zip(texts, short, strict=True) if is_short]
        meanings = iter(self.embedder.embed_for_comparison(candidates) if candidates else [])
        return [is_short and self._means_agreement(next(meanings)) for is_short in short]

    def _means_agreement(self, meaning: list[float]) -> bool:
        return max(_cosine(meaning, example) for example in self.examples) >= AGREEMENT_SIMILARITY


def _could_be_agreement(text: str) -> bool:
    asks_or_links = "?" in text or "http" in text
    return not asks_or_links and len(text.split()) <= MAX_AGREEMENT_WORDS


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    size = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / size if size else 0.0
