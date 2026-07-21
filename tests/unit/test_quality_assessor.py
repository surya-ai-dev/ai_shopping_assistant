"""Unit tests for Data Quality Assessor (DQA) stage."""

from src.domain.enums import CategoryEnum
from src.domain.models.product import Product
from src.domain.models.specs import LaptopSpecs
from src.quality.assessor import DataQualityAssessor

PASSING_THRESHOLD = 0.8


def test_quality_assessor_valid_laptop(
    quality_assessor: DataQualityAssessor, sample_laptop_product: Product
) -> None:
    """Verify quality report calculation on valid laptop product model."""
    report = quality_assessor.assess_product(sample_laptop_product)
    assert report.is_passed is True
    assert report.completeness_score >= PASSING_THRESHOLD
    assert report.parse_confidence >= PASSING_THRESHOLD
    assert report.overall_quality_score >= PASSING_THRESHOLD
    assert len(report.missing_fields) == 0
    assert len(report.invalid_fields) == 0


def test_quality_assessor_missing_required_fields(quality_assessor: DataQualityAssessor) -> None:
    """Verify quality report correctly identifies missing core & spec attributes."""
    incomplete_laptop = Product(
        site_id="bestbuy_us",
        url="https://www.bestbuy.com/site/incomplete.p",
        title="Generic Laptop",
        brand="Generic",
        model_name="Unknown",
        category=CategoryEnum.LAPTOP,
        current_price=500.0,
        specs=LaptopSpecs(processor="Intel i3"),  # Missing ram_gb, storage_gb, screen_size
    )

    report = quality_assessor.assess_product(incomplete_laptop)
    assert report.is_passed is False
    assert "specs.ram_gb" in report.missing_fields
    assert "specs.storage_gb" in report.missing_fields
    assert report.completeness_score < PASSING_THRESHOLD
