"""
Module for custom exceptions for the project.

All custom exceptions in the application should inherit from AppBaseError
or one of its more specific subclasses.

Recommended hierarchy:

AppBaseError
├── ConfigurationError          - problems with config, .json/.env files, etc.
├── ValidationError             - data/input validation failures
│   └── DataFormatError
├── ResourceError               - resources not found, permissions, etc.
│   ├── FileNotFoundError       (may also inherit from OSError if applicable)
│   └── AuthenticationError
├── OperationError              - business logic / operation errors
│   ├── RetryableError           can be retried (e.g., temporary network issues)
│   └── FatalOperationError
└── ExternalServiceError        - errors in external APIs, DB, etc.
    └── RateLimitError

Advantages:
- Easy to catch groups of errors: except AppBaseError
- Useful messages and additional context
- More precise logging and monitoring
"""

from typing import Any, Optional, Union


class AppBaseError(Exception):
    """Base class for all custom exceptions in the project.

    All application exceptions should inherit from this class
    (or one of its more specific subclasses) instead of Exception directly.

    Attributes:

        message: Descriptive error message
        context: Optional dictionary with additional information (useful for logs)
        status_code: Suggested HTTP status code (if applicable in APIs)

    Usage:

        raise MissingConfigError(key="DATABASE_URL", source=".env")
        raise AppBaseError(
            message="Something went wrong",
            context={"key": "value"},
            status_code=500
        )
    """

    def __init__(
        self,
        message: str = "Application error",
        context: Optional[dict[str, Any]] = None,
        status_code: int = 500,
        *args: Any,
    ) -> None:
        super().__init__(message, *args)
        self.message = message
        self.context = context or {}
        self.status_code = status_code

    @property
    def cause(self) -> Optional[BaseException]:
        """Get the exception cause if available."""
        return self.__cause__

    def __str__(self) -> str:
        """Readable representation of the error (used in str(e) and logging)."""
        base = self.message
        if self.context:
            ctx_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            base += f" | context: {ctx_str}"
        return base

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r}, context={self.context!r})"

    def to_dict(self) -> dict[str, Any]:
        """Convert the error to a dictionary (useful for JSON responses, logs, etc.)."""
        cause_info = None
        if self.__cause__ is not None:
            cause_info = repr(self.__cause__)

        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "status_code": self.status_code,
            "cause": cause_info,
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
        config_key: Optional[str] = None,
        file_path: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        context = kwargs
        if config_key:
            context["config_key"] = config_key
        if file_path:
            context["file_path"] = file_path
        super().__init__(message, context=context, status_code=500)


class MissingConfigError(ConfigurationError):
    """Missing a required configuration key."""

    def __init__(self, key: str, source: str = "config") -> None:
        super().__init__(
            message=f"Missing required configuration key: {key!r}",
            config_key=key,
            source=source,
        )


# ────────────────────────────────────────────────
# Validation exceptions (works well with your asserts)
# ────────────────────────────────────────────────


class ValidationError(AppBaseError):
    """Data validation error or invalid state.

    Use when enforce/ASSERT fail or when validating user/API input.
    """

    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        value: Any = None,
        **kwargs: Any,
    ) -> None:
        context = {"field": field, "value": value, **kwargs}
        super().__init__(message, context=context, status_code=422)  # Unprocessable Entity


class DataFormatError(ValidationError):
    """Incorrect data format (malformed JSON, wrong type, etc.)."""

    pass  # you can add more logic if needed


class FatalAssertionError(ValidationError):
    """Raised in debug mode or when fatal behavior is requested."""

    pass


# ────────────────────────────────────────────────
# Resource / access exceptions
# ────────────────────────────────────────────────


class ResourceNotFoundError(AppBaseError):
    """Requested resource does not exist (file, DB record, user, etc.)."""

    def __init__(
        self,
        resource_type: str,
        identifier: Union[str, int],
        **kwargs: Any,
    ) -> None:
        super().__init__(
            message=f"{resource_type} not found: {identifier!r}",
            context={"type": resource_type, "id": identifier, **kwargs},
            status_code=404,
        )


class AuthenticationError(AppBaseError):
    """Authentication / authorization failure."""

    def __init__(self, message: str = "Authentication failed", **kwargs: Any) -> None:
        super().__init__(message, context=kwargs, status_code=401)


class PermissionError(AppBaseError):
    """Permission denied for the requested operation."""

    def __init__(self, message: str = "Permission denied", **kwargs: Any) -> None:
        super().__init__(message, context=kwargs, status_code=403)


# ────────────────────────────────────────────────
# Operational / business errors
# ────────────────────────────────────────────────


class OperationError(AppBaseError):
    """Error during a business operation."""

    pass


class RetryableError(OperationError):
    """Transient error that can be retried (e.g., network timeout)."""

    def __init__(
        self,
        message: str = "Retryable error",
        retry_after: Optional[int] = None,  # suggested seconds
        **kwargs: Any,
    ) -> None:
        context = {"retry_after": retry_after, **kwargs}
        super().__init__(message, context=context, status_code=503)


# ────────────────────────────────────────────────
# External service errors
# ────────────────────────────────────────────────


class ExternalServiceError(AppBaseError):
    """Failure in an external service (API, DB, storage, etc.)."""

    def __init__(
        self,
        service: str,
        message: str = "Error in external service",
        original_exc: Optional[Exception] = None,
        **kwargs: Any,
    ) -> None:
        context = {
            "service": service,
            "original": str(original_exc) if original_exc else None,
            **kwargs,
        }
        super().__init__(message, context=context, status_code=502)
