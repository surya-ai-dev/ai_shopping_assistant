"""Duplicate Detection Engine generating product fingerprints and checking uniqueness."""

from src.core.logging import get_logger
from src.core.metrics import DUPLICATE_PRODUCTS_TOTAL
from src.domain.models.product import Product, ProductFingerprint
from src.interfaces.repository import ProductRepositoryInterface

logger = get_logger(__name__)


class DuplicateDetector:
    """Detects product duplicates across sites using normalized fingerprint hash key comparisons."""

    def __init__(self, repository: ProductRepositoryInterface | None = None) -> None:
        self.repository = repository

    def generate_fingerprint(self, product: Product) -> ProductFingerprint:
        """Generate a deterministic ProductFingerprint for product model."""
        key_spec = ""
        specs_dict = product.specs.model_dump()

        # Extract primary spec discriminator
        if specs_dict.get("ram_gb"):
            key_spec += f"ram{specs_dict['ram_gb']}"
        if specs_dict.get("storage_gb"):
            key_spec += f"_str{specs_dict['storage_gb']}"

        fingerprint = ProductFingerprint.generate(
            brand=product.brand,
            model=product.model_name,
            category=product.category,
            key_spec=key_spec,
        )
        return fingerprint

    async def is_duplicate(self, product: Product) -> tuple[bool, Product | None]:
        """Check if product listing is a duplicate of an existing record.

        Args:
            product: Product candidate model.

        Returns:
            Tuple of (is_duplicate_boolean, existing_matched_product_or_none).
        """
        if not product.fingerprint:
            product.fingerprint = self.generate_fingerprint(product)

        if not self.repository:
            return False, None

        # Query database repository by fingerprint hash key
        existing = await self.repository.get_by_fingerprint(product.fingerprint.hash_key)
        if existing and existing.id != product.id:
            DUPLICATE_PRODUCTS_TOTAL.labels(category=product.category.value).inc()
            logger.info(
                "Duplicate product listing detected",
                candidate_url=product.url,
                matched_id=existing.id,
                hash_key=product.fingerprint.hash_key,
            )
            return True, existing

        return False, None
