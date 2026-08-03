"""LLM client API provider enumeration."""

from enum import StrEnum


class ProviderEnum(StrEnum):
    """Supported LLM backend API providers."""

    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    QWEN = "qwen"
    LLAMA = "llama"
