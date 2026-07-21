"""Data Quality Assessment (DQA) Engine evaluating extracted Product domain entities."""

from src.core.logging import get_logger
from src.domain.enums import CategoryEnum
from src.domain.models.product import Product
from src.domain.models.quality import DataQualityReport

logger = get_logger(__name__)


# Data Quality Assessment Constants
MAX_PRODUCT_RATING = 5.0
MIN_TITLE_LENGTH = 10
CORE_COMPLETENESS_WEIGHT = 0.6
SPECS_COMPLETENESS_WEIGHT = 0.4
PARSE_CONFIDENCE_IMAGE_DEDUCTION = 0.15
PARSE_CONFIDENCE_TITLE_DEDUCTION = 0.15
INVALID_FIELD_DEDUCTION_WEIGHT = 0.2
COMPLETENESS_OVERALL_WEIGHT = 0.5
CONFIDENCE_OVERALL_WEIGHT = 0.5


class DataQualityAssessor:
    """Evaluates product quality, score completeness, missing/invalid fields, and parse confidence."""

    def __init__(
        self,
        min_completeness: float = 0.80,
        min_confidence: float = 0.70,
        min_overall_score: float = 0.65,
    ) -> None:
        # Minimum required completeness score (0.80 threshold required for passing product assessment)
        self.min_completeness = min_completeness
        self.min_confidence = min_confidence
        self.min_overall_score = min_overall_score

    def assess_product(self, product: Product) -> DataQualityReport:
        """Perform quality assessment on extracted Product domain model.

        Args:
            product: Populated Product model.

        Returns:
            Calculated DataQualityReport instance.
        """
        missing_fields: list[str] = []
        invalid_fields: list[str] = []

        # Required Core Fields
        required_core = [
            ("title", product.title),
            ("brand", product.brand),
            ("model_name", product.model_name),
            ("current_price", product.current_price),
            ("url", product.url),
        ]

        total_core_fields = len(required_core)
        populated_core_count = 0

        for field_name, value in required_core:
            if not value and value != 0:
                missing_fields.append(f"core.{field_name}")
            else:
                populated_core_count += 1

        # Check field validity rules
        if product.current_price < 0:
            invalid_fields.append("core.current_price_negative")
        if product.original_price is not None and product.original_price < product.current_price:
            invalid_fields.append("core.original_price_below_current")
        if product.rating is not None and not (0.0 <= product.rating <= MAX_PRODUCT_RATING):
            invalid_fields.append("core.rating_out_of_bounds")

        # Category Specific Specs Quality Check
        specs_dict = product.specs.model_dump()
        expected_spec_keys: list[str] = []

        if product.category == CategoryEnum.LAPTOP:
            expected_spec_keys = [
                "processor",
                "ram_gb",
                "storage_gb",
                "screen_size_inches",
                "operating_system",
            ]
        elif product.category == CategoryEnum.MOBILE:
            expected_spec_keys = [
                "processor",
                "ram_gb",
                "storage_gb",
                "screen_size_inches",
                "battery_capacity_mah",
                "operating_system",
            ]

        populated_specs_count = 0
        total_spec_fields = len(expected_spec_keys)

        for key in expected_spec_keys:
            val = specs_dict.get(key)
            if not val and val != 0:
                missing_fields.append(f"specs.{key}")
            else:
                populated_specs_count += 1

        # Calculate Scores
        core_completeness = (
            populated_core_count / float(total_core_fields) if total_core_fields > 0 else 0.0
        )
        specs_completeness = (
            populated_specs_count / float(total_spec_fields) if total_spec_fields > 0 else 1.0
        )

        completeness_score = round(
            CORE_COMPLETENESS_WEIGHT * core_completeness
            + SPECS_COMPLETENESS_WEIGHT * specs_completeness,
            2,
        )

        # Parse confidence based on image, title length, and invalid fields
        parse_confidence = 1.0
        if not product.image_urls:
            parse_confidence -= PARSE_CONFIDENCE_IMAGE_DEDUCTION
        if len(product.title) < MIN_TITLE_LENGTH:
            parse_confidence -= PARSE_CONFIDENCE_TITLE_DEDUCTION
        if invalid_fields:
            parse_confidence -= len(invalid_fields) * INVALID_FIELD_DEDUCTION_WEIGHT
        parse_confidence = max(0.0, round(parse_confidence, 2))

        # Overall Quality Score
        overall_quality_score = round(
            COMPLETENESS_OVERALL_WEIGHT * completeness_score
            + CONFIDENCE_OVERALL_WEIGHT * parse_confidence,
            2,
        )

        is_passed = (
            completeness_score >= self.min_completeness
            and parse_confidence >= self.min_confidence
            and overall_quality_score >= self.min_overall_score
            and len(invalid_fields) == 0
        )

        logger.debug(
            "Product data quality assessed",
            url=product.url,
            overall_score=overall_quality_score,
            is_passed=is_passed,
        )

        return DataQualityReport(
            product_id=product.id,
            site_id=product.site_id,
            completeness_score=completeness_score,
            missing_fields=missing_fields,
            invalid_fields=invalid_fields,
            parse_confidence=parse_confidence,
            overall_quality_score=overall_quality_score,
            is_passed=is_passed,
            assessment_details={
                "core_completeness": core_completeness,
                "specs_completeness": specs_completeness,
            },
        )
