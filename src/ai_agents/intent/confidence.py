from typing import Any, Final

MIN_CONFIDENCE_EARLY_RETURN_THRESHOLD: Final[float] = 0.10


class ConfidenceCalculator:
    """Combines raw detector confidence with matching density metrics to output a normalized score."""

    def calculate(
        self,
        base_confidence: float,
        matched_keywords: list[str],
        entities: dict[str, Any],
        has_category: bool,
    ) -> float:
        """Calculates normalized classification confidence between 0.0 and 1.0.

        Args:
            base_confidence: Raw confidence from the selected detector.
            matched_keywords: Match list from the selected detector.
            entities: Parsed query entities.
            has_category: True if a supported category was extracted.

        Returns:
            A float score capped between 0.0 and 1.0.
        """
        if base_confidence <= MIN_CONFIDENCE_EARLY_RETURN_THRESHOLD:
            return base_confidence

        score = base_confidence

        # Apply keyword density bonus (up to 0.15)
        keyword_bonus = min(0.05 * len(matched_keywords), 0.15)
        score += keyword_bonus

        # Apply entity density bonus (up to 0.15)
        entity_bonus = min(0.05 * len(entities), 0.15)
        score += entity_bonus

        # Apply category domain certainty bonus
        if has_category:
            score += 0.05

        # Bound output between 0.0 and 1.0
        return min(max(score, 0.0), 1.0)
