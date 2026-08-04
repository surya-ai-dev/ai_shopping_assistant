"""Conflict resolution component for sorting and selecting user query intents."""

from src.ai_agents.enums.intent import IntentEnum
from src.ai_agents.intent.constants import INTENT_PRIORITIES, THRESHOLD_MEDIUM
from src.ai_agents.intent.result import DetectorResult


class ConflictResolver:
    """Resolves classification overlap by evaluating intent priorities and confidence thresholds."""

    def resolve(self, results: list[DetectorResult]) -> tuple[IntentEnum, float, list[IntentEnum]]:
        """Sorts detector matches to select the primary intent and secondary intents.

        Args:
            results: list of raw classification results from all detectors.

        Returns:
            A tuple of (primary_intent, confidence, secondary_intents).
        """
        # Filter only matched detectors
        matches = [r for r in results if r.matched]

        if not matches:
            return IntentEnum.UNSUPPORTED, 0.0, []

        # Sort matches: priority descending, confidence descending
        matches.sort(
            key=lambda r: (INTENT_PRIORITIES.get(r.intent, 0), r.confidence),
            reverse=True,
        )

        primary_match = matches[0]

        # Low-confidence classifications automatically fall back to UNSUPPORTED (Unknown)
        if primary_match.confidence < THRESHOLD_MEDIUM:
            primary_intent = IntentEnum.UNSUPPORTED
            primary_confidence = primary_match.confidence
        else:
            primary_intent = primary_match.intent
            primary_confidence = primary_match.confidence

        # Secondary intents: other matched intents
        secondary_intents: list[IntentEnum] = []
        for r in matches:
            if r.intent != primary_intent and r.intent not in secondary_intents:
                secondary_intents.append(r.intent)

        return primary_intent, primary_confidence, secondary_intents
