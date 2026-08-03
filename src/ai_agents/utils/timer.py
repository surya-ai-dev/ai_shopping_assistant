"""Timer utility context manager to trace step execution latency."""

import time
from types import TracebackType


class Timer:
    """Context manager to measure execution time in milliseconds.

    Attributes:
        start_time: Host tick timestamp execution started.
        end_time: Host tick timestamp execution completed.
        elapsed_ms: Calculated execution duration in milliseconds.
    """

    def __init__(self) -> None:
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> "Timer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.end_time = time.perf_counter()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000.0
