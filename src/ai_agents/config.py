"""Configuration settings for the AI Agents platform powered by Pydantic Settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.ai_agents.feature_flags import AIFeatureFlags


class AIAgentSettings(BaseSettings):
    """Configuration settings for the AI agent platform."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        env_prefix="AI_",
    )

    # Core LLM configurations
    default_llm_provider: str = Field(default="ollama", description="Default model provider (e.g. ollama, openai, gemini).")
    default_llm_model: str = Field(default="llama3.2:3b", description="Default model name identifier.")
    llm_temperature: float = Field(default=0.0, description="Temperature parameter for inference responses.")
    llm_timeout_seconds: float = Field(default=30.0, description="Timeout limit for external LLM requests.")
    llm_max_retries: int = Field(default=3, description="Maximum number of retries for failed LLM requests.")

    # Provider endpoints
    ollama_url: str = Field(default="http://localhost:11434", description="Base HTTP URL for local Ollama instances.")
    openai_api_key: str | None = Field(default=None, description="Secret API key for OpenAI.")
    gemini_api_key: str | None = Field(default=None, description="Secret API key for Google Gemini.")
    anthropic_api_key: str | None = Field(default=None, description="Secret API key for Anthropic Claude.")

    # Cache Settings
    enable_cache: bool = Field(default=True, description="Toggle caching for LLM requests.")
    cache_ttl_seconds: int = Field(default=3600, description="Time-To-Live in seconds for cached elements.")
    redis_url: str = Field(default="redis://localhost:6379/1", description="Redis connection string for short-term caching.")

    # Logging Settings
    log_level: str = Field(default="INFO", description="Target logging level for AI events.")
    enable_structured_logs: bool = Field(default=True, description="Enable structured JSON log printing.")

    # Embedded Feature Flags
    feature_flags: AIFeatureFlags = Field(default_factory=AIFeatureFlags)


@lru_cache
def get_ai_settings() -> AIAgentSettings:
    """Return cached singleton instance of AIAgentSettings."""
    return AIAgentSettings()
