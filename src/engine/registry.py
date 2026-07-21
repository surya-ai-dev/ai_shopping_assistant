"""Collector & Parser Registry supporting dynamic plugin auto-discovery via importlib."""

import importlib
import inspect
import pkgutil
from typing import ClassVar

from src.core.exceptions import CollectorNotFoundError
from src.core.logging import get_logger
from src.interfaces.collector import BaseCollector
from src.interfaces.parser import BaseParser

logger = get_logger(__name__)


class CollectorRegistry:
    """Thread-safe Registry for Collectors and Parsers with plugin auto-discovery."""

    _collectors: ClassVar[dict[str, type[BaseCollector]]] = {}
    _parsers: ClassVar[dict[str, type[BaseParser]]] = {}

    @classmethod
    def register(
        cls,
        site_id: str,
        collector_cls: type[BaseCollector],
        parser_cls: type[BaseParser] | None = None,
    ) -> None:
        """Register a collector class and optional parser class.

        Args:
            site_id: Target site identifier string.
            collector_cls: Subclass of BaseCollector.
            parser_cls: Optional subclass of BaseParser.
        """
        cls._collectors[site_id] = collector_cls
        if parser_cls:
            cls._parsers[site_id] = parser_cls
        logger.info("Registered site collector plugin", site_id=site_id)

    @classmethod
    def register_parser(cls, site_id: str, parser_cls: type[BaseParser]) -> None:
        """Register a parser class for a site."""
        cls._parsers[site_id] = parser_cls

    @classmethod
    def get_collector(cls, site_id: str) -> type[BaseCollector]:
        """Retrieve registered collector class by site_id."""
        if site_id not in cls._collectors:
            raise CollectorNotFoundError(
                f"No collector registered for site_id '{site_id}'",
                details={"registered_sites": list(cls._collectors.keys())},
            )
        return cls._collectors[site_id]

    @classmethod
    def get_parser(cls, site_id: str) -> type[BaseParser]:
        """Retrieve registered parser class by site_id."""
        if site_id not in cls._parsers:
            raise CollectorNotFoundError(
                f"No parser registered for site_id '{site_id}'",
                details={"registered_sites": list(cls._parsers.keys())},
            )
        return cls._parsers[site_id]

    @classmethod
    def list_sites(cls) -> list[str]:
        """List all registered site identifiers."""
        return list(cls._collectors.keys())

    @classmethod
    def discover_plugins(cls, package_name: str = "src.collectors") -> int:
        """Dynamically discover and import collector/parser plugins inside a package.

        Args:
            package_name: Dot-separated python package path.

        Returns:
            Number of newly discovered and registered plugins.
        """
        discovered_count = 0
        try:
            package = importlib.import_module(package_name)
        except ModuleNotFoundError:
            logger.info(
                "Collector package directory not found, skipping plugin discovery",
                package=package_name,
            )
            return 0

        if not hasattr(package, "__path__"):
            return 0

        for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
            try:
                mod = importlib.import_module(module_name)
                for _, obj in inspect.getmembers(mod, inspect.isclass):
                    if (
                        issubclass(obj, BaseCollector)
                        and obj is not BaseCollector
                        and not inspect.isabstract(obj)
                    ):
                        site_id = getattr(obj, "site_id", None)
                        if isinstance(site_id, property):
                            site_id = None
                        if not site_id:
                            try:
                                site_id = getattr(obj(), "site_id", None)
                            except Exception:
                                site_id = None

                        if site_id and site_id not in cls._collectors:
                            cls._collectors[site_id] = obj
                            discovered_count += 1

                    if (
                        issubclass(obj, BaseParser)
                        and obj is not BaseParser
                        and not inspect.isabstract(obj)
                    ):
                        site_id = getattr(obj, "site_id", None)
                        if isinstance(site_id, property):
                            site_id = None
                        if not site_id:
                            try:
                                site_id = getattr(obj(), "site_id", None)
                            except Exception:
                                site_id = None

                        if site_id and site_id not in cls._parsers:
                            cls._parsers[site_id] = obj

            except Exception as exc:
                logger.warning(
                    "Error importing plugin module during discovery",
                    module=module_name,
                    error=str(exc),
                )

        logger.info(
            "Auto-discovery complete",
            discovered_count=discovered_count,
            total_registered=len(cls._collectors),
        )
        return discovered_count
