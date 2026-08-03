"""Model complexity sizes for dynamic routing decisions."""

from enum import StrEnum


class ModelSizeEnum(StrEnum):
    """Classification of models by reasoning capacity to guide cost/routing optimizer."""

    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
