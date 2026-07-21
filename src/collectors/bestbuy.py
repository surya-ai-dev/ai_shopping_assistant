"""BestBuy site collector and parser plugins."""

import re
from typing import Any, cast
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import Page, Response

from src.core.logging import get_logger
from src.domain.enums import CategoryEnum, CurrencyEnum, PriorityEnum
from src.domain.models.product import Product
from src.domain.models.specs import LaptopSpecs
from src.domain.models.url import DiscoveredURL
from src.interfaces.collector import BaseCollector
from src.interfaces.parser import BaseParser

logger = get_logger(__name__)

HTTP_STATUS_BAD_REQUEST = 400
HTTP_SUCCESS_THRESHOLD = 400


class BestBuyCollector(BaseCollector):
    """BestBuy site collector plugin."""

    @property
    def site_id(self) -> str:
        """Unique identifier string for the site collector."""
        return "bestbuy_us"

    @property
    def supported_category(self) -> CategoryEnum:
        """Category type supported by this collector."""
        return CategoryEnum.LAPTOP

    @property
    def supported_domains(self) -> list[str]:
        """List of domains supported by this collector."""
        return ["bestbuy.com"]

    async def setup(self) -> None:
        """Lifecycle hook executed prior to starting collection tasks."""
        logger.info("Setting up BestBuy collector plugin")

    async def teardown(self) -> None:
        """Lifecycle hook executed upon completion of collection tasks."""
        logger.info("Tearing down BestBuy collector plugin")

    async def health_check(self, page: Page) -> bool:
        """Verify target website accessibility."""
        try:
            response = await self.request_manager.execute_goto(
                page, "https://www.bestbuy.com", collector_name=self.site_id
            )
            return response is not None and response.status < HTTP_STATUS_BAD_REQUEST
        except Exception as exc:
            logger.warning("Health check failed for BestBuy", error=str(exc))
            return False

    async def discover_urls(self, page: Page, seed_url: str) -> list[DiscoveredURL]:
        """Crawl listing pages or sitemaps to discover product URLs."""
        logger.info("Discovering URLs from BestBuy listing page", seed_url=seed_url)
        response = await self.request_manager.execute_goto(
            page, seed_url, collector_name=self.site_id
        )
        if not response:
            return []

        html_content = await page.content()
        soup = BeautifulSoup(html_content, "html.parser")
        discovered_urls: list[DiscoveredURL] = []
        seen_urls = set()

        # Look for product page links (e.g. contain /site/ or similar patterns)
        for link in soup.find_all("a", href=True):
            href = link.get("href")
            if isinstance(href, str):
                if "/site/" in href and (".p?" in href or href.endswith(".p")):
                    full_url = urljoin(seed_url, href)
                    # Keep clean URLs
                    clean_url = full_url.split("?")[0]
                    if clean_url not in seen_urls:
                        seen_urls.add(clean_url)
                        discovered_urls.append(
                            DiscoveredURL(
                                url=clean_url,
                                site_id=self.site_id,
                                category=self.supported_category,
                                priority=PriorityEnum.MEDIUM,
                            )
                        )

        logger.info("Discovered urls count", count=len(discovered_urls))
        return discovered_urls

    async def fetch_page(self, page: Page, url: str) -> Response | None:
        """Navigate to product page."""
        return await self.request_manager.execute_goto(page, url, collector_name=self.site_id)


class BestBuyParser(BaseParser):
    """BestBuy site parser plugin."""

    @property
    def site_id(self) -> str:
        """Site identifier matching the corresponding collector."""
        return "bestbuy_us"

    @property
    def supported_category(self) -> CategoryEnum:
        """Supported product category."""
        return CategoryEnum.LAPTOP

    def normalize(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Normalize raw dictionary attributes."""
        normalized = super().normalize(raw_data)

        # Normalize price
        price_raw = normalized.get("current_price")
        if isinstance(price_raw, str):
            price_str = re.sub(r"[^\d.]", "", price_raw)
            try:
                normalized["current_price"] = float(price_str)
            except ValueError:
                normalized["current_price"] = 0.0
        elif price_raw is None:
            normalized["current_price"] = 0.0

        orig_price_raw = normalized.get("original_price")
        if isinstance(orig_price_raw, str):
            orig_price_str = re.sub(r"[^\d.]", "", orig_price_raw)
            try:
                normalized["original_price"] = float(orig_price_str)
            except ValueError:
                normalized["original_price"] = None
        elif orig_price_raw is None:
            normalized["original_price"] = None

        # Normalize currency
        normalized["currency"] = CurrencyEnum.USD

        # Normalize URLs
        for key in ["url", "image_urls"]:
            val = normalized.get(key)
            if isinstance(val, str):
                normalized[key] = val.strip()
            elif isinstance(val, list):
                normalized[key] = [img.strip() for img in val if isinstance(img, str)]

        # Normalize rating
        rating_raw = normalized.get("rating")
        if isinstance(rating_raw, str):
            rating_str = re.search(r"(\d+(\.\d+)?)", rating_raw)
            if rating_str:
                normalized["rating"] = float(rating_str.group(1))
            else:
                normalized["rating"] = None
        elif rating_raw is not None:
            try:
                normalized["rating"] = float(rating_raw)
            except (ValueError, TypeError):
                normalized["rating"] = None

        # Normalize specs
        raw_specs = normalized.get("specs", {})
        normalized_specs: dict[str, Any] = {}
        for k, v in raw_specs.items():
            clean_key = k.lower().replace(" ", "_").replace("-", "_")
            clean_key = re.sub(r"[^\w]", "", clean_key)
            normalized_specs[clean_key] = v

        normalized["specs"] = normalized_specs
        return normalized

    def _extract_title_brand(self, soup: BeautifulSoup) -> tuple[str, str]:
        """Extract title and brand from HTML content."""
        title_el = soup.select_one("h1, .sku-title, .product-title")
        title = title_el.get_text() if title_el else "Unknown Product"
        brand_el = soup.select_one(".brand-link, a[data-track='brand']")
        if brand_el:
            brand = brand_el.get_text().strip()
        else:
            brand = title.split(" ")[0] if title else "Unknown"
        return title, brand

    def _extract_prices(self, soup: BeautifulSoup) -> tuple[str, str | None]:
        """Extract current and original prices."""
        price_el = soup.select_one(".price-block, .priceView-customer-price span, .value")
        current_price = price_el.get_text() if price_el else "0.0"
        orig_price_el = soup.select_one(".priceView-pricing-regular-price, .strike-rx")
        original_price = orig_price_el.get_text() if orig_price_el else None
        return current_price, original_price

    def _extract_sku(self, soup: BeautifulSoup, url: str) -> str | None:
        """Extract SKU / Product ID."""
        sku_el = soup.select_one(".sku-value, [data-sku]")
        sku = None
        if sku_el:
            sku = sku_el.get_text().strip()
            if not sku and sku_el.has_attr("data-sku"):
                data_sku = sku_el["data-sku"]
                if isinstance(data_sku, list):
                    sku = data_sku[0] if data_sku else ""
                else:
                    sku = str(data_sku)
        if not sku:
            sku_match = re.search(r"site/(\d+)\.p", url)
            if sku_match:
                sku = sku_match.group(1)
        return sku

    def _extract_images(self, soup: BeautifulSoup, url: str) -> list[str]:
        """Extract image URLs."""
        image_urls: list[str] = []
        for img in soup.select("img.primary-image, .image-gallery img, img[src*='bestbuy.com/images']"):
            src = img.get("src")
            if isinstance(src, str):
                image_urls.append(urljoin(url, src))
        return image_urls

    def _extract_availability(self, soup: BeautifulSoup) -> bool:
        """Extract product availability."""
        add_to_cart_btn = soup.select_one(".add-to-cart-button, button.btn-primary")
        is_in_stock = True
        if add_to_cart_btn:
            btn_text = add_to_cart_btn.get_text().lower()
            if "sold out" in btn_text or "unavailable" in btn_text:
                is_in_stock = False
        return is_in_stock

    def _extract_rating_reviews(self, soup: BeautifulSoup) -> tuple[str | None, int | None]:
        """Extract rating and review count."""
        rating = None
        rating_el = soup.select_one(".c-ratings-reviews, .ugc-ratings-reviews, [class*='rating']")
        if rating_el:
            rating = rating_el.get_text().strip()
        review_count = None
        review_el = soup.select_one(".c-reviews, .ugc-reviews, [class*='review-count']")
        if review_el:
            review_text = review_el.get_text().strip()
            review_match = re.search(r"(\d+)", review_text.replace(",", ""))
            if review_match:
                review_count = int(review_match.group(1))
        return rating, review_count

    def _extract_specs_table(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract specs table into a raw dictionary."""
        specs: dict[str, Any] = {}
        for spec_row in soup.select(".specs-table-row, tr.spec-row"):
            label_el = spec_row.select_one(".spec-label, td.label")
            val_el = spec_row.select_one(".spec-value, td.value")
            if label_el and val_el:
                specs[label_el.get_text().strip()] = val_el.get_text().strip()
        return specs

    async def parse(
        self, html_content: str, url: str, raw_payload_id: str | None = None
    ) -> Product:
        """Parse raw HTML string and extract BestBuy Laptop product."""
        soup = self.create_soup(html_content)

        title, brand = self._extract_title_brand(soup)
        current_price, original_price = self._extract_prices(soup)
        sku = self._extract_sku(soup, url)
        image_urls = self._extract_images(soup, url)
        is_in_stock = self._extract_availability(soup)
        rating, review_count = self._extract_rating_reviews(soup)
        specs = self._extract_specs_table(soup)

        # Model Name
        model_el = soup.select_one(".model-number, .model-value")
        model_name = model_el.get_text().strip() if model_el else "Unknown Model"

        # Run normalization
        raw_data = {
            "title": title,
            "brand": brand,
            "current_price": current_price,
            "original_price": original_price,
            "sku": sku,
            "model_name": model_name,
            "image_urls": image_urls,
            "is_in_stock": is_in_stock,
            "rating": rating,
            "review_count": review_count,
            "specs": specs,
        }
        normalized = self.normalize(raw_data)

        specs_dict = cast(dict[str, Any], normalized.get("specs", {}))
        # Parse specific laptop specs
        laptop_specs_dict = {
            "processor": self._find_spec(
                specs_dict,
                ["processor_model", "processor", "cpu_model", "cpu", "processor_type"]
            ),
            "ram_gb": self._parse_int_spec(
                self._find_spec(
                    specs_dict,
                    ["system_memory_ram", "ram_gb", "ram", "system_memory", "memory"]
                )
            ),
            "ram_type": self._find_spec(
                specs_dict,
                ["type_of_memory_ram", "ram_type", "memory_type"]
            ),
            "storage_gb": self._parse_int_spec(
                self._find_spec(
                    specs_dict,
                    [
                        "total_storage_capacity",
                        "storage_capacity",
                        "storage_gb",
                        "storage",
                        "hard_drive_capacity",
                        "ssd_capacity",
                    ]
                )
            ),
            "storage_type": self._find_spec(
                specs_dict,
                ["storage_type", "hard_drive_type"]
            ),
            "screen_size_inches": self._parse_float_spec(
                self._find_spec(
                    specs_dict,
                    ["screen_size", "screen_size_inches", "display_size"]
                )
            ),
            "display_resolution": self._find_spec(
                specs_dict,
                ["screen_resolution", "display_resolution", "resolution"]
            ),
            "gpu": self._find_spec(
                specs_dict,
                ["graphics", "gpu", "graphics_card", "gpu_model"]
            ),
            "operating_system": self._find_spec(
                specs_dict,
                ["operating_system", "os"]
            ),
            "extra_specs": specs_dict,
        }
        laptop_specs = LaptopSpecs.model_validate(laptop_specs_dict)

        return Product(
            site_id=self.site_id,
            url=url,
            sku=normalized["sku"],
            title=normalized["title"],
            brand=normalized["brand"],
            model_name=normalized["model_name"],
            category=self.supported_category,
            current_price=normalized["current_price"],
            original_price=normalized["original_price"],
            currency=normalized["currency"],
            is_in_stock=normalized["is_in_stock"],
            rating=normalized["rating"],
            review_count=normalized["review_count"],
            image_urls=normalized["image_urls"],
            raw_payload_id=raw_payload_id,
            specs=laptop_specs,
            metadata={"raw_payload_id": raw_payload_id},
        )

    def _parse_int_spec(self, val: Any) -> int | None:
        if not val:
            return None
        match = re.search(r"(\d+)", str(val))
        return int(match.group(1)) if match else None

    def _parse_float_spec(self, val: Any) -> float | None:
        if not val:
            return None
        match = re.search(r"(\d+(\.\d+)?)", str(val))
        return float(match.group(1)) if match else None
