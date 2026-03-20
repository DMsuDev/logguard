"""
logguard - Utilities for structured logging, assertions, and semantic exceptions.

This package provides:

1. Configurable logging with AppLogger:
   - Rich console output, file rotation, optional JSON logging
   - Centralized logger configuration for apps and libraries

2. Advanced assertions (asserts module):
   - Environment-aware assertions: ASSERT, CHECK, ENSURE, VERIFY
   - Specialized helpers: ASSERT_NOT_NULL, ASSERT_IN_RANGE, etc.
   - Raises errors in development, logs in production

3. Semantic exceptions (exceptions module):
   - Hierarchical custom exceptions for configuration, validation, and resource issues
   - All exceptions inherit from LogGuardError for consistent error handling

Lazy-loading submodules:
- The asserts, exceptions, and logger submodules are imported only when accessed.
- Compatible with Pylance/IDE autocomplete via TYPE_CHECKING.

Example usage:

    from logguard import AppLogger, ASSERT, ValidationError

    AppLogger.setup(console_level="INFO")
    logger = AppLogger.get_logger(__name__)

    x = -5
    ASSERT(x > 0, "Value must be positive", value=x)

Version: 0.3.0
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

# Type checking imports for IDEs and static analysis (Pylance, mypy)
# ruff: noqa: I001
if TYPE_CHECKING:
    # Submodules
    from . import asserts as asserts
    from . import exceptions as exceptions
    from . import logger as logger

    # Logger
    from .logger import AppLogger as AppLogger

    # Assertions - core
    from .asserts import ASSERT as ASSERT
    from .asserts import AssertionConfig as AssertionConfig
    from .asserts import AssertionManager as AssertionManager
    from .asserts import AssertionMode as AssertionMode
    from .asserts import CHECK as CHECK
    from .asserts import ENSURE as ENSURE
    from .asserts import VERIFY as VERIFY

    # Assertions - specialized
    from .asserts import ASSERT_BETWEEN_EXCLUSIVE as ASSERT_BETWEEN_EXCLUSIVE
    from .asserts import ASSERT_EQUALS as ASSERT_EQUALS
    from .asserts import ASSERT_GREATER as ASSERT_GREATER
    from .asserts import ASSERT_IN as ASSERT_IN
    from .asserts import ASSERT_IN_RANGE as ASSERT_IN_RANGE
    from .asserts import ASSERT_LESS as ASSERT_LESS
    from .asserts import ASSERT_NOT_EMPTY as ASSERT_NOT_EMPTY
    from .asserts import ASSERT_NOT_NULL as ASSERT_NOT_NULL
    from .asserts import ASSERT_NULL as ASSERT_NULL
    from .asserts import ASSERT_TYPE as ASSERT_TYPE

    # Exceptions - base
    from .exceptions import LogGuardError as LogGuardError

    # Exceptions - configuration
    from .exceptions import ConfigurationError as ConfigurationError
    from .exceptions import MissingConfigError as MissingConfigError

    # Exceptions - validation/assertion
    from .exceptions import AssertFailure as AssertFailure
    from .exceptions import ComparisonError as ComparisonError
    from .exceptions import EmptyError as EmptyError
    from .exceptions import EqualsError as EqualsError
    from .exceptions import MembershipError as MembershipError
    from .exceptions import NullError as NullError
    from .exceptions import RangeError as RangeError
    from .exceptions import TypeErrorAssert as TypeErrorAssert
    from .exceptions import ValidationError as ValidationError

    # Exceptions - resource
    from .exceptions import ForbiddenError as ForbiddenError
    from .exceptions import ResourceError as ResourceError
    from .exceptions import ResourceNotFoundError as ResourceNotFoundError

__version__ = "0.3.0"

__all__ = [  # noqa: RUF022
    # Version
    "__version__",
    # Submodules
    "asserts",
    "exceptions",
    "logger",
    # Logger
    "AppLogger",
    # Assertions - core
    "ASSERT",
    "AssertionConfig",
    "AssertionManager",
    "AssertionMode",
    "CHECK",
    "ENSURE",
    "VERIFY",
    # Assertions - specialized
    "ASSERT_BETWEEN_EXCLUSIVE",
    "ASSERT_EQUALS",
    "ASSERT_GREATER",
    "ASSERT_IN",
    "ASSERT_IN_RANGE",
    "ASSERT_LESS",
    "ASSERT_NOT_EMPTY",
    "ASSERT_NOT_NULL",
    "ASSERT_NULL",
    "ASSERT_TYPE",
    # Exceptions - base
    "LogGuardError",
    # Exceptions - configuration
    "ConfigurationError",
    "MissingConfigError",
    # Exceptions - validation/assertion
    "AssertFailure",
    "ComparisonError",
    "EmptyError",
    "EqualsError",
    "MembershipError",
    "NullError",
    "RangeError",
    "TypeErrorAssert",
    "ValidationError",
    # Exceptions - resource
    "ForbiddenError",
    "ResourceError",
    "ResourceNotFoundError",
]

# -------------------------------
# Symbol to submodule mapping
# -------------------------------

_SYMBOL_TO_MODULE: dict[str, str] = {
    # Logger
    "AppLogger": "logger",
    # Assertions - core
    "ASSERT": "asserts",
    "AssertionConfig": "asserts",
    "AssertionManager": "asserts",
    "AssertionMode": "asserts",
    "CHECK": "asserts",
    "ENSURE": "asserts",
    "VERIFY": "asserts",
    # Assertions - specialized
    "ASSERT_BETWEEN_EXCLUSIVE": "asserts",
    "ASSERT_EQUALS": "asserts",
    "ASSERT_GREATER": "asserts",
    "ASSERT_IN": "asserts",
    "ASSERT_IN_RANGE": "asserts",
    "ASSERT_LESS": "asserts",
    "ASSERT_NOT_EMPTY": "asserts",
    "ASSERT_NOT_NULL": "asserts",
    "ASSERT_NULL": "asserts",
    "ASSERT_TYPE": "asserts",
    # Exceptions - base
    "LogGuardError": "exceptions",
    # Exceptions - configuration
    "ConfigurationError": "exceptions",
    "MissingConfigError": "exceptions",
    # Exceptions - validation/assertion
    "AssertFailure": "exceptions",
    "ComparisonError": "exceptions",
    "EmptyError": "exceptions",
    "EqualsError": "exceptions",
    "MembershipError": "exceptions",
    "NullError": "exceptions",
    "RangeError": "exceptions",
    "TypeErrorAssert": "exceptions",
    "ValidationError": "exceptions",
    # Exceptions - resource
    "ForbiddenError": "exceptions",
    "ResourceError": "exceptions",
    "ResourceNotFoundError": "exceptions",
}


# -------------------------------
# Lazy import helpers
# -------------------------------


def _lazy_import(submodule: str) -> Any:
    """Load a submodule on demand and cache it in globals()."""
    try:
        mod = import_module(f".{submodule}", package=__package__)
        globals()[submodule] = mod
        return mod
    except Exception as exc:
        raise ImportError(f"Failed to import logguard.{submodule}: {exc}") from exc


def __getattr__(name: str) -> Any:
    """Support lazy-loading of submodules and attributes."""
    # Lazy-load core submodules
    if name in {"logger", "asserts", "exceptions"}:
        return _lazy_import(name)

    # Lazy-load individual symbols
    if name in _SYMBOL_TO_MODULE:
        submod = _lazy_import(_SYMBOL_TO_MODULE[name])
        attr = getattr(submod, name)
        globals()[name] = attr
        return attr

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    """List available attributes (used by autocomplete and dir())."""
    return sorted(__all__)
