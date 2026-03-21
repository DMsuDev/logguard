"""Assertion System for LogGuard.

This module provides a flexible assertion system that adapts its behavior
based on the application environment (development vs production).

Assertion Types:
    CHECK   -> Always raises (fatal) - use for critical invariants
    ASSERT  -> Raises in development, ignored in production - use for debugging
    ENSURE  -> Raises in development, logs in production - use for preconditions
    VERIFY  -> Always evaluated, raises in dev, logs in prod - use for postconditions

Specialized helpers (all use ASSERT behavior):
    ASSERT_NOT_NULL         -> Validates value is not None
    ASSERT_NULL             -> Validates value is None
    ASSERT_IN_RANGE         -> Validates value is within inclusive range [min, max]
    ASSERT_BETWEEN_EXCLUSIVE -> Validates value is within exclusive range (min, max)
    ASSERT_GREATER          -> Validates a > b
    ASSERT_LESS             -> Validates a < b
    ASSERT_EQUALS           -> Validates actual == expected
    ASSERT_TYPE             -> Validates isinstance(value, expected)
    ASSERT_NOT_EMPTY        -> Validates value is truthy (not empty)
    ASSERT_IN               -> Validates item is in container

Example::

    from logguard.asserts import ASSERT, CHECK, AssertionManager

    AssertionManager.configure(AssertionConfig(environment="development"))
    CHECK(user is not None, "User required", user_id=123)
    ASSERT(age > 0, "Age must be positive", age=age)

Configuration:

    Set ``APP_ENV`` environment variable to control behavior:

    - ``"development"``, ``"dev"``, ``"local"``, ``"test"`` -> Development mode (raises)
    - ``"production"``, ``"prod"`` -> Production mode (logs only for ENSURE/VERIFY)
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .exceptions import (
    AssertFailure,
    ComparisonError,
    EmptyError,
    EqualsError,
    MembershipError,
    NullError,
    RangeError,
    TypeErrorAssert,
)

# ========================================================================
# Assertion Mode
# ========================================================================


class AssertionMode(str, Enum):
    """Assertion evaluation modes.

    Controls how the assertion engine handles failed conditions depending on
    the current environment.

    Members:
        RAISE: Always raise an exception (used by :func:`CHECK`).
        DEBUG_ONLY: Raise in development when ``enable_asserts`` is ``True``;
            completely skipped otherwise (used by :func:`ASSERT`).
        DEV_RAISE: Raise in development, log in production
            (used by :func:`ENSURE` / :func:`VERIFY`).
    """

    RAISE = "raise"
    DEBUG_ONLY = "debug_only"
    DEV_RAISE = "dev_raise"


# ========================================================================
# Configuration
# ========================================================================


@dataclass(frozen=True)
class AssertionConfig:
    """Configuration for the assertion system.

    Attributes:
        environment: Current environment name. Controls assertion behavior.
            Values like ``"dev"``, ``"development"``, ``"local"``, ``"test"``
            enable strict mode.  Values like ``"prod"``, ``"production"``
            enable lenient mode.
        enable_asserts: Master switch to enable/disable ``ASSERT`` evaluations.
            When ``False``, ``ASSERT`` calls are completely skipped.

    Example::

        config = AssertionConfig(environment="production", enable_asserts=True)
        AssertionManager.configure(config)
    """

    #: Recognized environments that map to *development* mode.
    DEV_ENVIRONMENTS: tuple[str, ...] = ("dev", "development", "local", "test")
    #: Recognized environments that map to *production* mode.
    PROD_ENVIRONMENTS: tuple[str, ...] = ("prod", "production", "staging")

    environment: str = "development"
    enable_asserts: bool = True


#: Type alias for failure strategy callbacks.
#: A failure strategy receives a message and context dict, and handles the failure.
FailureStrategy = Callable[[str, dict[str, Any], type[AssertFailure]], None]


def _default_raise_strategy(
    message: str,
    context: dict[str, Any],
    exception_class: type[AssertFailure] = AssertFailure,
) -> None:
    """
    Default strategy that raises an exception on assertion failure.

    Args:
        message: Error message describing the failure.
        context: Additional context data for debugging.
        exception_class: The exception class to raise.

    Raises:
        AssertFailure: Or a subclass based on exception_class parameter.
    """
    raise exception_class(message, context=context)


def _default_log_strategy(
    message: str,
    context: dict[str, Any],
    exception_class: type[AssertFailure] = AssertFailure,
) -> None:
    """Default strategy that logs assertion failures without raising.

    Args:
        message: Error message describing the failure.
        context: Additional context data for debugging.
        exception_class: The exception class (used for logging type info).
    """
    logger = logging.getLogger("logguard.assertions")
    logger.error(
        "[ASSERTION FAILED] %s | type=%s | context=%s",
        message,
        exception_class.__name__,
        context,
    )


# ========================================================================
# Assertion Manager
# ========================================================================


class AssertionManager:
    """
    Central assertion engine for LogGuard.

    This class manages assertion configuration and behavior across the application.
    It is closed for modification but open for extension via configure() and
    set_failure_strategy().

    The manager supports three assertion modes:
        - "raise": Always raises an exception (used by CHECK)
        - "debug_only": Raises in dev when enable_asserts=True (used by ASSERT)
        - "dev_raise": Raises in dev, logs in prod (used by ENSURE/VERIFY)

    Class Attributes:
        _config: Current assertion configuration.
        _raise_strategy: Callback for raising exceptions.
        _log_strategy: Callback for logging failures.

    Example:
        >>> AssertionManager.configure(AssertionConfig(environment="production"))
        >>> AssertionManager.set_failure_strategy(raise_strategy=my_custom_handler)
    """

    _config: AssertionConfig = AssertionConfig(
        environment=os.getenv("APP_ENV", "development").lower(),
        enable_asserts=True,
    )

    _raise_strategy: FailureStrategy = _default_raise_strategy
    _log_strategy: FailureStrategy = _default_log_strategy

    # -----------------------------------------

    @classmethod
    def configure(cls, config: AssertionConfig) -> None:
        """
        Configure the assertion system.

        Args:
            config: New configuration to apply.

        Example:
            >>> AssertionManager.configure(
            ...     AssertionConfig(environment="production", enable_asserts=False)
            ... )
        """
        cls._config = config

    @classmethod
    def set_failure_strategy(
        cls,
        *,
        raise_strategy: FailureStrategy | None = None,
        log_strategy: FailureStrategy | None = None,
    ) -> None:
        """
        Set custom failure handling strategies.

        Use this to customize how assertion failures are handled. For example,
        to send failures to an error tracking service.

        Args:
            raise_strategy: Custom callback for raising exceptions.
                Signature: (message: str, context: dict, exception_class: type) -> None
            log_strategy: Custom callback for logging failures.
                Signature: (message: str, context: dict, exception_class: type) -> None

        Example:
            >>> def my_handler(msg, ctx, exc_cls):
            ...     sentry.capture_message(msg, extra=ctx)
            ...     raise exc_cls(msg, context=ctx)
            >>> AssertionManager.set_failure_strategy(raise_strategy=my_handler)
        """
        if raise_strategy:
            cls._raise_strategy = raise_strategy
        if log_strategy:
            cls._log_strategy = log_strategy

    @classmethod
    def reset(cls) -> None:
        """
        Reset the assertion manager to default configuration.

        Useful for testing to restore initial state.
        """
        cls._config = AssertionConfig(
            environment=os.getenv("APP_ENV", "development").lower(),
            enable_asserts=True,
        )
        cls._raise_strategy = _default_raise_strategy
        cls._log_strategy = _default_log_strategy

    # -----------------------------------------

    @classmethod
    def _is_dev(cls) -> bool:
        """Check if running in development environment."""
        return cls._config.environment in AssertionConfig.DEV_ENVIRONMENTS

    @classmethod
    def _is_prod(cls) -> bool:
        """Check if running in production environment."""
        return cls._config.environment in AssertionConfig.PROD_ENVIRONMENTS

    @classmethod
    def _handle(
        cls,
        *,
        condition: bool,
        message: str,
        context: dict[str, Any],
        mode: AssertionMode | str,
        exception_class: type[AssertFailure] = AssertFailure,
    ) -> AssertFailure | None:
        """Internal handler for assertion evaluation.

        Returns the exception to raise (or ``None``).  The caller is
        responsible for raising, this keeps internal frames out of the
        user-visible traceback.

        Args:
            condition: The condition to evaluate. If ``True``, assertion passes.
            message: Error message if assertion fails.
            context: Additional context for debugging.
            mode: Assertion mode (:class:`AssertionMode` or legacy string).
            exception_class: Exception class to raise on failure.

        Returns:
            An exception instance when the assertion failed and should be
            raised by the caller, or ``None`` otherwise.

        Raises:
            ValueError: If an unknown mode is specified.
        """
        if condition:
            return None

        # Accept both enum values and legacy strings
        try:
            mode = AssertionMode(mode)
        except ValueError:
            raise ValueError(f"Unknown assertion mode: {mode}") from None

        if mode is AssertionMode.RAISE:
            return cls._build_failure(message, context, exception_class)

        if mode is AssertionMode.DEV_RAISE:
            if cls._is_dev():
                return cls._build_failure(message, context, exception_class)
            cls._log_strategy(message, context, exception_class)

        elif mode is AssertionMode.DEBUG_ONLY and cls._is_dev() and cls._config.enable_asserts:
            return cls._build_failure(message, context, exception_class)

        return None

    @classmethod
    def _build_failure(
        cls,
        message: str,
        context: dict[str, Any],
        exception_class: type[AssertFailure],
    ) -> AssertFailure:
        """Build the failure exception via the configured raise strategy.

        Delegates to ``_raise_strategy`` (which may be user-supplied) and
        captures the resulting exception so that it can be re-raised by the
        public assertion function with a clean traceback.
        """
        try:
            cls._raise_strategy(message, context, exception_class)
        except exception_class as exc:
            exc.__traceback__ = None
            return exc
        # Fallback: strategy did not raise (custom strategy that just logs, etc.)
        return exception_class(message, context=context)


# ========================================================================
# Base Assertions
# ========================================================================


def CHECK(condition: bool, message: str = "", **context: Any) -> None:
    """
    Fatal assertion that always raises on failure.

    Use CHECK for critical invariants that must never be violated,
    regardless of environment. This is the strictest assertion type.

    Args:
        condition: Condition to verify. Must be True for assertion to pass.
        message: Error message describing what went wrong.
        **context: Additional key-value pairs for debugging context.

    Raises:
        AssertFailure: Always raised when condition is False.

    Example:
        >>> CHECK(config is not None, "Configuration required", component="auth")
        >>> CHECK(len(items) > 0, "Items list cannot be empty", items=items)
    """
    _exc = AssertionManager._handle(
        condition=condition,
        message=message or "CHECK failed",
        context=context,
        mode=AssertionMode.RAISE,
        exception_class=AssertFailure,
    )
    if _exc is not None:
        raise _exc


def ASSERT(condition: bool, message: str = "", **context: Any) -> None:
    """
    Debug assertion that raises in development, ignored in production.

    Use ASSERT for development-time checks that help catch bugs early
    but shouldn't impact production performance or behavior.

    Args:
        condition: Condition to verify. Must be True for assertion to pass.
        message: Error message describing what went wrong.
        **context: Additional key-value pairs for debugging context.

    Raises:
        AssertFailure: Raised in development when enable_asserts=True and
            condition is False. Silently ignored in production.

    Example:
        >>> ASSERT(user_id > 0, "Invalid user ID", user_id=user_id)
        >>> ASSERT(isinstance(data, dict), "Expected dict", got=type(data))
    """
    _exc = AssertionManager._handle(
        condition=condition,
        message=message or "ASSERT failed",
        context=context,
        mode=AssertionMode.DEBUG_ONLY,
        exception_class=AssertFailure,
    )
    if _exc is not None:
        raise _exc


def ENSURE(condition: bool, message: str = "", **context: Any) -> None:
    """
    Precondition assertion that raises in dev, logs in production.

    Use ENSURE to validate preconditions at function entry points.
    In development, violations are fatal. In production, they're logged
    but execution continues.

    Args:
        condition: Precondition to verify. Must be True to proceed.
        message: Error message describing the violated precondition.
        **context: Additional key-value pairs for debugging context.

    Raises:
        AssertFailure: Raised in development when condition is False.
            In production, logs error and continues.

    Example:
        >>> def process_order(order: Order) -> None:
        ...     ENSURE(order.is_valid(), "Invalid order", order_id=order.id)
        ...     ENSURE(order.items, "Order has no items", order_id=order.id)
    """
    _exc = AssertionManager._handle(
        condition=condition,
        message=message or "ENSURE failed",
        context=context,
        mode=AssertionMode.DEV_RAISE,
        exception_class=AssertFailure,
    )
    if _exc is not None:
        raise _exc


def VERIFY(condition: bool, message: str = "", **context: Any) -> None:
    """
    Postcondition assertion that raises in dev, logs in production.

    Use VERIFY to validate postconditions and return values.
    Unlike ASSERT, VERIFY is always evaluated (not skipped in production).
    In development, violations raise. In production, they're logged.

    Args:
        condition: Postcondition to verify. Must be True to confirm success.
        message: Error message describing the violated postcondition.
        **context: Additional key-value pairs for debugging context.

    Raises:
        AssertFailure: Raised in development when condition is False.
            In production, logs error and continues.

    Example:
        >>> result = calculate_total(items)
        >>> VERIFY(result >= 0, "Total cannot be negative", result=result)
        >>> return result
    """
    _exc = AssertionManager._handle(
        condition=condition,
        message=message or "VERIFY failed",
        context=context,
        mode=AssertionMode.DEV_RAISE,
        exception_class=AssertFailure,
    )
    if _exc is not None:
        raise _exc


# ========================================================================
# Specialized Assertions
# ========================================================================


def ASSERT_NOT_NULL(value: Any, message: str = "") -> None:
    """
    Assert that a value is not None.

    Args:
        value: Value to check.
        message: Custom error message.

    Raises:
        NullError: In development when value is None.

    Example:
        >>> ASSERT_NOT_NULL(user, "User is required")
        >>> ASSERT_NOT_NULL(config.api_key, "API key not configured")
    """
    _exc = AssertionManager._handle(
        condition=value is not None,
        message=message or "Value must not be None",
        context={"value": value},
        mode=AssertionMode.DEBUG_ONLY,
        exception_class=NullError,
    )
    if _exc is not None:
        raise _exc


def ASSERT_NULL(value: Any, message: str = "") -> None:
    """
    Assert that a value is None.

    Useful for verifying cleanup or ensuring optional values are unset.

    Args:
        value: Value to check.
        message: Custom error message.

    Raises:
        NullError: In development when value is not None.

    Example:
        >>> ASSERT_NULL(cache.get(key), "Cache should be empty")
    """
    _exc = AssertionManager._handle(
        condition=value is None,
        message=message or "Value must be None",
        context={"value": value},
        mode=AssertionMode.DEBUG_ONLY,
        exception_class=NullError,
    )
    if _exc is not None:
        raise _exc


def ASSERT_EQUALS(actual: Any, expected: Any, message: str = "") -> None:
    """
    Assert that two values are equal.

    Args:
        actual: The actual value.
        expected: The expected value.
        message: Custom error message.

    Raises:
        EqualsError: In development when actual != expected.

    Example:
        >>> ASSERT_EQUALS(response.status, 200, "Expected success status")
        >>> ASSERT_EQUALS(len(items), 5, "Should have 5 items")
    """
    _exc = AssertionManager._handle(
        condition=actual == expected,
        message=message or f"Expected {expected!r}, got {actual!r}",
        context={"actual": actual, "expected": expected},
        mode=AssertionMode.DEBUG_ONLY,
        exception_class=EqualsError,
    )
    if _exc is not None:
        raise _exc


def ASSERT_GREATER(a: Any, b: Any, message: str = "") -> None:
    """
    Assert that a is greater than b.

    Args:
        a: First value (should be greater).
        b: Second value (should be less).
        message: Custom error message.

    Raises:
        ComparisonError: In development when a <= b.

    Example:
        >>> ASSERT_GREATER(balance, 0, "Balance must be positive")
        >>> ASSERT_GREATER(end_date, start_date, "Invalid date range")
    """
    _exc = AssertionManager._handle(
        condition=a > b,
        message=message or f"{a} is not greater than {b}",
        context={"a": a, "b": b},
        mode=AssertionMode.DEBUG_ONLY,
        exception_class=ComparisonError,
    )
    if _exc is not None:
        raise _exc


def ASSERT_LESS(a: Any, b: Any, message: str = "") -> None:
    """
    Assert that a is less than b.

    Args:
        a: First value (should be less).
        b: Second value (should be greater).
        message: Custom error message.

    Raises:
        ComparisonError: In development when a >= b.

    Example:
        >>> ASSERT_LESS(retry_count, max_retries, "Too many retries")
        >>> ASSERT_LESS(age, 150, "Invalid age")
    """
    _exc = AssertionManager._handle(
        condition=a < b,
        message=message or f"{a} is not less than {b}",
        context={"a": a, "b": b},
        mode=AssertionMode.DEBUG_ONLY,
        exception_class=ComparisonError,
    )
    if _exc is not None:
        raise _exc


def ASSERT_IN_RANGE(
    value: int | float,
    min_value: int | float,
    max_value: int | float,
    message: str = "",
) -> None:
    """
    Assert that a value is within an inclusive range [min, max].

    Args:
        value: Value to check.
        min_value: Minimum allowed value (inclusive).
        max_value: Maximum allowed value (inclusive).
        message: Custom error message.

    Raises:
        RangeError: In development when value is outside range.

    Example:
        >>> ASSERT_IN_RANGE(percentage, 0, 100, "Invalid percentage")
        >>> ASSERT_IN_RANGE(age, 18, 65, "Age out of valid range")
    """
    _exc = AssertionManager._handle(
        condition=min_value <= value <= max_value,
        message=message or f"{value} not in range [{min_value}, {max_value}]",
        context={"value": value, "min": min_value, "max": max_value},
        mode=AssertionMode.DEBUG_ONLY,
        exception_class=RangeError,
    )
    if _exc is not None:
        raise _exc


def ASSERT_BETWEEN_EXCLUSIVE(
    value: int | float,
    min_value: int | float,
    max_value: int | float,
    message: str = "",
) -> None:
    """
    Assert that a value is within an exclusive range (min, max).

    The boundaries are excluded: min < value < max.

    Args:
        value: Value to check.
        min_value: Minimum boundary (exclusive).
        max_value: Maximum boundary (exclusive).
        message: Custom error message.

    Raises:
        RangeError: In development when value is outside range.

    Example:
        >>> ASSERT_BETWEEN_EXCLUSIVE(ratio, 0.0, 1.0, "Ratio must be between 0 and 1")
    """
    _exc = AssertionManager._handle(
        condition=min_value < value < max_value,
        message=message or f"{value} not in exclusive range ({min_value}, {max_value})",
        context={"value": value, "min": min_value, "max": max_value},
        mode=AssertionMode.DEBUG_ONLY,
        exception_class=RangeError,
    )
    if _exc is not None:
        raise _exc


def ASSERT_TYPE(value: Any, expected: type | tuple[type, ...], message: str = "") -> None:
    """
    Assert that a value is of the expected type.

    Args:
        value: Value to check.
        expected: Expected type or tuple of types.
        message: Custom error message.

    Raises:
        TypeErrorAssert: In development when value is not of expected type.

    Example:
        >>> ASSERT_TYPE(config, dict, "Config must be a dictionary")
        >>> ASSERT_TYPE(value, (int, float), "Expected numeric type")
    """
    _exc = AssertionManager._handle(
        condition=isinstance(value, expected),
        message=message or f"Expected type {expected}, got {type(value)}",
        context={"value": value, "expected": expected, "actual": type(value)},
        mode=AssertionMode.DEBUG_ONLY,
        exception_class=TypeErrorAssert,
    )
    if _exc is not None:
        raise _exc


def ASSERT_NOT_EMPTY(value: Any, message: str = "") -> None:
    """
    Assert that a value is not empty (truthy).

    Works with strings, lists, dicts, sets, and any object with __bool__ or __len__.

    Args:
        value: Value to check.
        message: Custom error message.

    Raises:
        EmptyError: In development when value is empty/falsy.

    Example:
        >>> ASSERT_NOT_EMPTY(users, "No users found")
        >>> ASSERT_NOT_EMPTY(name.strip(), "Name cannot be blank")
    """
    _exc = AssertionManager._handle(
        condition=bool(value),
        message=message or f"{type(value).__name__} is empty",
        context={
            "value": value,
            "length": len(value) if hasattr(value, "__len__") else None,
        },
        mode=AssertionMode.DEBUG_ONLY,
        exception_class=EmptyError,
    )
    if _exc is not None:
        raise _exc


def ASSERT_IN(item: Any, container: Any, message: str = "") -> None:
    """
    Assert that an item exists in a container.

    Args:
        item: Item to find.
        container: Container to search (list, set, dict, str, etc.).
        message: Custom error message.

    Raises:
        MembershipError: In development when item is not in container.

    Example:
        >>> ASSERT_IN(status, ["pending", "active", "completed"], "Invalid status")
        >>> ASSERT_IN(user_id, allowed_users, "User not authorized")
    """
    _exc = AssertionManager._handle(
        condition=item in container,
        message=message or f"{item!r} not found in container",
        context={"item": item, "container_type": type(container).__name__},
        mode=AssertionMode.DEBUG_ONLY,
        exception_class=MembershipError,
    )
    if _exc is not None:
        raise _exc
