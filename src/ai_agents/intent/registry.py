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


class DetectorRegistry:
    """Manages the lifecycle, registration, and default execution sequence of detectors."""

    def __init__(self, detectors: list[IntentDetector] | None = None) -> None:
        """Initialize the DetectorRegistry.

        Args:
            detectors: Optional custom list of detectors to register. If None,
                      loads the standard defaults.
        """
        self._detectors: list[IntentDetector] = []
        if detectors is not None:
            self._detectors.extend(detectors)
        else:
            self._load_default_detectors()

    def _load_default_detectors(self) -> None:
        """Helper to register default detectors in priority order."""
        self.register_detector(ComparisonDetector())
        self.register_detector(RecommendationDetector())
        self.register_detector(SearchDetector())
        self.register_detector(ProductDetailsDetector())
        self.register_detector(PriceDetector())
        self.register_detector(AvailabilityDetector())
        self.register_detector(FeatureDetector())
        self.register_detector(BrandDetector())
        self.register_detector(BestProductDetector())
        self.register_detector(UnknownDetector())


    def register_detector(self, detector: IntentDetector) -> None:
        """Register a new detector into the active list.

        Ensures that if UnknownDetector is already present, it stays at the end.

        Args:
            detector: An object implementing the IntentDetector protocol.
        """
        # If the list is empty or doesn't end with UnknownDetector, just append
        if not self._detectors:
            self._detectors.append(detector)
            return

        # Keep UnknownDetector always executing last
        if self._detectors[-1].name == "UnknownDetector":
            self._detectors.insert(len(self._detectors) - 1, detector)
        else:
            self._detectors.append(detector)

    def get_detectors(self) -> list[IntentDetector]:
        """Retrieve the ordered list of registered detectors.

        Returns:
            A copy of the current detectors sequence.
        """
        return list(self._detectors)
