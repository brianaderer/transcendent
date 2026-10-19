"""Squashes posts' embeddings to two dimensions for the dot plot (atlas OPEN-20, plate 31)."""

from collections.abc import Sequence

import numpy as np
from sklearn.manifold import TSNE

SEED = 0  # the same posts always give the same map
LARGEST_PERPLEXITY = 30  # how many neighbours each post weighs; scikit-learn's default
FEWEST_FOR_TSNE = 5  # below this t-SNE has too few neighbours, so the posts are laid in a row

Point = tuple[float, float]


def flatten(vectors: Sequence[Sequence[float]]) -> list[Point]:
    """One point per vector, posts close in meaning close together, fitted into the square
    from -1 to 1."""
    if not vectors:
        return []
    data = np.asarray(vectors, dtype=np.float32)
    points = _in_a_row(len(data)) if len(data) < FEWEST_FOR_TSNE else _tsne(data)
    return [(float(x), float(y)) for x, y in _fitted_to_unit_square(points)]


def _tsne(data: np.ndarray) -> np.ndarray:
    perplexity = min(LARGEST_PERPLEXITY, (len(data) - 1) / 3)
    model = TSNE(2, perplexity=perplexity, metric="cosine", init="pca", random_state=SEED)
    return model.fit_transform(data)


def _in_a_row(count: int) -> np.ndarray:
    return np.column_stack([np.arange(count, dtype=float), np.zeros(count)])


def _fitted_to_unit_square(points: np.ndarray) -> np.ndarray:
    centred = points - points.mean(axis=0)
    largest = np.abs(centred).max()
    return centred / largest if largest else centred
