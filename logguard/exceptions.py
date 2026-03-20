"""
Custom exceptions for LogGuard assertions and logging.

Provides a semantic exception hierarchy for structured error handling.
All exceptions include rich context accessible via `to_dict()`.

Hierarchy::

    LogGuardError
    +-- ConfigurationError
    |   +-- MissingConfigError
    +-- ValidationError
    |   +-- AssertFailure
    |       +-- NullError
    |       +-- RangeError
    |       +-- TypeErrorAssert
    |       +-- EmptyError
    |       +-- EqualsError
    |       +-- ComparisonError
    |       +-- MembershipError
    +-- ResourceError
        +-- ResourceNotFoundError
        +-- ForbiddenError

Example::

    from logguard.exceptions import ValidationError
    raise ValidationError("Invalid email", field="email")
"""

from __future__ import annotations

from typing import Any


class LogGuardError(Exception):
    """Base class for all LogGuard exceptions.

    Every exception carries a human-readable *message* and an optional
    *context* dictionary that holds structured debugging information.
    """

    def __init__(self, message: str = "LogGuard error", context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        if not self.context:
            return self.message
        ctx = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
        return f"{self.message} | context: {ctx}"

    def __repr__(self) -> str:
        cls = self.__class__.__name__
        if self.context:
            return f"{cls}({self.message!r}, context={self.context!r})"
        return f"{cls}({self.message!r})"

    def to_dict(self) -> dict[str, Any]:
        """Convert the exception to a dictionary for structured logging or serialization."""
        data = {"type": self.__class__.__name__, "message": self.message, "context": self.context.copy()}
        if self.__cause__:
            data["cause"] = {"type": type(self.__cause__).__name__, "message": str(self.__cause__)}
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LogGuardError:
        """Create an exception instance from a dictionary."""
        return cls(message=data.get("message", "LogGuard error recovered"), context=data.get("context", {}))


# ----------------------------------------------
# Configuration errors
# ----------------------------------------------


class ConfigurationError(LogGuardError):
    """Configuration issues (invalid/missing keys, files, etc.)"""


class MissingConfigError(ConfigurationError):
    """Required configuration key or env variable missing"""

    def __init__(self, key: str, source: str = "config") -> None:
        super().__init__(f"Missing configuration key: {key!r}", context={"key": key, "source": source})


# ----------------------------------------------
# Validation / assertion errors
# ----------------------------------------------


class ValidationError(LogGuardError):
    """Base class for validation/assertion failures."""


class AssertFailure(ValidationError):
    """Base for all assertion failures."""


class NullError(AssertFailure):
    """Raised when a value is unexpectedly None."""


class RangeError(AssertFailure):
    """Raised when a value is out of the expected range."""


class TypeErrorAssert(AssertFailure):
    """Raised when a value is not of expected type."""


class EmptyError(AssertFailure):
    """Raised when a value is empty but should not be."""


class EqualsError(AssertFailure):
    """Raised when values are expected to be equal but are not."""


class ComparisonError(AssertFailure):
    """Raised when a comparison assertion fails (greater than, less than, etc.)."""


class MembershipError(AssertFailure):
    """Raised when a value is not found in a container."""


# ----------------------------------------------
# Resource errors
# ----------------------------------------------


class ResourceError(LogGuardError):
    """Base for resource-related errors (missing files, permissions, etc.)"""


class ResourceNotFoundError(ResourceError):
    """Resource does not exist."""

    def __init__(self, resource_type: str, identifier: str | int) -> None:
        super().__init__(
            f"{resource_type} not found: {identifier!r}", context={"type": resource_type, "id": identifier}
        )


class ForbiddenError(ResourceError):
    """Permission denied."""

    def __init__(self, message: str = "Permission denied", **kwargs: Any) -> None:
        super().__init__(message, context=kwargs)
