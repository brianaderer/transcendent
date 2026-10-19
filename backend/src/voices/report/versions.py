"""The comparison's two versions (atlas plate 70): A, the model on its own, and B, the model
with tools that read our store."""

from typing import Literal

Version = Literal["A", "B"]
VERSIONS: tuple[Version, ...] = ("A", "B")
