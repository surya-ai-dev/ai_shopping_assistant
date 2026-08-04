"""Intent Classifier coordinating detectors execution, conflict resolution, and entity extraction."""

from src.ai_agents.intent.confidence import ConfidenceCalculator
from src.ai_agents.intent.conflict_resolver import ConflictResolver
from src.ai_agents.intent.entity_extractor import EntityExtractor
from src.ai_agents.intent.registry import DetectorRegistry
from src.ai_agents.intent.result import IntentResult


class IntentClassifier:
    """Orchestrates detectors, resolves overlap conflicts, and calculates classification confidence."""

    def __init__(
        self,
        registry: DetectorRegistry | None = None,
        conflict_resolver: ConflictResolver | None = None,
        entity_extractor: EntityExtractor | None = None,
        confidence_calculator: ConfidenceCalculator | None = None,
    ) -> None:
        """Initialize the IntentClassifier with injected components.

        Args:
            registry: Detector list supplier.
            conflict_resolver: Conflict sorting component.
            entity_extractor: Specification parsing component.
            confidence_calculator: Scoring normalization component.
        """
        self._registry = registry or DetectorRegistry()
        self._resolver = conflict_resolver or ConflictResolver()
        self._extractor = entity_extractor or EntityExtractor()
        self._confidence_calculator = confidence_calculator or ConfidenceCalculator()

    def classify(self, query: str) -> IntentResult:
        """Classify user query and extract matching entities.

        Args:
            query: User input query.

        Returns:
            IntentResult schema matching Phase 8.1 structure.
        """
        detectors = self._registry.get_detectors()
        detector_results = []

        # 1. Execute all detectors
        for detector in detectors:
            res = detector.detect(query)
            detector_results.append(res)

        # 2. Invoke ConflictResolver to decide primary and secondary intents
        primary_intent, base_conf, secondary_intents = self._resolver.resolve(detector_results)

        # 3. Invoke EntityExtractor
        entities = self._extractor.extract(query)

        # Get matched keywords from selected primary detector
        primary_keywords = []
        for r in detector_results:
            if r.intent == primary_intent and r.matched:
                primary_keywords = r.matched_keywords
                break

        # 4. Invoke ConfidenceCalculator
        has_category = "category" in entities
        normalized_confidence = self._confidence_calculator.calculate(
            base_confidence=base_conf,
            matched_keywords=primary_keywords,
            entities=entities,
            has_category=has_category,
        )

        # Build telemetry/metadata to assign secondary intents
        metadata = {
            "secondary_intents": [i.value for i in secondary_intents],
            "entities_extracted": list(entities.keys()),
        }

        # Embed metadata info inside entities or return clean IntentResult
        # IntentResult (Phase 8.1) has: primary_intent, confidence, entities.
        # We can write secondary intents list into entities["secondary_intents"]
        if secondary_intents:
            entities["secondary_intents"] = [i.value for i in secondary_intents]

        # Ensure we also store debug info inside metadata block of entities
        entities["_metadata"] = metadata

        return IntentResult(
            primary_intent=primary_intent,
            confidence=normalized_confidence,
            entities=entities,
        )
