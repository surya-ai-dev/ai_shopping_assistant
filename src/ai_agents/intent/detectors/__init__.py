"""Intent detectors exports."""

from src.ai_agents.intent.detectors.availability import AvailabilityDetector
from src.ai_agents.intent.detectors.base import IntentDetector
from src.ai_agents.intent.detectors.best_product import BestProductDetector
from src.ai_agents.intent.detectors.brand import BrandDetector
from src.ai_agents.intent.detectors.comparison import ComparisonDetector
from src.ai_agents.intent.detectors.details import ProductDetailsDetector
from src.ai_agents.intent.detectors.feature import FeatureDetector
from src.ai_agents.intent.detectors.price import PriceDetector
from src.ai_agents.intent.detectors.recommendation import RecommendationDetector
from src.ai_agents.intent.detectors.search import SearchDetector
from src.ai_agents.intent.detectors.unknown import UnknownDetector

__all__ = [
    "AvailabilityDetector",
    "BestProductDetector",
    "BrandDetector",
    "ComparisonDetector",
    "FeatureDetector",
    "IntentDetector",
    "PriceDetector",
    "ProductDetailsDetector",
    "RecommendationDetector",
    "SearchDetector",
    "UnknownDetector",
]
