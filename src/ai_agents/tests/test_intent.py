"""Unit tests for the AI Intent Classification Layer (Phase 8.5)."""


from src.ai_agents.enums.intent import IntentEnum
from src.ai_agents.intent import (
    ConfidenceCalculator,
    ConflictResolver,
    DetectorRegistry,
    DetectorResult,
    EntityExtractor,
    IntentClassifier,
    IntentEngine,
)


def test_detector_registry() -> None:
    """Verify that DetectorRegistry correctly orders, registers, and exposes detectors."""
    registry = DetectorRegistry()
    detectors = registry.get_detectors()

    assert len(detectors) >= 10
    assert detectors[0].name == "ComparisonDetector"
    assert detectors[-1].name == "UnknownDetector"

    # Verify custom registration keeps UnknownDetector last
    class DummyDetector:
        @property
        def name(self) -> str:
            return "DummyDetector"

        @property
        def version(self) -> str:
            return "1.0.0"

        def detect(self, query: str) -> DetectorResult:
            return DetectorResult(
                matched=False,
                confidence=0.0,
                intent=IntentEnum.UNSUPPORTED,
                detector_name=self.name,
                detector_version=self.version,
                execution_time_ms=0.0,
            )

    registry.register_detector(DummyDetector())
    new_detectors = registry.get_detectors()
    assert new_detectors[-2].name == "DummyDetector"
    assert new_detectors[-1].name == "UnknownDetector"


def test_comparison_detector() -> None:
    """Verify that ComparisonDetector matches vs, compare, and versus keywords."""
    registry = DetectorRegistry()
    detectors = {d.name: d for d in registry.get_detectors()}
    comp_detector = detectors["ComparisonDetector"]

    # Matched comparison query
    res = comp_detector.detect("Compare Dell XPS 13 vs MacBook Air")
    assert res.matched is True
    assert res.intent == IntentEnum.COMPARE_PRODUCTS
    assert res.confidence >= 0.80
    assert "vs" in res.matched_keywords or "compare" in res.matched_keywords

    # Non-matching
    res_no = comp_detector.detect("Best dell laptops in stock")
    assert res_no.matched is False
    assert res_no.confidence == 0.0


def test_recommendation_detector() -> None:
    """Verify that RecommendationDetector matches recommendation keywords."""
    registry = DetectorRegistry()
    detectors = {d.name: d for d in registry.get_detectors()}
    rec_detector = detectors["RecommendationDetector"]

    res = rec_detector.detect("recommend me a student laptop please")
    assert res.matched is True
    assert res.intent == IntentEnum.SHOPPING_ADVICE
    assert res.confidence >= 0.80

    res_no = rec_detector.detect("price of iphone 15")
    assert res_no.matched is False


def test_search_detector() -> None:
    """Verify that SearchDetector matches search queries."""
    registry = DetectorRegistry()
    detectors = {d.name: d for d in registry.get_detectors()}
    search_detector = detectors["SearchDetector"]

    res = search_detector.detect("show me dell laptops under $800")
    assert res.matched is True
    assert res.intent == IntentEnum.SEARCH_PRODUCT


def test_details_detector() -> None:
    """Verify that ProductDetailsDetector matches specs and info queries."""
    registry = DetectorRegistry()
    detectors = {d.name: d for d in registry.get_detectors()}
    details_detector = detectors["ProductDetailsDetector"]

    res = details_detector.detect("specification sheet of macbook air m3")
    assert res.matched is True
    assert res.intent == IntentEnum.PRODUCT_DETAILS


def test_price_detector() -> None:
    """Verify that PriceDetector identifies price drops and history dynamically."""
    registry = DetectorRegistry()
    detectors = {d.name: d for d in registry.get_detectors()}
    price_detector = detectors["PriceDetector"]

    # Price history query
    res_hist = price_detector.detect("show me the price history of galaxy s24")
    assert res_hist.matched is True
    assert res_hist.intent == IntentEnum.PRICE_HISTORY

    # Price drop query
    res_drop = price_detector.detect("is there any price drop or discount on iphone 15?")
    assert res_drop.matched is True
    assert res_drop.intent == IntentEnum.PRICE_DROP


def test_availability_detector() -> None:
    """Verify that AvailabilityDetector matches delivery and stock queries."""
    registry = DetectorRegistry()
    detectors = {d.name: d for d in registry.get_detectors()}
    availability_detector = detectors["AvailabilityDetector"]

    res = availability_detector.detect("is Dell XPS 15 in stock right now?")
    assert res.matched is True
    assert res.intent == IntentEnum.AVAILABILITY


def test_feature_detector() -> None:
    """Verify that FeatureDetector matches specific specs queries."""
    registry = DetectorRegistry()
    detectors = {d.name: d for d in registry.get_detectors()}
    feature_detector = detectors["FeatureDetector"]

    res = feature_detector.detect("how is the screen and battery life on zenbook?")
    assert res.matched is True
    assert res.intent == IntentEnum.FEATURE


def test_brand_detector() -> None:
    """Verify that BrandDetector matches brand names queries."""
    registry = DetectorRegistry()
    detectors = {d.name: d for d in registry.get_detectors()}
    brand_detector = detectors["BrandDetector"]

    res = brand_detector.detect("laptops from ASUS or Lenovo")
    assert res.matched is True
    assert res.intent == IntentEnum.BRAND


def test_best_product_detector() -> None:
    """Verify that BestProductDetector matches best product terms."""
    registry = DetectorRegistry()
    detectors = {d.name: d for d in registry.get_detectors()}
    best_detector = detectors["BestProductDetector"]

    res = best_detector.detect("greatest and best gaming laptop under 1000")
    assert res.matched is True
    assert res.intent == IntentEnum.BEST_PRODUCT


def test_unknown_detector() -> None:
    """Verify that UnknownDetector matches greetings and defaults as unsupported fallback."""
    registry = DetectorRegistry()
    detectors = {d.name: d for d in registry.get_detectors()}
    unknown_detector = detectors["UnknownDetector"]

    # Greetings check
    res_greet = unknown_detector.detect("Hello there, how are you?")
    assert res_greet.matched is True
    assert res_greet.intent == IntentEnum.GENERAL_GREETING
    assert res_greet.confidence == 0.90

    # General unknown check
    res_unsupported = unknown_detector.detect("blah blah widgets")
    assert res_unsupported.matched is True
    assert res_unsupported.intent == IntentEnum.UNSUPPORTED
    assert res_unsupported.confidence == 0.10


def test_conflict_resolver() -> None:
    """Verify that ConflictResolver sorts matches by priority and confidence, resolving overlaps."""
    resolver = ConflictResolver()

    # Match 1: SearchProduct (Priority 80)
    match_search = DetectorResult(
        matched=True,
        confidence=0.85,
        intent=IntentEnum.SEARCH_PRODUCT,
        detector_name="SearchDetector",
        detector_version="1.0.0",
        execution_time_ms=0.1,
    )
    # Match 2: CompareProducts (Priority 100)
    match_compare = DetectorResult(
        matched=True,
        confidence=0.80,
        intent=IntentEnum.COMPARE_PRODUCTS,
        detector_name="ComparisonDetector",
        detector_version="1.0.0",
        execution_time_ms=0.1,
    )

    primary, confidence, secondary = resolver.resolve([match_search, match_compare])
    assert primary == IntentEnum.COMPARE_PRODUCTS
    assert confidence == 0.80
    assert secondary == [IntentEnum.SEARCH_PRODUCT]


def test_entity_extractor() -> None:
    """Verify that EntityExtractor parses brands, products, category, specs, colors, and prices correctly."""
    extractor = EntityExtractor()

    # Test query with rupees
    res = extractor.extract("Compare Dell vs HP under ₹70,000")
    assert "Dell" in res["brands"]
    assert "Hp" in res["brands"]
    assert res["price"] == 70000.0

    # Test specs query
    res_specs = extractor.extract(
        "looking for an Apple laptop with 16gb ram, 1TB SSD, RTX 4060 GPU, macOS and OLED screen"
    )
    assert res_specs["brands"] == ["Apple"]
    assert res_specs["category"] == "laptop"
    assert res_specs["ram"] == "16GB"
    assert res_specs["storage"] == "1TB"
    assert res_specs["gpu"] == "RTX 4060"
    assert res_specs["display"] == "OLED"
    assert res_specs["operating_system"] == "macOS"


def test_confidence_calculator() -> None:
    """Verify that ConfidenceCalculator normalizes scores and applies keyword/entity density bonuses."""
    calculator = ConfidenceCalculator()

    # Low base score doesn't get bonuses
    assert calculator.calculate(0.10, ["vs"], {"brands": ["Dell"]}, True) == 0.10

    # Normal base score gets calculated bonuses
    score = calculator.calculate(
        base_confidence=0.80,
        matched_keywords=["compare", "vs"],
        entities={"brands": ["Dell", "Apple"], "category": "laptop"},
        has_category=True,
    )
    # Base: 0.80
    # Keywords bonus: 0.05 * 2 = +0.10
    # Entity bonus: 0.05 * 2 = +0.10
    # Category bonus: +0.05
    # Total score capped to 1.0
    assert score == 1.0


def test_intent_engine_orchestration() -> None:
    """Verify that IntentEngine check runs end-to-end and captures outputs correctly."""
    engine = IntentEngine()

    res = engine.classify_intent("Compare Dell XPS 13 versus MacBook Pro with 16GB RAM under $1500")
    assert res.primary_intent == IntentEnum.COMPARE_PRODUCTS
    assert res.confidence > 0.80
    assert "Dell" in res.entities["brands"]
    assert "ram" in res.entities
    assert res.entities["ram"] == "16GB"
    # Secondary intents tracking
    assert "_metadata" in res.entities


def test_low_confidence_fallback() -> None:
    """Verify that low-confidence matches fallback to UNSUPPORTED."""
    # Custom low confidence detector mock
    class LowConfDetector:
        @property
        def name(self) -> str:
            return "LowConfDetector"

        @property
        def version(self) -> str:
            return "1.0.0"

        def detect(self, query: str) -> DetectorResult:
            return DetectorResult(
                matched=True,
                confidence=0.45,
                intent=IntentEnum.SEARCH_PRODUCT,
                detector_name=self.name,
                detector_version=self.version,
                execution_time_ms=0.0,
            )

    registry = DetectorRegistry(detectors=[LowConfDetector()])
    classifier = IntentClassifier(registry=registry)
    engine = IntentEngine(classifier=classifier)

    res = engine.classify_intent("Looking for something")
    assert res.primary_intent == IntentEnum.UNSUPPORTED
    assert res.confidence == 0.45
