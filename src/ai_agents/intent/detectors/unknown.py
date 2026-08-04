"""Fallback detector checking for unknown/unsupported intents and general greetings."""

import re
import time
from typing import Final

from src.ai_agents.enums.intent import IntentEnum
from src.ai_agents.intent.constants import GREETING_KEYWORDS
from src.ai_agents.intent.result import DetectorResult

GREETING_CONFIDENCE: Final[float] = 0.90
UNSUPPORTED_CONFIDENCE: Final[float] = 0.10



class UnknownDetector:
    """Fallback detector that matches greetings and general unsupported inputs."""

    @property
    def name(self) -> str:
        """The name of the detector."""
        return "UnknownDetector"

    @property
    def version(self) -> str:
        """SemVer identifier for this detector version."""
        return "1.0.0"

    def detect(self, query: str) -> DetectorResult:
        """Scan query for greetings, falling back to unsupported intent.

        Args:
            query: User input query.

        Returns:
            DetectorResult indicating greeting or unsupported fallback.
        """
        start_time = time.perf_counter()
        lowered_query = query.lower()
        matched_keywords: list[str] = []

        # Check for greeting keywords
        for kw in GREETING_KEYWORDS:
            pattern = rf"\b{re.escape(kw)}\b"
            if re.search(pattern, lowered_query):
                matched_keywords.append(kw)

        matched = len(matched_keywords) > 0
        if matched:
            intent = IntentEnum.GENERAL_GREETING
            confidence = GREETING_CONFIDENCE
        else:
            intent = IntentEnum.UNSUPPORTED
            confidence = UNSUPPORTED_CONFIDENCE

        execution_time_ms = (time.perf_counter() - start_time) * 1000.0

        return DetectorResult(
            matched=True,
            confidence=confidence,
            intent=intent,
            detector_name=self.name,
            detector_version=self.version,
            execution_time_ms=execution_time_ms,
            matched_keywords=matched_keywords,
        )
