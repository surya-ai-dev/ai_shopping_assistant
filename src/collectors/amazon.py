"""Amazon site collector and parser plugins."""

import re
from typing import Any, cast
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.async_api import Page, Response

from src.core.logging import get_logger
from src.domain.enums import CategoryEnum, CurrencyEnum, PriorityEnum
from src.domain.models.product import Product
from src.domain.models.specs import MobileSpecs
from src.domain.models.url import DiscoveredURL
from src.interfaces.collector import BaseCollector
from src.interfaces.parser import BaseParser

logger = get_logger(__name__)

HTTP_STATUS_BAD_REQUEST = 400
HTTP_SUCCESS_THRESHOLD = 400


class AmazonCollector(BaseCollector):
    """Amazon mobile phone collector plugin."""

    @property
    def site_id(self) -> str:
        """Unique identifier string for the site collector."""
        return "amazon_us"

    @property
    def supported_category(self) -> CategoryEnum:
        """Category type supported by this collector."""
        return CategoryEnum.MOBILE

    @property
    def supported_domains(self) -> list[str]:
        """List of domains supported by this collector."""
        return ["amazon.com"]

    async def setup(self) -> None:
        """Lifecycle hook executed prior to starting collection tasks."""
        logger.info("Setting up Amazon collector plugin")

    async def teardown(self) -> None:
        """Lifecycle hook executed upon completion of collection tasks."""
        logger.info("Tearing down Amazon collector plugin")

    async def health_check(self, page: Page) -> bool:
        """Verify target website accessibility."""
        try:
            response = await self.request_manager.execute_goto(
                page, "https://www.amazon.com", collector_name=self.site_id
            )
            return response is not None and response.status < HTTP_STATUS_BAD_REQUEST
        except Exception as exc:
            logger.warning("Health check failed for Amazon", error=str(exc))
            return False

    async def discover_urls(self, page: Page, seed_url: str) -> list[DiscoveredURL]:
        """Crawl listing pages or sitemaps to discover product URLs."""
        logger.info("Discovering URLs from Amazon listing page", seed_url=seed_url)
        response = await self.request_manager.execute_goto(
            page, seed_url, collector_name=self.site_id
        )
        if not response:
            return []

        html_content = await page.content()
        soup = BeautifulSoup(html_content, "html.parser")
        discovered_urls: list[DiscoveredURL] = []
        seen_urls = set()

        # Find product links (often containing /dp/ or /gp/product/)
        for link in soup.find_all("a", href=True):
            href = link.get("href")
            if isinstance(href, str):
                if "/dp/" in href or "/gp/product/" in href:
                    full_url = urljoin(seed_url, href)
                    # Parse out and keep standard Amazon product URLs
                    dp_match = re.search(r"/(dp|gp/product)/([A-Z0-9]{10})", full_url)
                    if dp_match:
                        clean_url = f"https://www.amazon.com/dp/{dp_match.group(2)}"
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


class AmazonParser(BaseParser):
    """Amazon mobile phone parser plugin."""

    @property
    def site_id(self) -> str:
        """Site identifier matching the corresponding collector."""
        return "amazon_us"

    @property
    def supported_category(self) -> CategoryEnum:
        """Supported product category."""
        return CategoryEnum.MOBILE

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

        # Normalize specs keys
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
        title_el = soup.select_one("#productTitle, .qa-title")
        title = title_el.get_text() if title_el else "Unknown Product"
        brand_el = soup.select_one("#bylineInfo, .a-brand, #brand")
        if brand_el:
            brand_text = brand_el.get_text().strip()
            # Clean up brand text like "Brand: Samsung" or "Visit the Apple Store"
            brand_text = re.sub(r"(Brand:\s*|Visit the\s*|\s*Store)", "", brand_text, flags=re.IGNORECASE)
            brand = brand_text.strip()
        else:
            brand = title.split(" ")[0] if title else "Unknown"
        return title, brand

    def _extract_prices(self, soup: BeautifulSoup) -> tuple[str, str | None]:
        """Extract current and original prices."""
        price_el = soup.select_one(".a-price .a-offscreen, #priceBlock_ourPrice, #priceblock_dealprice")
        current_price = price_el.get_text() if price_el else "0.0"
        orig_price_el = soup.select_one(".basisPrice .a-offscreen, .listPrice")
        original_price = orig_price_el.get_text() if orig_price_el else None
        return current_price, original_price

    def _extract_sku(self, url: str) -> str | None:
        """Extract SKU (ASIN) from product page URL."""
        sku = None
        asin_match = re.search(r"/dp/([A-Z0-9]{10})", url)
        if asin_match:
            sku = asin_match.group(1)
        return sku

    def _extract_image_urls(self, soup: BeautifulSoup, url: str) -> list[str]:
        """Extract image URLs from page content."""
        image_urls: list[str] = []
        for img in soup.select("#landingImage, #imgTagWrapperId img, img[src*='media-amazon.com/images']"):
            src_val = img.get("src") or img.get("data-old-hires") or img.get("data-a-dynamic-image")
            src = None
            if isinstance(src_val, list) and src_val:
                src = src_val[0]
            elif isinstance(src_val, str):
                src = src_val

            if src:
                # Handle dynamic image map strings
                if src.startswith("{"):
                    # Grab the first key
                    match = re.search(r'"([^"]+)"', src)
                    if match:
                        src = match.group(1)
                image_urls.append(urljoin(url, src))
        return image_urls

    def _extract_availability(self, soup: BeautifulSoup) -> bool:
        """Extract availability status."""
        availability_el = soup.select_one("#availability, .availability")
        is_in_stock = True
        if availability_el:
            avail_text = availability_el.get_text().lower()
            if "currently unavailable" in avail_text or "out of stock" in avail_text:
                is_in_stock = False
        return is_in_stock

    def _extract_rating_reviews(self, soup: BeautifulSoup) -> tuple[str | None, int | None]:
        """Extract rating and review count."""
        rating = None
        rating_el = soup.select_one(".a-icon-alt, #acrCustomerReviewText")
        if rating_el:
            rating = rating_el.get_text().strip()
        review_count = None
        review_el = soup.select_one("#acrCustomerReviewText, #acrCustomerReviewLink, .a-size-base")
        if review_el:
            review_text = review_el.get_text().strip()
            review_match = re.search(r"(\d+)", review_text.replace(",", ""))
            if review_match:
                review_count = int(review_match.group(1))
        return rating, review_count

    def _extract_specs_table(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract specs table and bullet points into a raw dictionary."""
        specs: dict[str, Any] = {}
        for spec_row in soup.select("table.prodDetTable tr"):
            label_el = spec_row.select_one("th")
            val_el = spec_row.select_one("td")
            if label_el and val_el:
                specs[label_el.get_text().strip()] = val_el.get_text().strip()
        for item in soup.select("#detailBullets_feature_div li"):
            text = item.get_text().strip()
            if ":" in text:
                parts = text.split(":", 1)
                specs[parts[0].strip()] = parts[1].strip()
        return specs

    async def parse(
        self, html_content: str, url: str, raw_payload_id: str | None = None
    ) -> Product:
        """Parse raw HTML string and extract Amazon Mobile product."""
        soup = self.create_soup(html_content)

        title, brand = self._extract_title_brand(soup)
        current_price, original_price = self._extract_prices(soup)
        sku = self._extract_sku(url)
        image_urls = self._extract_image_urls(soup, url)
        is_in_stock = self._extract_availability(soup)
        rating, review_count = self._extract_rating_reviews(soup)
        specs = self._extract_specs_table(soup)

        # Model Name
        model_el = soup.select_one(".product-model-name, .model-value")
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
        # Parse specific mobile specs
        mobile_specs_dict = {
            "processor": self._find_spec(
                specs_dict,
                ["processor", "cpu_model", "cpu", "chipset", "processor_type"]
            ),
            "ram_gb": self._parse_int_spec(
                self._find_spec(
                    specs_dict,
                    ["ram", "system_memory_ram", "ram_gb", "system_memory", "memory"]
                )
            ),
            "storage_gb": self._parse_int_spec(
                self._find_spec(
                    specs_dict,
                    ["storage", "internal_memory", "storage_gb", "storage_capacity", "rom"]
                )
            ),
            "screen_size_inches": self._parse_float_spec(
                self._find_spec(
                    specs_dict,
                    [
                        "screen_size",
                        "standing_screen_display_size",
                        "display_size",
                        "screen_size_inches",
                    ]
                )
            ),
            "display_type": self._find_spec(
                specs_dict,
                ["display_type", "screen_type", "display_technology"]
            ),
            "refresh_rate_hz": self._parse_int_spec(
                self._find_spec(
                    specs_dict,
                    ["refresh_rate", "refresh_rate_hz"]
                )
            ),
            "main_camera_mp": self._parse_float_spec(
                self._find_spec(
                    specs_dict,
                    [
                        "main_camera",
                        "rear_camera",
                        "rear_camera_resolution",
                        "main_camera_mp",
                    ]
                )
            ),
            "selfie_camera_mp": self._parse_float_spec(
                self._find_spec(
                    specs_dict,
                    [
                        "selfie_camera",
                        "front_camera",
                        "front_camera_resolution",
                        "selfie_camera_mp",
                    ]
                )
            ),
            "battery_capacity_mah": self._parse_int_spec(
                self._find_spec(
                    specs_dict,
                    ["battery_capacity", "battery_capacity_mah", "battery"]
                )
            ),
            "charging_wattage": self._parse_float_spec(
                self._find_spec(
                    specs_dict,
                    ["charging_speed", "charging_wattage", "fast_charging"]
                )
            ),
            "operating_system": self._find_spec(
                specs_dict,
                ["operating_system", "os", "os_version"]
            ),
            "extra_specs": specs_dict,
        }
        mobile_specs = MobileSpecs.model_validate(mobile_specs_dict)

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
            specs=mobile_specs,
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