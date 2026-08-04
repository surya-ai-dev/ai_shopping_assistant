"""Detector checking for product search intent."""

import re
import time

from src.ai_agents.enums.intent import IntentEnum
from src.ai_agents.intent.constants import SEARCH_KEYWORDS
from src.ai_agents.intent.result import DetectorResult


class SearchDetector:
    """Detector identifying when users want to search for laptops or mobile phones."""

    @property
    def name(self) -> str:
        """The name of the detector."""
        return "SearchDetector"

    @property
    def version(self) -> str:
        """SemVer identifier for this detector version."""
        return "1.0.0"

    def detect(self, query: str) -> DetectorResult:
        """Detect product search requests.

        Args:
            query: Normalized user input query.

        Returns:
            DetectorResult indicating match status and confidence.
        """
        start_time = time.perf_counter()
        lowered_query = query.lower()
        matched_keywords: list[str] = []

        # Scan for word boundary matches on search keywords
        for kw in SEARCH_KEYWORDS:
            pattern = rf"\b{re.escape(kw)}\b"
            if re.search(pattern, lowered_query):
                matched_keywords.append(kw)

        matched = len(matched_keywords) > 0
        confidence = 0.0
        if matched:
            confidence = min(0.80 + (0.05 * len(matched_keywords)), 1.0)

        execution_time_ms = (time.perf_counter() - start_time) * 1000.0

        return DetectorResult(
            matched=matched,
            confidence=confidence,
            intent=IntentEnum.SEARCH_PRODUCT,
            detector_name=self.name,
            detector_version=self.version,
            execution_time_ms=execution_time_ms,
            matched_keywords=matched_keywords,
        )
