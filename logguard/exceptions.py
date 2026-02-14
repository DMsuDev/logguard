"""
Module for custom exceptions for logguard.

Recommended hierarchy:

AppBaseError
├── ConfigurationError          - problems with config, .json/.env files, etc.
│   └── MissingConfigError      - missing required env var or config key
├── ValidationError             - data/input validation failures
└── ResourceError               - resources not found, permissions, etc.
    ├── ResourceNotFoundError       (may also inherit from OSError if applicable)
    └── ForbiddenError          - permission denied (before PermissionError to avoid shadowing)

Note: Can be expanded with more specific exceptions as needed
Or modified to fit specific use cases, but all should inherit from AppBaseError.

Built-in exceptions are still in work.
"""

from typing import Any


class AppBaseError(Exception):
    """Base class for all custom exceptions of logguard.

    All application exceptions should inherit from this class
    (or one of its more specific subclasses) instead of Exception directly.

    Attributes:

        message: Descriptive error message
        context: Optional dictionary with additional information (useful for logs)
    """

    def __init__(
        self,
        message: str = "Application error",
        context: dict[str, Any] | None = None,
        *args: Any,
    ) -> None:
        super().__init__(message, *args)
        self.message = message
        self.context = context or {}

    def __str__(self) -> str:
        """Readable representation of the error (used in str(e) and logging)."""
        if not self.context:
            return self.message
        ctx = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
        return f"{self.message} | context: {ctx}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r}, context={self.context!r})"

    def to_dict(self) -> dict[str, Any]:
        """Convert the error to a dictionary (useful for JSON responses, logs, etc.)."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
        }


# ────────────────────────────────────────────────
# Configuration and startup exceptions
# ────────────────────────────────────────────────


class ConfigurationError(AppBaseError):
    """Error related to application configuration.

    Examples: invalid JSON file, missing environment variable,
    configuration schema not met, etc.
    """

    def __init__(
        self,
        message: str = "Configuration error",
        config_key: str | None = None,
        file_path: str | None = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs
        if config_key:
            context["config_key"] = config_key
        if file_path:
            context["file_path"] = file_path
        super().__init__(message, context=context)


class MissingConfigError(ConfigurationError):
    """Missing a required configuration key."""

    def __init__(self, key: str, source: str = "config") -> None:
        super().__init__(
            message=f"Missing required configuration key: {key!r}",
            config_key=key,
            source=source,
        )


# ────────────────────────────────────────────────
# Validation exceptions and asserts
# ────────────────────────────────────────────────


class ValidationError(AppBaseError):
    """Data validation error or invalid state.

    Use when enforce/ASSERT fail or when validating user/API input.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        field: str | None = None,
        value: Any = None,
        **kwargs: Any,
    ) -> None:
        context: dict[str, Any] = kwargs.copy()
        if field is not None:
            context["field"] = field
        if value is not None:
            context["value"] = value
        super().__init__(message, context=context)


# ────────────────────────────────────────────────
# Resource / access exceptions
# ────────────────────────────────────────────────


class ResourceError(AppBaseError):
    """Base class for resource-related errors.

    Includes access issues, missing resources, authentication, permissions, etc.
    """

    pass


class ResourceNotFoundError(ResourceError):
    """Requested resource does not exist (file, DB record, user, etc.)."""

    def __init__(
        self,
        resource_type: str,
        identifier: str | int,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=f"{resource_type} not found: {identifier!r}",
            context={"type": resource_type, "id": identifier, **kwargs},
        )


class ForbiddenError(ResourceError):
    """
    Permission denied for the requested operation.
    """

    def __init__(self, message: str = "Permission denied", **kwargs: Any) -> None:
        super().__init__(message, context=kwargs)
