"""
logguard — Utilities for structured logging, assertions, and semantic exceptions

Provides:
- Configurable logging (AppLogger)
- Assertions with automatic expression capture (ASSERT + helpers)
- Meaningful application-level exception hierarchy

Lazy loading: submodules are imported only when accessed.

Quick examples:

    from logguard import AppLogger, ASSERT, ValidationError

    AppLogger.setup(console_level="INFO", log_file="logs/app.log")
    logger = AppLogger.get_logger(__name__)

    x = -5
    ASSERT(x > 0, "Value must be positive", extra={"value": x})

Version: 0.1.0
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:  # pragma: no cover
    from .asserts import (
        ASSERT,
        ASSERT_EQUALS,
        ASSERT_IN,
        ASSERT_NONE,
        ASSERT_NOT_EMPTY,
        ASSERT_NOT_NONE,
        ASSERT_RANGE,
        ASSERT_TYPE,
        enforce,
        set_failure_handler,
    )
    from .exceptions import (
        AppBaseError,
        ConfigurationError,
        ForbiddenError,
        MissingConfigError,
        ResourceError,
        ResourceNotFoundError,
        ValidationError,
    )
    from .logger import AppLogger

__version__: Final[str] = "0.2.0"

__all__ = [
    "ASSERT",
    "ASSERT_EQUALS",
    "ASSERT_IN",
    "ASSERT_NONE",
    "ASSERT_NOT_EMPTY",
    "ASSERT_NOT_NONE",
    "ASSERT_RANGE",
    "ASSERT_TYPE",
    "AppBaseError",
    "AppLogger",
    "ConfigurationError",
    "ForbiddenError",
    "MissingConfigError",
    "ResourceError",
    "ResourceNotFoundError",
    "ValidationError",
    "asserts",
    "enforce",
    "exceptions",
    "logger",
    "set_failure_handler",
]

# Sets for faster lookup in __getattr__
ASSERT_HELPERS = {
    "ASSERT",
    "enforce",
    "set_failure_handler",
    "ASSERT_TYPE",
    "ASSERT_IN",
    "ASSERT_NOT_EMPTY",
    "ASSERT_RANGE",
    "ASSERT_EQUALS",
    "ASSERT_NONE",
    "ASSERT_NOT_NONE",
}

EXCEPTION_NAMES = {
    "AppBaseError",
    "ConfigurationError",
    "ForbiddenError",
    "MissingConfigError",
    "ResourceError",
    "ResourceNotFoundError",
    "ValidationError",
}

_submodules: dict[str, Any] = {}


def _lazy_import(submodule: str) -> Any:
    """Load submodule on demand and cache it."""
    if submodule not in _submodules:
        try:
            mod = import_module(f".{submodule}", package=__package__)
            _submodules[submodule] = mod
        except Exception as exc:
            raise ImportError(f"Failed to load submodule 'logguard.{submodule}': {exc}") from exc
    return _submodules[submodule]


def __getattr__(name: str) -> Any:
    """Lazy attribute access - most frequent paths first."""
    if name == "AppLogger":
        value = _lazy_import("logger").AppLogger
        globals()[name] = value
        return value

    if name in ASSERT_HELPERS:
        value = getattr(_lazy_import("asserts"), name)
        globals()[name] = value
        return value

    if name in EXCEPTION_NAMES:
        value = getattr(_lazy_import("exceptions"), name)
        globals()[name] = value
        return value

    if name in {"logger", "asserts", "exceptions"}:
        return _lazy_import(name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """Improve dir() and IDE autocompletion."""
    public = set(__all__)
    public.update(_submodules.keys())
    for mod in _submodules.values():
        public.update(getattr(mod, "__all__", []))
    return sorted(public)
