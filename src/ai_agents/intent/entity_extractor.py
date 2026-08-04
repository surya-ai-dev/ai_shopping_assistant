"""Regex-based Entity Extractor for capturing laptop and mobile specifications."""

import re
from typing import Any, Final

from src.ai_agents.intent.constants import BRAND_KEYWORDS

MIN_STORAGE_GB_THRESHOLD: Final[int] = 128


class EntityExtractor:
    """Extracts brands, product lines, specs, OS, colors, and prices using deterministic regex."""

    def extract(self, query: str) -> dict[str, Any]:
        """Parse query string and return dictionary of matched entities.

        Args:
            query: Normalized user query.

        Returns:
            Dictionary containing extracted shopping parameters.
        """
        lowered_query = query.lower()
        entities: dict[str, Any] = {}

        self._extract_brands(lowered_query, entities)
        self._extract_category(lowered_query, entities)
        self._extract_products(lowered_query, entities)
        self._extract_ram(lowered_query, entities)
        self._extract_storage(lowered_query, entities)
        self._extract_gpu(lowered_query, entities)
        self._extract_cpu(lowered_query, entities)
        self._extract_display(lowered_query, entities)
        self._extract_price(lowered_query, entities)
        self._extract_color(lowered_query, entities)
        self._extract_os(lowered_query, entities)

        return entities

    def _extract_brands(self, lowered_query: str, entities: dict[str, Any]) -> None:
        """Extract matching brand names."""
        matched_brands = []
        for brand in BRAND_KEYWORDS:
            pattern = rf"\b{re.escape(brand)}\b"
            if re.search(pattern, lowered_query):
                matched_brands.append(brand.title())
        if matched_brands:
            entities["brands"] = matched_brands

    def _extract_category(self, lowered_query: str, entities: dict[str, Any]) -> None:
        """Extract product category (laptop or mobile)."""
        category = None
        laptop_patterns = [r"\blaptop\b", r"\bnotebook\b", r"\bmacbook\b", r"\bultrabook\b"]
        mobile_patterns = [r"\bphone\b", r"\bmobile\b", r"\bsmartphone\b", r"\biphone\b"]
        if any(re.search(pat, lowered_query) for pat in laptop_patterns):
            category = "laptop"
        elif any(re.search(pat, lowered_query) for pat in mobile_patterns):
            category = "mobile"
        if category:
            entities["category"] = category

    def _extract_products(self, lowered_query: str, entities: dict[str, Any]) -> None:
        """Extract specific product series/lines."""
        products = []
        prod_patterns = {
            "MacBook Pro": r"\bmacbook\s*pro\b",
            "MacBook Air": r"\bmacbook\s*air\b",
            "Dell XPS": r"\bdell\s*xps\b",
            "Galaxy S24": r"\bgalaxy\s*s24\b",
            "Galaxy S25": r"\bgalaxy\s*s25\b",
            "iPhone 15": r"\biphone\s*15\b",
            "iPhone 16": r"\biphone\s*16\b",
            "Asus Zenbook": r"\basus\s*zenbook\b",
            "Zenbook": r"\bzenbook\b",
            "ThinkPad": r"\bthinkpad\b",
        }
        for name, pat in prod_patterns.items():
            if re.search(pat, lowered_query):
                products.append(name)
        if products:
            entities["products"] = products

    def _extract_ram(self, lowered_query: str, entities: dict[str, Any]) -> None:
        """Extract memory size specifications."""
        ram_match = re.search(r"\b(\d+)\s*(?:gb|gig)\s*(?:ram|memory)?\b", lowered_query)
        if ram_match:
            entities["ram"] = f"{ram_match.group(1)}GB"

    def _extract_storage(self, lowered_query: str, entities: dict[str, Any]) -> None:
        """Extract storage space details, filtering out common RAM specs."""
        storage_matches = re.finditer(r"\b(\d+)\s*(gb|tb)\s*(ssd|storage|hdd)?\b", lowered_query)
        for storage_match in storage_matches:
            val, unit = storage_match.group(1), storage_match.group(2).upper()
            txt = f"{val}{unit}"
            if unit == "TB" or int(val) >= MIN_STORAGE_GB_THRESHOLD:
                entities["storage"] = txt
                break

    def _extract_gpu(self, lowered_query: str, entities: dict[str, Any]) -> None:
        """Extract graphics processing unit specifications."""
        gpu_patterns = [
            r"\brtx\s*\d{4}(?:\s*ti)?\b",
            r"\bgtx\s*\d{4}(?:\s*ti)?\b",
            r"\bintel\s*iris\s*(?:xe)?\b",
            r"\bradeon\b",
            r"\bapple\s*gpu\b",
            r"\bm\d\s*gpu\b",
        ]
        for pat in gpu_patterns:
            gpu_match = re.search(pat, lowered_query)
            if gpu_match:
                entities["gpu"] = gpu_match.group(0).upper()
                break

    def _extract_cpu(self, lowered_query: str, entities: dict[str, Any]) -> None:
        """Extract central processor specifications."""
        cpu_patterns = [
            r"\bintel\s*(?:core)?\s*(?:i[3579])\b",
            r"\bamd\s*ryzen\s*[3579]\b",
            r"\bm[1234]\s*(?:pro|max|ultra)?\b",
            r"\bsnapdragon\s*(?:x\s*elite)?\b",
        ]
        for pat in cpu_patterns:
            cpu_match = re.search(pat, lowered_query)
            if cpu_match:
                entities["cpu"] = cpu_match.group(0).title()
                break

    def _extract_display(self, lowered_query: str, entities: dict[str, Any]) -> None:
        """Extract display panel specifications."""
        display_patterns = [
            r"\boled\b",
            r"\bamoled\b",
            r"\bretina\b",
            r"\bips\b",
            r"\blcd\b",
            r"\b\d{2}(?:\.\d)?\s*(?:inch|in|\")\b",
            r"\b\d{3}\s*hz\b",
        ]
        matched_displays = []
        for pat in display_patterns:
            display_match = re.search(pat, lowered_query)
            if display_match:
                matched_displays.append(display_match.group(0).upper())
        if matched_displays:
            entities["display"] = " ".join(matched_displays)

    def _extract_price(self, lowered_query: str, entities: dict[str, Any]) -> None:
        """Extract budget bounds and price limitations."""
        price_patterns = [
            r"(?:under|below|₹|\$)\s*(\d{1,3}(?:,\d{2,3})*(?:\.\d+)?)\b",
            r"\b(\d{1,3}(?:,\d{2,3})*(?:\.\d+)?)\s*(?:rs|rupees|usd|dollars)?\b",
        ]
        prices = []
        for pat in price_patterns:
            for price_match in re.finditer(pat, lowered_query):
                price_str = price_match.group(1).replace(",", "")
                try:
                    prices.append(float(price_str))
                except ValueError:
                    pass
        if prices:
            entities["price"] = min(prices)

    def _extract_color(self, lowered_query: str, entities: dict[str, Any]) -> None:
        """Extract product color specifications."""
        colors = ["space gray", "silver", "midnight", "black", "white", "titanium", "gold"]
        for c in colors:
            pattern = rf"\b{re.escape(c)}\b"
            if re.search(pattern, lowered_query):
                entities["color"] = c.title()
                break

    def _extract_os(self, lowered_query: str, entities: dict[str, Any]) -> None:
        """Extract software operating system targets."""
        os_patterns = {
            "macOS": r"\bmacos\b",
            "Windows": r"\bwindows\s*(?:11|10)?\b",
            "Android": r"\bandroid\b",
            "iOS": r"\bios\b",
        }
        for name, pat in os_patterns.items():
            if re.search(pat, lowered_query):
                entities["operating_system"] = name
                break
