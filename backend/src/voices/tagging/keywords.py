"""The words that most set one topic apart from the rest of the conversation (atlas plate 21)."""

import re
from collections import Counter
from collections.abc import Sequence

MIN_WORD_LENGTH = 4
COMMON_WORDS = {
    "about",
    "after",
    "again",
    "also",
    "been",
    "best",
    "boat",
    "could",
    "does",
    "from",
    "good",
    "have",
    "just",
    "know",
    "like",
    "looking",
    "make",
    "more",
    "much",
    "need",
    "only",
    "other",
    "really",
    "some",
    "than",
    "that",
    "their",
    "them",
    "then",
    "there",
    "they",
    "think",
    "this",
    "time",
    "tips",
    "very",
    "want",
    "were",
    "what",
    "when",
    "where",
    "which",
    "will",
    "with",
    "would",
    "your",
}


def distinctive_keywords(
    cluster_texts: Sequence[str], all_texts: Sequence[str], limit: int
) -> list[str]:
    """Words frequent in the cluster's texts and rare in all the texts, best first."""
    inside, everywhere = _word_counts(cluster_texts), _word_counts(all_texts)
    score = {word: count / everywhere[word] * count for word, count in inside.items()}
    return sorted(score, key=lambda word: (-score[word], word))[:limit]


def _word_counts(texts: Sequence[str]) -> Counter[str]:
    """In how many texts each meaningful word appears."""
    return Counter(word for text in texts for word in set(_words(text)))


def _words(text: str) -> list[str]:
    words = re.findall(r"[a-z][a-z0-9']+", text.lower())
    return [w for w in words if len(w) >= MIN_WORD_LENGTH and w not in COMMON_WORDS]
