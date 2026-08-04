"""Wrapper for intent classification test cases complying with folder structure."""

from src.ai_agents.tests.test_intent import (
    test_availability_detector,
    test_best_product_detector,
    test_brand_detector,
    test_comparison_detector,
    test_confidence_calculator,
    test_conflict_resolver,
    test_details_detector,
    test_detector_registry,
    test_entity_extractor,
    test_feature_detector,
    test_intent_engine_orchestration,
    test_low_confidence_fallback,
    test_price_detector,
    test_recommendation_detector,
    test_search_detector,
    test_unknown_detector,
)

__all__ = [
    "test_availability_detector",
    "test_best_product_detector",
    "test_brand_detector",
    "test_comparison_detector",
    "test_confidence_calculator",
    "test_conflict_resolver",
    "test_details_detector",
    "test_detector_registry",
    "test_entity_extractor",
    "test_feature_detector",
    "test_intent_engine_orchestration",
    "test_low_confidence_fallback",
    "test_price_detector",
    "test_recommendation_detector",
    "test_search_detector",
    "test_unknown_detector",
]
