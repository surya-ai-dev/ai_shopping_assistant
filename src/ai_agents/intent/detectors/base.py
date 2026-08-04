"""Base protocol interface for all Intent Detectors."""

from typing import Protocol

from src.ai_agents.intent.result import DetectorResult


class IntentDetector(Protocol):
    """Protocol defining the interface that all intent detectors must implement."""

    @property
    def name(self) -> str:
        """The developer name of the detector (e.g. ComparisonDetector)."""
        ...

    @property
    def version(self) -> str:
        """SemVer identifier tracking changes to this detector."""
        ...

    def detect(self, query: str) -> DetectorResult:
        """Exhaustively checks if the user's query matches the target intent.

        Args:
            query: The normalized user query string.

        Returns:
            A DetectorResult containing match status, confidence, and telemetry.
        """
        ...
