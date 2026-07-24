"""Product mapper converting between domain Product and ORM ProductORM."""

from src.domain.enums import CategoryEnum, CurrencyEnum
from src.domain.models.product import PriceHistory, Product, ProductFingerprint
from src.domain.models.specs import GenericProductSpecs, LaptopSpecs, MobileSpecs
from src.orm.models import ImageORM, PriceHistoryORM, ProductFingerprintORM, ProductORM, SpecificationORM


def domain_to_orm(product: Product) -> ProductORM:
    """Map a Product domain model to ProductORM."""
    orm = ProductORM(
        id=product.id,
        site_id=product.site_id,
        url=product.url,
        sku=product.sku,
        title=product.title,
        brand=product.brand,
        model_name=product.model_name,
        category=product.category.value,
        current_price=product.current_price,
        original_price=product.original_price,
        currency=product.currency.value,
        is_in_stock=product.is_in_stock,
        rating=product.rating,
        review_count=product.review_count,
        raw_payload_id=product.raw_payload_id,
        metadata_json=product.metadata or {},
    )

    # Map specs
    specs_dict = product.specs.model_dump() if product.specs else {}
    if hasattr(product.specs, "attributes"):
        attributes = getattr(product.specs, "attributes")
    else:
        attributes = specs_dict

    orm.specs = SpecificationORM(
        product_id=product.id,
        attributes=attributes or {},
    )

    # Map price history
    orm.price_history = [
        PriceHistoryORM(
            id=ph.id,
            product_id=product.id,
            price=ph.price,
            original_price=ph.original_price,
            currency=ph.currency.value,
            is_in_stock=ph.is_in_stock,
            seller_name=ph.seller_name,
            timestamp=ph.timestamp,
        )
        for ph in product.price_history
    ]

    # Map images
    orm.images = [
        ImageORM(
            product_id=product.id,
            url=url,
        )
        for url in product.image_urls
    ]

    # Map fingerprint
    if product.fingerprint:
        orm.fingerprint = ProductFingerprintORM(
            product_id=product.id,
            hash_key=product.fingerprint.hash_key,
            brand=product.fingerprint.brand,
            normalized_model=product.fingerprint.normalized_model,
            category=product.fingerprint.category.value,
        )

    return orm


def orm_to_domain(orm: ProductORM) -> Product:
    """Map a ProductORM to Product domain model."""
    category = CategoryEnum(orm.category)

    # Map specs
    specs_attrs = orm.specs.attributes if orm.specs else {}
    specs: LaptopSpecs | MobileSpecs | GenericProductSpecs
    if category == CategoryEnum.LAPTOP:
        specs = LaptopSpecs.model_validate(specs_attrs)
    elif category == CategoryEnum.MOBILE:
        specs = MobileSpecs.model_validate(specs_attrs)
    else:
        specs = GenericProductSpecs.model_validate({"attributes": specs_attrs})

    # Map price history
    history = [
        PriceHistory(
            id=ph.id,
            product_id=ph.product_id,
            price=ph.price,
            original_price=ph.original_price,
            currency=CurrencyEnum(ph.currency),
            is_in_stock=ph.is_in_stock,
            seller_name=ph.seller_name,
            timestamp=ph.timestamp,
        )
        for ph in orm.price_history
    ]
    # Keep history sorted by timestamp ascending
    history = sorted(history, key=lambda x: x.timestamp)

    # Map images
    image_urls = [img.url for img in orm.images] if orm.images else []

    # Map fingerprint
    fingerprint = None
    if orm.fingerprint:
        fingerprint = ProductFingerprint(
            hash_key=orm.fingerprint.hash_key,
            brand=orm.fingerprint.brand,
            normalized_model=orm.fingerprint.normalized_model,
            category=CategoryEnum(orm.fingerprint.category),
        )

    return Product(
        id=orm.id,
        site_id=orm.site_id,
        url=orm.url,
        sku=orm.sku,
        title=orm.title,
        brand=orm.brand,
        model_name=orm.model_name,
        category=category,
        current_price=orm.current_price,
        original_price=orm.original_price,
        currency=CurrencyEnum(orm.currency),
        is_in_stock=orm.is_in_stock,
        rating=orm.rating,
        review_count=orm.review_count,
        image_urls=image_urls,
        raw_payload_id=orm.raw_payload_id,
        specs=specs,
        price_history=history,
        fingerprint=fingerprint,
        metadata=orm.metadata_json or {},
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )
