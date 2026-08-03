"""Product category enumeration, strictly enforcing Laptop and Mobile Phone categories."""

from enum import StrEnum


class CategoryEnum(StrEnum):
    """Enforces boundaries for product categories in the AI assistant."""

    LAPTOP = "laptop"
    MOBILE = "mobile"
