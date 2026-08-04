"""Intent Engine orchestrating classification pipelines, timings, and logging telemetry."""

import time
from typing import Any

from src.ai_agents.intent.classifier import IntentClassifier
from src.ai_agents.intent.result import IntentResult
from src.ai_agents.logging import get_ai_logger


class IntentEngine:
    """Main orchestrator for AI Intent Classification Layer (Phase 8.5)."""

    def __init__(self, classifier: IntentClassifier | None = None) -> None:
        """Initialize the IntentEngine.

        Args:
            classifier: Custom IntentClassifier instance. If None, uses default.
        """
        self._classifier = classifier or IntentClassifier()
        self._logger = get_ai_logger("IntentEngine")

    def classify_intent(self, query: str, metadata: dict[str, Any] | None = None) -> IntentResult:
        """Classify user query intent and parse context details.

        Args:
            query: User input query text.
            metadata: Timing and context correlation IDs.

        Returns:
            IntentResult containing primary intent, confidence, and entities.
        """
        start_time = time.perf_counter()

        meta_dict = metadata or {}
        correlation_id = (
            meta_dict.get("request_id")
            or meta_dict.get("trace_id")
            or "unknown_correlation_id"
        )

        try:
            # Execute classification
            result = self._classifier.classify(query)

            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # Log metrics without raw query text (privacy boundary check)
            self._logger.info(
                "Intent classification completed successfully",
                correlation_id=correlation_id,
                primary_intent=result.primary_intent.value,
                confidence=result.confidence,
                execution_time_ms=duration_ms,
            )

            return result

        except Exception as exc:
            self._logger.exception(
                "Failed to run intent classification engine",
                correlation_id=correlation_id,
            )
            raise exc
