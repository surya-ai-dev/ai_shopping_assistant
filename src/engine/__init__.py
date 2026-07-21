"""Engine package init."""

from src.engine.deduplication import DuplicateDetector
from src.engine.pipeline import ScrapePipeline
from src.engine.queue import AsyncURLQueue
from src.engine.registry import CollectorRegistry
from src.engine.worker import WorkerPool

__all__ = [
    "AsyncURLQueue",
    "CollectorRegistry",
    "DuplicateDetector",
    "ScrapePipeline",
    "WorkerPool",
]
