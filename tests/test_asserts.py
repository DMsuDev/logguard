"""
Summary of tests for logguard.asserts:

- Core assertions: CHECK, ASSERT, ENSURE, VERIFY
- Specialized assertions: ASSERT_NOT_NULL, ASSERT_IN_RANGE, ASSERT_TYPE, etc.
- Environment-aware behavior (dev vs prod)
- Custom failure strategies
- Context handling and edge cases
"""

from collections.abc import Callable
from typing import Any

import pytest

from logguard.asserts import (
    ASSERT,
    ASSERT_BETWEEN_EXCLUSIVE,
    ASSERT_EQUALS,
    ASSERT_GREATER,
    ASSERT_IN,
    ASSERT_IN_RANGE,
    ASSERT_LESS,
    ASSERT_NOT_EMPTY,
    ASSERT_NOT_NULL,
    ASSERT_NULL,
    ASSERT_TYPE,
    CHECK,
    ENSURE,
    VERIFY,
    AssertionConfig,
    AssertionManager,
    AssertionMode,
)
from logguard.exceptions import (
    AssertFailure,
    ComparisonError,
    EmptyError,
    EqualsError,
    MembershipError,
    NullError,
    RangeError,
    TypeErrorAssert,
)

# ------------ Core Assertions ------------


@pytest.mark.parametrize("assert_fn", [CHECK, ASSERT, ENSURE, VERIFY])
def test_assertion_passes_on_true(assert_fn: Callable, dev_environment: None) -> None:
    """All assertions pass when the condition is True."""
    assert_fn(True, "Should pass")


@pytest.mark.parametrize(
    "assert_fn,exc,prod_behaviour",
    [
        (CHECK, AssertFailure, True),
        (ASSERT, AssertFailure, False),
        (ENSURE, AssertFailure, False),
        (VERIFY, AssertFailure, False),
    ],
)
def test_assertion_behaviour(
    assert_fn: Callable,
    exc: type[AssertFailure],
    prod_behaviour: bool,
    capture_logs: pytest.LogCaptureFixture,
) -> None:
    """Verify that assertions behave according to the environment."""

    # En dev
    AssertionManager.configure(AssertionConfig(environment="development", enable_asserts=True))
    if assert_fn in [CHECK, ASSERT, ENSURE, VERIFY]:
        with pytest.raises(exc):
            assert_fn(False, "Dev fail")

    # En prod
    AssertionManager.configure(AssertionConfig(environment="production", enable_asserts=True))
    if prod_behaviour:
        with pytest.raises(exc):
            assert_fn(False, "Prod fail")
    else:
        assert_fn(False, "Prod logs")
        if assert_fn in (ENSURE, VERIFY) and capture_logs:
            assert "Prod logs" in capture_logs.text


@pytest.mark.parametrize(
    "unknown_mode",
    [
        "RAISE",
        "dev-raise",
        "log_only",
        "",
        "unknown",
    ],
)
def test_handle_unknown_modes(unknown_mode: Any) -> None:
    """Test various invalid values for 'mode' (parameterized)."""

    with pytest.raises(ValueError) as exc_info:
        AssertionManager._handle(
            condition=False,
            message="dummy",
            context={},
            mode=unknown_mode,
            exception_class=AssertFailure,
        )

    assert "Unknown assertion mode:" in str(exc_info.value)


# ------------ Specialized Assertions ------------


@pytest.mark.parametrize(
    "fn,value,extra,should_pass,exc_class",
    [
        (ASSERT_NOT_NULL, "x", {}, True, NullError),
        (ASSERT_NOT_NULL, None, {}, False, NullError),
        (ASSERT_NULL, None, {}, True, NullError),
        (ASSERT_NULL, 1, {}, False, NullError),
        (ASSERT_EQUALS, 5, 5, True, EqualsError),
        (ASSERT_EQUALS, 5, 10, False, EqualsError),
        (ASSERT_GREATER, 10, 5, True, ComparisonError),
        (ASSERT_GREATER, 3, 10, False, ComparisonError),
        (ASSERT_LESS, 3, 10, True, ComparisonError),
        (ASSERT_LESS, 10, 3, False, ComparisonError),
        (ASSERT_IN_RANGE, 50, (0, 100), True, RangeError),
        (ASSERT_IN_RANGE, -1, (0, 100), False, RangeError),
        (ASSERT_BETWEEN_EXCLUSIVE, 50, (0, 100), True, RangeError),
        (ASSERT_BETWEEN_EXCLUSIVE, 0, (0, 100), False, RangeError),
        (ASSERT_TYPE, 42, int, True, TypeErrorAssert),
        (ASSERT_TYPE, "x", int, False, TypeErrorAssert),
        (ASSERT_NOT_EMPTY, [1], {}, True, EmptyError),
        (ASSERT_NOT_EMPTY, [], {}, False, EmptyError),
        (ASSERT_IN, "a", ["a", "b"], True, MembershipError),
        (ASSERT_IN, "x", ["a", "b"], False, MembershipError),
    ],
)
def test_specialized_assertions(
    fn: Callable, value: Any, extra: Any, should_pass: bool, exc_class: type[AssertFailure], dev_environment: None
) -> None:
    """Parameterize the cases for specialized assertions."""
    if should_pass:
        if fn in [ASSERT_EQUALS, ASSERT_GREATER, ASSERT_LESS]:
            fn(value, extra)
        elif fn in [ASSERT_IN_RANGE, ASSERT_BETWEEN_EXCLUSIVE]:
            fn(value, *extra)
        elif fn is ASSERT_TYPE or fn is ASSERT_IN:
            fn(value, extra)
        else:
            fn(value)
    else:
        with pytest.raises(exc_class):
            if fn in [ASSERT_EQUALS, ASSERT_GREATER, ASSERT_LESS]:
                fn(value, extra)
            elif fn in [ASSERT_IN_RANGE, ASSERT_BETWEEN_EXCLUSIVE]:
                fn(value, *extra)
            elif fn is ASSERT_TYPE or fn is ASSERT_IN:
                fn(value, extra)
            else:
                fn(value)


# ------------ Configuration & Custom Strategies ------------


def test_assertion_manager_config(dev_environment: None) -> None:
    """configure and reset affect the assertions environment."""
    AssertionManager.configure(AssertionConfig(environment="production"))
    ASSERT(False, "Ignored in prod")
    AssertionManager.reset()
    with pytest.raises(AssertFailure):
        ASSERT(False, "Should raise after reset")


def test_custom_failure_strategy(
    dev_environment: None, prod_environment: None, capture_logs: pytest.LogCaptureFixture
) -> None:
    """Custom raise and log strategies work correctly."""
    calls = []

    def custom_raise(msg: str, ctx: dict, exc_class: type[AssertFailure]) -> None:
        calls.append((msg, ctx))
        raise exc_class(msg, context=ctx)

    AssertionManager.set_failure_strategy(raise_strategy=custom_raise)
    with pytest.raises(AssertFailure):
        CHECK(False, "Custom", key=1)
    assert calls[0][0] == "Custom"

    calls.clear()

    def custom_log(msg: str, ctx: dict, exc_class: type[AssertFailure]) -> None:
        calls.append((msg, ctx))

    AssertionManager.set_failure_strategy(log_strategy=custom_log)
    ENSURE(False, "Custom log", key=2)
    assert calls[0][0] == "Custom log"


# ------------ Edge Cases ------------


def test_assertion_empty_message_and_context(dev_environment: None) -> None:
    """Assertions work with empty messages or without context."""
    with pytest.raises(AssertFailure) as e:
        CHECK(False)
    assert "CHECK failed" in str(e.value)

    with pytest.raises(AssertFailure) as e:
        CHECK(False, "No context")
    assert e.value.context == {}


def test_assertion_manager_is_production_flag() -> None:
    """AssertionManager._is_prod reflects the current environment."""
    AssertionManager.configure(AssertionConfig(environment="production"))
    assert AssertionManager._is_prod() is True
    AssertionManager.configure(AssertionConfig(environment="development"))
    assert AssertionManager._is_prod() is False


# ------------ AssertionMode Enum ------------


@pytest.mark.parametrize(
    "mode, expected",
    [
        ("RAISE", "raise"),
        ("DEBUG_ONLY", "debug_only"),
        ("DEV_RAISE", "dev_raise"),
    ],
)
def test_assertion_mode_values(mode: str, expected: str) -> None:
    """AssertionMode enum exposes correct string values."""
    assert getattr(AssertionMode, mode).value == expected


@pytest.mark.parametrize("mode", [AssertionMode.RAISE, "raise"])
def test_handle_accepts_enum_and_string(mode, dev_environment: None) -> None:
    """_handle accepts both enum and legacy string modes."""
    exc = AssertionManager._handle(
        condition=False,
        message="test",
        context={},
        mode=mode,
        exception_class=AssertFailure,
    )
    assert isinstance(exc, AssertFailure)


def test_staging_environment_acts_like_production() -> None:
    """Staging behaves like production (no assertions raised)."""
    AssertionManager.configure(AssertionConfig(environment="staging"))

    assert AssertionManager._is_prod()
    assert not AssertionManager._is_dev()

    # Should not raise
    ASSERT(False, "Should not raise in staging")


def test_config_environment_constants() -> None:
    """Environment constants include expected values."""
    assert {"development"} <= set(AssertionConfig.DEV_ENVIRONMENTS)
    assert {"production", "staging"} <= set(AssertionConfig.PROD_ENVIRONMENTS)
