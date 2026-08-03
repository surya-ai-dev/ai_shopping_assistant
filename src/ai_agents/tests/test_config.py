"""Unit tests verifying AI Agent configuration schemas and singleton loader."""

from src.ai_agents.config import AIAgentSettings, get_ai_settings
from src.ai_agents.feature_flags import AIFeatureFlags


def test_ai_settings_default_values() -> None:
    """Verify that AIAgentSettings initializes with expected production defaults."""
    settings = AIAgentSettings()
    assert settings.default_llm_provider == "ollama"
    assert settings.llm_temperature == 0.0
    assert settings.llm_timeout_seconds == 30.0
    assert settings.llm_max_retries == 3
    assert settings.ollama_url == "http://localhost:11434"
    assert settings.enable_cache is True


def test_ai_feature_flags_default_values() -> None:
    """Verify that default feature flags are enabled."""
    flags = AIFeatureFlags()
    assert flags.enable_memory is True
    assert flags.enable_guardrails is True
    assert flags.enable_streaming is True
    assert flags.enable_planner is True
    assert flags.enable_monitoring is True
    assert flags.enable_tracing is True


def test_ai_settings_singleton() -> None:
    """Verify that get_ai_settings loader returns the same cached object."""
    settings_1 = get_ai_settings()
    settings_2 = get_ai_settings()
    assert settings_1 is settings_2
