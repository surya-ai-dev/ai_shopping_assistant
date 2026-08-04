"""Detector checking for best product searches."""

import re
import time

from src.ai_agents.enums.intent import IntentEnum
from src.ai_agents.intent.constants import BEST_PRODUCT_KEYWORDS
from src.ai_agents.intent.result import DetectorResult


class BestProductDetector:
    """Detector identifying when users look for the 'best' or 'top' products."""

    @property
    def name(self) -> str:
        """The name of the detector."""
        return "BestProductDetector"

    @property
    def version(self) -> str:
        """SemVer identifier for this detector version."""
        return "1.0.0"

    def detect(self, query: str) -> DetectorResult:
        """Detect best product requests.

        Args:
            query: Normalized user input query.

        Returns:
            DetectorResult indicating match status and confidence.
        """
        start_time = time.perf_counter()
        lowered_query = query.lower()
        matched_keywords: list[str] = []

        # Scan for word boundary matches on best keywords
        for kw in BEST_PRODUCT_KEYWORDS:
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
            intent=IntentEnum.BEST_PRODUCT,
            detector_name=self.name,
            detector_version=self.version,
            execution_time_ms=execution_time_ms,
            matched_keywords=matched_keywords,
        )
