"""Type definitions and aliases for the AI Agents platform."""

from collections.abc import Callable, Coroutine
from typing import Any

# Common dictionary types for JSON and payload values
JSONDict = dict[str, Any]
MetadataDict = dict[str, Any]

# Async callable function signature type (e.g. for tools or pipeline execution)
AsyncFunc = Callable[..., Coroutine[Any, Any, Any]]
