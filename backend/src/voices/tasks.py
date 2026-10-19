"""How the API hands a job to the worker without importing the worker's code."""

from collections.abc import Callable

Queue = Callable[[str, list[str]], object]  # a task's name and its arguments
