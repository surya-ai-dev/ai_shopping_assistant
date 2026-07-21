"""Hierarchical YAML configuration loader for system defaults and site collectors."""

from pathlib import Path
from typing import Any, cast

import yaml

from src.core.exceptions import ConfigurationError
from src.core.logging import get_logger

logger = get_logger(__name__)

DEFAULT_CONFIG_PATH = Path("config/default.yaml")


def load_yaml_config(config_path: Path | str = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Load and parse YAML configuration file.

    Args:
        config_path: Path to YAML file.

    Returns:
        Parsed configuration dictionary.
    """
    path = Path(config_path)
    if not path.exists():
        logger.warning("Configuration file not found, returning empty dict", path=str(path))
        return {}

    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if not isinstance(data, dict):
                return {}
            return cast(dict[str, Any], data)
    except Exception as exc:
        raise ConfigurationError(
            f"Failed to parse YAML configuration at {path}", details={"error": str(exc)}
        ) from exc


def get_collector_config(
    site_id: str, collectors_dir: Path | str = "config/collectors"
) -> dict[str, Any]:
    """Load site-specific collector YAML configuration file.

    Args:
        site_id: Site identifier e.g. 'amazon_us'.
        collectors_dir: Folder path where collector configs reside.

    Returns:
        Collector configuration dictionary.
    """
    base_config = load_yaml_config()
    default_collector_settings = cast(
        dict[str, Any], base_config.get("collector_defaults", {})
    )

    site_file = Path(collectors_dir) / f"{site_id}.yaml"
    if not site_file.exists():
        logger.info(
            "Site specific config file not found, utilizing system defaults", site_id=site_id
        )
        return default_collector_settings

    site_config = load_yaml_config(site_file)
    # Merge defaults with site overrides
    merged: dict[str, Any] = {**default_collector_settings, **site_config}
    return merged
