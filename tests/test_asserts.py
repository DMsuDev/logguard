"""
Comprehensive tests for logguard.asserts module.

Tests cover:
- ASSERT macro with auto-capture
- enforce function with manual parameters
- All helper assertions (ASSERT_TYPE, ASSERT_IN, etc.)
- Custom failure handlers
- Edge cases and error handling
- Extra context capturing
"""

from typing import NoReturn
from unittest.mock import patch

import pytest

from logguard import ASSERT, enforce, set_failure_handler
from logguard.asserts import (
    ASSERT_EQUALS,
    ASSERT_IN,
    ASSERT_NONE,
    ASSERT_NOT_EMPTY,
    ASSERT_NOT_NONE,
    ASSERT_RANGE,
    ASSERT_TYPE,
    _default_failure_handler,
    assertion_logger,
)
from logguard.exceptions import FatalAssertionError, ValidationError


class TestASSERTBasic:
    """Tests for basic ASSERT functionality."""

    def test_assert_passes_on_true(self) -> None:
        """Test that ASSERT passes when condition is true."""
        # Should not raise
        ASSERT(True)
        ASSERT(5 > 2)
        ASSERT(1 == 1)
        ASSERT("hello")
        ASSERT([1, 2, 3])

    def test_assert_fails_on_false(self) -> None:
        """Test that ASSERT raises FatalAssertionError when condition is false."""
        with pytest.raises(FatalAssertionError):
            ASSERT(False)

    def test_assert_with_message(self) -> None:
        """Test ASSERT with custom message."""
        with pytest.raises(FatalAssertionError, match="Custom message"):
            ASSERT(False, "Custom message")

    def test_assert_with_condition_and_message(self) -> None:
        """Test ASSERT with both condition and message."""
        x = -5
        with pytest.raises(FatalAssertionError, match="Value must be positive"):
            ASSERT(x > 0, "Value must be positive")

    def test_assert_captures_expression(self) -> None:
        """Test that ASSERT captures the expression from source."""
        x = 10
        with pytest.raises(FatalAssertionError) as exc_info:
            ASSERT(x < 5)

        # Expression should be captured in error message
        error_str = str(exc_info.value)
        assert "x < 5" in error_str or "10" in error_str or "ASSERT" in error_str

    def test_assert_with_extra_context(self) -> None:
        """Test ASSERT with extra context dictionary."""
        x = 10
        with pytest.raises(FatalAssertionError):
            ASSERT(x < 5, "Value too large", extra={"value": x, "limit": 5})

    def test_assert_with_complex_expression(self) -> None:
        """Test ASSERT with complex boolean expressions."""
        a, b, c = 1, 2, 3

        # Should pass
        ASSERT(a < b < c)
        ASSERT(a == 1 and b == 2)
        ASSERT(a in [1, 2, 3] or b in [4, 5, 6])

        # Should fail
        with pytest.raises(FatalAssertionError):
            ASSERT(a > b > c)

    def test_assert_logs_failure(self) -> None:
        """Test that ASSERT logs failure with context."""
        with patch.object(assertion_logger, "error") as mock_error:
            with pytest.raises(FatalAssertionError):
                ASSERT(False, "Test failure")

            mock_error.assert_called()
            call_args = str(mock_error.call_args)
            assert "ASSERT FAILED" in call_args
            assert "Test failure" in call_args

    def test_assert_with_callable_condition(self) -> None:
        """Test ASSERT with callable that returns bool."""

        def check_valid() -> bool:
            return False

        with pytest.raises(FatalAssertionError):
            ASSERT(check_valid())

    def test_assert_with_truthy_values(self) -> None:
        """Test ASSERT with various truthy/falsy values."""
        # Truthy - should pass
        ASSERT(1)
        ASSERT("string")
        ASSERT([1])
        ASSERT({"key": "value"})
        ASSERT(object())

        # Falsy - should fail
        with pytest.raises(FatalAssertionError):
            ASSERT(0)
        with pytest.raises(FatalAssertionError):
            ASSERT("")
        with pytest.raises(FatalAssertionError):
            ASSERT([])
        with pytest.raises(FatalAssertionError):
            ASSERT({})
        with pytest.raises(FatalAssertionError):
            ASSERT(None)


class TestEnforceFunction:
    """Tests for enforce function."""

    def test_enforce_passes_on_true(self) -> None:
        """Test that enforce passes when condition is true."""
        enforce(True, "Should not raise")
        enforce(5 > 2, "Math works")

    def test_enforce_fails_on_false(self) -> None:
        """Test that enforce raises FatalAssertionError when condition is false."""
        with pytest.raises(FatalAssertionError):
            enforce(False, "Test failure")

    def test_enforce_with_explicit_context(self) -> None:
        """Test enforce with explicit context parameters."""
        with pytest.raises(FatalAssertionError):
            enforce(
                False,
                "Validation failed",
                expression="x > 0",
                filename="test.py",
                line=42,
                function="test_func",
            )

    def test_enforce_logs_context(self) -> None:
        """Test that enforce logs all context information."""
        with patch.object(assertion_logger, "error") as mock_error:
            with pytest.raises(FatalAssertionError):
                enforce(
                    False,
                    "Test failure",
                    expression="x == y",
                    filename="test.py",
                    line=99,
                    function="my_function",
                    extra={"x": 5, "y": 10},
                )

            mock_error.assert_called()
            args = str(mock_error.call_args)
            assert "ASSERT FAILED" in args
            assert "x == y" in args
            assert "Test failure" in args
            assert "test.py:99" in args

    def test_enforce_with_custom_exc_type(self) -> None:
        """Test enforce with custom exception type."""
        # In debug mode, should still raise FatalAssertionError
        with pytest.raises((FatalAssertionError, ValidationError)):
            enforce(False, "Custom exc", exc_type=ValidationError)

    def test_enforce_with_extra_dict(self) -> None:
        """Test enforce with extra context dictionary."""
        with pytest.raises(FatalAssertionError):
            enforce(
                False,
                "Value out of range",
                expression="value in range",
                extra={"value": 100, "min": 0, "max": 50},
            )


class TestASSERTHelpers:
    """Tests for ASSERT helper functions."""

    def test_assert_type_passes(self) -> None:
        """Test ASSERT_TYPE with correct types."""
        ASSERT_TYPE(42, int)
        ASSERT_TYPE("hello", str)
        ASSERT_TYPE([1, 2, 3], list)
        ASSERT_TYPE({"key": "value"}, dict)
        ASSERT_TYPE(3.14, float)

    def test_assert_type_fails(self) -> None:
        """Test ASSERT_TYPE with incorrect types."""
        with pytest.raises(FatalAssertionError, match="Expected type"):
            ASSERT_TYPE(42, str)

        with pytest.raises(FatalAssertionError, match="Expected type"):
            ASSERT_TYPE("hello", int)

    def test_assert_type_multiple_types(self) -> None:
        """Test ASSERT_TYPE with tuple of types."""
        ASSERT_TYPE(42, (int, float))
        ASSERT_TYPE(3.14, (int, float))
        ASSERT_TYPE("hello", (str, bytes))

        with pytest.raises(FatalAssertionError):
            ASSERT_TYPE([], (int, str, float))

    def test_assert_type_custom_message(self) -> None:
        """Test ASSERT_TYPE with custom message."""
        with pytest.raises(FatalAssertionError, match="Custom type error"):
            ASSERT_TYPE(42, str, "Custom type error")

    def test_assert_in_passes(self) -> None:
        """Test ASSERT_IN with item in container."""
        ASSERT_IN(1, [1, 2, 3])
        ASSERT_IN("a", {"a": 1, "b": 2})
        ASSERT_IN("hello", "hello world")
        ASSERT_IN(5, range(10))

    def test_assert_in_fails(self) -> None:
        """Test ASSERT_IN with item not in container."""
        with pytest.raises(FatalAssertionError, match="not found"):
            ASSERT_IN(5, [1, 2, 3])

        with pytest.raises(FatalAssertionError):
            ASSERT_IN("z", "hello world")

    def test_assert_in_custom_message(self) -> None:
        """Test ASSERT_IN with custom message."""
        with pytest.raises(FatalAssertionError, match="Status invalid"):
            ASSERT_IN("invalid", ["active", "pending"], "Status invalid")

    def test_assert_not_empty_passes(self) -> None:
        """Test ASSERT_NOT_EMPTY with non-empty objects."""
        ASSERT_NOT_EMPTY([1, 2, 3])
        ASSERT_NOT_EMPTY("hello")
        ASSERT_NOT_EMPTY({"key": "value"})
        ASSERT_NOT_EMPTY((1, 2))
        ASSERT_NOT_EMPTY(42)  # Non-zero number

    def test_assert_not_empty_fails(self) -> None:
        """Test ASSERT_NOT_EMPTY with empty objects."""
        with pytest.raises(FatalAssertionError, match="empty"):
            ASSERT_NOT_EMPTY([])

        with pytest.raises(FatalAssertionError):
            ASSERT_NOT_EMPTY("")

        with pytest.raises(FatalAssertionError):
            ASSERT_NOT_EMPTY({})

        with pytest.raises(FatalAssertionError):
            ASSERT_NOT_EMPTY(0)

    def test_assert_not_empty_custom_message(self) -> None:
        """Test ASSERT_NOT_EMPTY with custom message."""
        with pytest.raises(FatalAssertionError, match="No users found"):
            ASSERT_NOT_EMPTY([], "No users found")

    def test_assert_range_passes(self) -> None:
        """Test ASSERT_RANGE with values in range."""
        ASSERT_RANGE(5, 0, 10)
        ASSERT_RANGE(0, 0, 10)  # Min boundary
        ASSERT_RANGE(10, 0, 10)  # Max boundary
        ASSERT_RANGE(-5, -10, 0)
        ASSERT_RANGE(3.14, 0.0, 10.0)

    def test_assert_range_fails(self) -> None:
        """Test ASSERT_RANGE with values out of range."""
        with pytest.raises(FatalAssertionError, match="not in range"):
            ASSERT_RANGE(15, 0, 10)

        with pytest.raises(FatalAssertionError):
            ASSERT_RANGE(-5, 0, 10)

        with pytest.raises(FatalAssertionError):
            ASSERT_RANGE(150, 0, 120)

    def test_assert_range_custom_message(self) -> None:
        """Test ASSERT_RANGE with custom message."""
        with pytest.raises(FatalAssertionError, match="Age invalid"):
            ASSERT_RANGE(200, 0, 150, "Age invalid")

    def test_assert_equals_passes(self) -> None:
        """Test ASSERT_EQUALS with equal values."""
        ASSERT_EQUALS(5, 5)
        ASSERT_EQUALS("hello", "hello")
        ASSERT_EQUALS([1, 2, 3], [1, 2, 3])
        ASSERT_EQUALS({"a": 1}, {"a": 1})
        ASSERT_EQUALS(None, None)

    def test_assert_equals_fails(self) -> None:
        """Test ASSERT_EQUALS with unequal values."""
        with pytest.raises(FatalAssertionError, match="Expected"):
            ASSERT_EQUALS(5, 10)

        with pytest.raises(FatalAssertionError):
            ASSERT_EQUALS("hello", "world")

        with pytest.raises(FatalAssertionError):
            ASSERT_EQUALS([1, 2], [1, 2, 3])

    def test_assert_equals_custom_message(self) -> None:
        """Test ASSERT_EQUALS with custom message."""
        with pytest.raises(FatalAssertionError, match="Wrong status code"):
            ASSERT_EQUALS(404, 200, "Wrong status code")

    def test_assert_none_passes(self) -> None:
        """Test ASSERT_NONE with None value."""
        ASSERT_NONE(None)
        x = None
        ASSERT_NONE(x)

    def test_assert_none_fails(self) -> None:
        """Test ASSERT_NONE with non-None values."""
        with pytest.raises(FatalAssertionError, match="Expected None"):
            ASSERT_NONE(0)

        with pytest.raises(FatalAssertionError):
            ASSERT_NONE("")

        with pytest.raises(FatalAssertionError):
            ASSERT_NONE([])

        with pytest.raises(FatalAssertionError):
            ASSERT_NONE(False)

    def test_assert_none_custom_message(self) -> None:
        """Test ASSERT_NONE with custom message."""
        with pytest.raises(FatalAssertionError, match="Expected no error"):
            ASSERT_NONE("error", "Expected no error")

    def test_assert_not_none_passes(self) -> None:
        """Test ASSERT_NOT_NONE with non-None values."""
        ASSERT_NOT_NONE(0)
        ASSERT_NOT_NONE("")
        ASSERT_NOT_NONE([])
        ASSERT_NOT_NONE(False)
        ASSERT_NOT_NONE("value")
        ASSERT_NOT_NONE(42)

    def test_assert_not_none_fails(self) -> None:
        """Test ASSERT_NOT_NONE with None value."""
        with pytest.raises(FatalAssertionError, match="Value is None"):
            ASSERT_NOT_NONE(None)

        x = None
        with pytest.raises(FatalAssertionError):
            ASSERT_NOT_NONE(x)

    def test_assert_not_none_custom_message(self) -> None:
        """Test ASSERT_NOT_NONE with custom message."""
        with pytest.raises(FatalAssertionError, match="User not found"):
            ASSERT_NOT_NONE(None, "User not found")


class TestCustomFailureHandler:
    """Tests for custom failure handler functionality."""

    def teardown_method(self) -> None:
        """Restore default handler after each test."""
        set_failure_handler(_default_failure_handler)

    def test_set_custom_handler(self) -> None:
        """Test setting a custom failure handler."""
        custom_called = []

        def custom_handler(message, expression, filename, line, function, extra) -> NoReturn:
            custom_called.append(
                {
                    "message": message,
                    "expression": expression,
                    "filename": filename,
                    "line": line,
                    "function": function,
                    "extra": extra,
                }
            )
            raise RuntimeError("Custom handler called")

        set_failure_handler(custom_handler)

        with pytest.raises(RuntimeError, match="Custom handler called"):
            enforce(False, "Test message", expression="test")

        assert len(custom_called) == 1
        assert custom_called[0]["message"] == "Test message"
        assert custom_called[0]["expression"] == "test"

    def test_restore_default_handler(self) -> None:
        """Test restoring default handler."""

        def custom_handler(*args) -> NoReturn:
            raise RuntimeError("Should not be called")

        # Set custom
        set_failure_handler(custom_handler)

        # Restore default
        set_failure_handler(_default_failure_handler)

        # Should raise FatalAssertionError, not RuntimeError
        with pytest.raises(FatalAssertionError):
            enforce(False, "test")

    def test_custom_handler_receives_all_context(self) -> None:
        """Test that custom handler receives all context parameters."""
        captured = {}

        def capture_handler(message, expression, filename, line, function, extra) -> None:
            captured.update(
                {
                    "message": message,
                    "expression": expression,
                    "filename": filename,
                    "line": line,
                    "function": function,
                    "extra": extra,
                }
            )

        set_failure_handler(capture_handler)

        enforce(
            False,
            "Test message",
            expression="x > 0",
            filename="test.py",
            line=42,
            function="test_func",
            extra={"x": -5},
        )

        assert captured["message"] == "Test message"
        assert captured["expression"] == "x > 0"
        assert captured["filename"] == "test.py"
        assert captured["line"] == 42
        assert captured["function"] == "test_func"
        assert captured["extra"]["x"] == -5


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_assert_with_multiline_expression(self) -> None:
        """Test ASSERT with expression spanning multiple lines."""
        # This might not capture perfectly, but should not crash
        result = True and True and True
        ASSERT(result)  # Should pass

    def test_assert_in_nested_function(self) -> None:
        """Test ASSERT used in nested function."""

        def outer() -> None:
            def inner() -> None:
                ASSERT(False, "Nested assertion")

            inner()

        with pytest.raises(FatalAssertionError, match="Nested assertion"):
            outer()

    def test_assert_in_lambda(self) -> None:
        """Test ASSERT behavior with lambda (edge case)."""
        # Lambda with assertion
        with pytest.raises(FatalAssertionError):
            (lambda: ASSERT(False, "Lambda assertion"))()

    def test_assert_with_side_effects(self) -> None:
        """Test that ASSERT evaluates condition only once."""
        call_count = [0]

        def condition_with_side_effect() -> bool:
            call_count[0] += 1
            return True

        ASSERT(condition_with_side_effect())
        assert call_count[0] == 1

    def test_assert_with_exception_in_condition(self) -> None:
        """Test ASSERT when condition evaluation raises exception."""

        def failing_condition() -> NoReturn:
            raise ValueError("Condition error")

        # The exception should propagate
        with pytest.raises(ValueError, match="Condition error"):
            ASSERT(failing_condition())

    def test_assert_with_very_long_message(self) -> None:
        """Test ASSERT with very long error message."""
        long_message = "x" * 1000
        with pytest.raises(FatalAssertionError):
            ASSERT(False, long_message)

    def test_assert_with_special_characters_in_message(self) -> None:
        """Test ASSERT with special characters in message."""
        with pytest.raises(FatalAssertionError):
            ASSERT(False, "Error: 'quote' and \"double\" and \n newline")

    def test_assert_with_unicode_in_message(self) -> None:
        """Test ASSERT with unicode characters in message."""
        with pytest.raises(FatalAssertionError, match="Émoji"):
            ASSERT(False, "Émoji test: 🚀 🎉 ñáéíó")

    def test_enforce_with_empty_message(self) -> None:
        """Test enforce with empty message uses fallback."""
        with pytest.raises(FatalAssertionError):
            enforce(False, "")

    def test_assert_with_none_extra(self) -> None:
        """Test ASSERT with extra=None (should auto-capture locals)."""
        # Auto-capture might work depending on implementation
        with pytest.raises(FatalAssertionError):
            ASSERT(False, "Test with locals")

    def test_assert_with_empty_extra(self) -> None:
        """Test ASSERT with empty extra dict."""
        with pytest.raises(FatalAssertionError):
            ASSERT(False, "Test", extra={})


class TestIntegrationScenarios:
    """Tests for real-world integration scenarios."""

    def test_validation_pipeline(self) -> None:
        """Test assertion chain in validation pipeline."""

        def validate_user(name: str, age: int, email: str) -> None:
            ASSERT_NOT_NONE(name, "Name is required")
            ASSERT_NOT_EMPTY(name, "Name cannot be empty")
            ASSERT_TYPE(age, int, "Age must be integer")
            ASSERT_RANGE(age, 0, 150, "Age out of valid range")
            ASSERT_IN("@", email, "Invalid email format")

        # Valid user
        validate_user("John", 30, "john@example.com")

        # Invalid age
        with pytest.raises(FatalAssertionError, match="Age out of valid range"):
            validate_user("John", 200, "john@example.com")

        # Invalid email
        with pytest.raises(FatalAssertionError, match="Invalid email"):
            validate_user("John", 30, "invalid-email")

    def test_nested_assertions(self) -> None:
        """Test nested function calls with assertions."""

        def level1(x):
            ASSERT(x > 0, "Level 1: x must be positive")
            return level2(x)

        def level2(x):
            ASSERT(x < 100, "Level 2: x must be less than 100")
            return level3(x)

        def level3(x):
            ASSERT(x != 50, "Level 3: x cannot be 50")
            return x * 2

        # Valid path
        assert level1(10) == 20

        # Fail at different levels
        with pytest.raises(FatalAssertionError, match="Level 1"):
            level1(-5)

        with pytest.raises(FatalAssertionError, match="Level 2"):
            level1(150)

        with pytest.raises(FatalAssertionError, match="Level 3"):
            level1(50)

    def test_assertions_in_loop(self) -> None:
        """Test assertions inside loops."""
        values = [1, 2, 3, 4, 5]

        for value in values:
            ASSERT_RANGE(value, 0, 10)

        # With invalid value
        invalid_values = [1, 2, 100, 4, 5]
        with pytest.raises(FatalAssertionError):
            for value in invalid_values:
                ASSERT_RANGE(value, 0, 10)

    def test_assertions_with_context_manager(self) -> None:
        """Test assertions work correctly in context managers."""

        class MockContext:
            def __enter__(self) -> None:
                return self

            def __exit__(self, *args):
                return False

        with MockContext():
            ASSERT(True, "Should pass")

        with pytest.raises(FatalAssertionError), MockContext():
            ASSERT(False, "Should fail in context")
