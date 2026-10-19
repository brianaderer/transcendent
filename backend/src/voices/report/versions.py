"""The comparison's two versions (atlas plate 70): A, the model reading a few posts with no
retrieval by meaning, and B, the model with tools that search our store (OPEN-39)."""

from typing import Literal

Version = Literal["A", "B"]
VERSIONS: tuple[Version, ...] = ("A", "B")
