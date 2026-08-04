"""Result schemas and dataclasses for the Intent Classification Layer."""

from dataclasses import dataclass, field
from typing import Any

from src.ai_agents.enums.intent import IntentEnum
from src.ai_agents.schemas.intent import IntentResult

__all__ = [
    "DetectorResult",
    "IntentResult",
]



@dataclass
class DetectorResult:
    """The raw classification result returned by an individual intent detector."""

    matched: bool
    confidence: float
    intent: IntentEnum
    detector_name: str
    detector_version: str
    execution_time_ms: float
    matched_keywords: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
