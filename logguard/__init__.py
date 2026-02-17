"""
logguard - Utilities for structured logging, assertions, and semantic exceptions

Provides:
- Configurable logging (logger.AppLogger)
- Assertions with automatic expression capture (asserts.ASSERT + helpers)
- Meaningful application-level exception hierarchy (exceptions.*)

Lazy loading: submodules are imported only when accessed.

Quick examples:

    from logguard.logger import AppLogger
    from logguard.asserts import ASSERT
    from logguard.exceptions import ValidationError

    AppLogger.setup(console_level="INFO", log_file="logs/app.log")
    logger = AppLogger.get_logger(__name__)

    x = -5
    ASSERT(x > 0, "Value must be positive", extra={"value": x})

Version: 0.2.0
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from . import asserts, exceptions, logger

__version__ = "0.2.0"
__all__ = ["__version__", "asserts", "exceptions", "logger"]


def _lazy_import(submodule: str) -> Any:
    """Load submodule on demand and cache it."""
    try:
        return import_module(f".{submodule}", package=__package__)
    except Exception as exc:
        raise ImportError(f"Failed to load logguard.{submodule}: {exc}") from exc


def __getattr__(name: str) -> Any:
    if name in {"logger", "asserts", "exceptions"}:
        mod = _lazy_import(name)
        globals()[name] = mod
        return mod

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
