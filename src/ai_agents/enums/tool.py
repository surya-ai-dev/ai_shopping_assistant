"""Tool classification and invocation type enums."""

from enum import StrEnum


class ToolTypeEnum(StrEnum):
    """Available tool categories in the AI Agent planner registry."""

    PRODUCT = "product"
    REVIEW = "review"
    PRICE = "price"
    RECOMMENDATION = "recommendation"
    WISHLIST = "wishlist"
    NOTIFICATION = "notification"
