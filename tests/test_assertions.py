import pytest

from logguard.asserts import ASSERT, ASSERT_IN, ASSERT_RANGE, ASSERT_TYPE, enforce, set_failure_handler
from logguard.exceptions import ValidationError


def test_enforce_success() -> None:
    enforce(True, "esto no debería fallar")
    # no exception


def test_enforce_fail(capture_logs: pytest.LogCaptureFixture) -> None:
    with pytest.raises(ValidationError) as exc_info:
        enforce(False, "condición fallida", extra={"valor": 42})

    assert "condición fallida" in str(exc_info.value)
    assert "valor=42" in capture_logs.text


def test_ASSERT_simple(capture_logs: pytest.LogCaptureFixture) -> None:
    x = 10
    ASSERT(x > 5)
    # no raise

    with pytest.raises(ValidationError):
        ASSERT(x < 0, "x debería ser negativo")


def test_ASSERT_with_message_and_extra(capture_logs: pytest.LogCaptureFixture) -> None:
    extra_data = {"test_id": 777}
    with pytest.raises(ValidationError) as exc:
        ASSERT(False, "prueba fallida", extra=extra_data)

    assert "prueba fallida" in str(exc.value)
    # Extra is in the logs
    assert "test_id=777" in capture_logs.text


def test_custom_failure_handler() -> None:
    from typing import Any

    calls: list[tuple[str, str, dict[str, Any]]] = []

    def custom_handler(msg: str, expr: str, fn: str, ln: int, func: str, extra: dict[str, Any]) -> None:
        calls.append((msg, expr, extra))
        raise ValidationError(msg)

    set_failure_handler(custom_handler)

    with pytest.raises(ValidationError):
        ASSERT(False, "custom test")

    assert len(calls) == 1
    assert "custom test" in calls[0][0]


def test_ASSERT_type_helpers() -> None:
    ASSERT_TYPE(42, int)

    with pytest.raises(ValidationError):
        ASSERT_TYPE("42", int)

    ASSERT_IN("a", ["a", "b", "c"])

    with pytest.raises(ValidationError):
        ASSERT_IN("z", ["a", "b", "c"])


@pytest.mark.parametrize(
    "value, minv, maxv, should_pass",
    [
        (50, 0, 100, True),
        (-1, 0, 100, False),
        (100, 0, 100, True),
        (101, 0, 100, False),
    ],
)
def test_ASSERT_RANGE(value: int, minv: int, maxv: int, should_pass: bool) -> None:
    if should_pass:
        ASSERT_RANGE(value, minv, maxv)
    else:
        with pytest.raises(ValidationError):
            ASSERT_RANGE(value, minv, maxv)


def test_no_raise_in_non_debug() -> None:
    # En modo debug, siempre lanza excepción
    # Este test verifica que __debug__ esté habilitado en testing
    assert __debug__ is True  # True by default in tests


@pytest.mark.parametrize(
    "assert_func, args, kwargs, error_pattern",
    [
        (ASSERT_TYPE, ("not an int", int), {}, "type"),
        (ASSERT_IN, ("z", ["a", "b", "c"]), {}, ("not found", "not in", "container")),
    ],
)
def test_assert_functions_fail(assert_func, args, kwargs, error_pattern) -> None:
    """Test ASSERT_TYPE and ASSERT_IN with failed assertions."""
    with pytest.raises(ValidationError) as exc:
        assert_func(*args, **kwargs)

    error_str = str(exc.value).lower()

    # Handle both single string and tuple of possible patterns
    if isinstance(error_pattern, tuple):
        assert any(pattern in error_str for pattern in error_pattern)
    else:
        assert error_pattern in error_str


def test_enforce_with_expression() -> None:
    """Test enforce with explicit expression."""
    with pytest.raises(ValidationError) as exc:
        enforce(
            False,
            "test message",
            expression="x > 0",
            filename="test.py",
            line=42,
            function="test_func",
        )
    error_dict = exc.value.to_dict()
    assert error_dict["type"] == "ValidationError"
    assert "test message" in error_dict["message"]


def test_reset_failure_handler() -> None:
    """Test resetting failure handler to default."""
    from typing import Any

    from logguard.asserts import _default_failure_handler, set_failure_handler

    custom_called: list[bool] = [False]

    def custom(msg: str, expr: str, fn: str, ln: int, func: str, extra: dict[str, Any]) -> None:
        custom_called[0] = True
        raise ValidationError(msg)

    set_failure_handler(custom)
    # Reset to default
    set_failure_handler(_default_failure_handler)

    with pytest.raises(ValidationError):
        ASSERT(False, "test")


def test_ASSERT_without_message() -> None:
    """Test ASSERT without explicit message."""
    with pytest.raises(ValidationError):
        ASSERT(False)  # No message provided
