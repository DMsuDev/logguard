"""
Assertion system with rich context, logging, and customizable failure handling.

Provides:
- ASSERT(condition, message="")          - macro-style with automatic capture
- enforce(condition, message, ...)       - explicit version (no auto capture)
- set_failure_handler(handler)           - customize behavior

Integrates:
- AppLogger for detailed logging
- custom exceptions (ValidationError / FatalAssertionError)
- different behavior in __debug__ vs production
"""

import inspect
import traceback
from pathlib import Path
from typing import Any, Callable, Optional, Union

from .exceptions import AppBaseError, FatalAssertionError, ValidationError
from .logger import AppLogger

# Dedicated logger for assertions (easy to filter/rotate/monitor)
assertion_logger = AppLogger.get_logger("assertions")

# Type alias for the failure handler
FailureHandler = Callable[[str, str, str, int, str, dict[str, Any]], None]

# Constants for assertion context capture
MAX_LOCALS_CAPTURED = 5  # Maximum number of local variables to capture
MAX_VAR_VALUE_LENGTH = 100  # Maximum length of stringified variable value


def _default_failure_handler(
    message: str,
    expression: str,
    filename: str,
    line: int,
    function: str,
    extra: dict[str, Any],
) -> None:
    """Default handler for assertion failures.

    - Logs the failure with context in a compact format.
    - Raises FatalAssertionError in debug mode.
    - Only logs in production mode.
    """
    short_file = Path(filename).name
    location = f"{short_file}:{line} in {function}()"

    # Build the main log message as parts for easy joining
    main_parts = [
        "[ASSERT FAILED]",
        f"{expression!r}",
        message,
        f"at {location}",
    ]

    # Add extra context if provided (sorted for consistency)
    extra_str = ""
    if extra:
        extra_parts = [f"{k}={v!r}" for k, v in sorted(extra.items())]
        extra_str = " | " + " ".join(extra_parts)

    # Log the error in a single line for better scannability
    assertion_logger.error(" ".join(main_parts) + extra_str)

    # In debug mode: raise fatal exception with clean traceback
    if __debug__:
        try:
            # Capture traceback excluding internals
            stack = traceback.format_stack(limit=10)[:-3]
            tb_str = "".join(stack).rstrip()
            assertion_logger.debug("Assertion traceback (clean):\n%s", tb_str)
        except Exception:
            assertion_logger.debug("Failed to capture clean traceback")

        raise FatalAssertionError(" ".join(main_parts) + extra_str) from None

    # In production: optional soft raise (commented; configure as needed)
    # raise ValidationError(message, context={...})


# Global failure handler
_failure_handler: FailureHandler = _default_failure_handler


def set_failure_handler(handler: FailureHandler) -> None:
    """Replaces the global assertion failure handler."""
    global _failure_handler
    _failure_handler = handler


def enforce(
    condition: bool,
    message: str = "Failed condition",
    *,
    expression: str = "<expression not captured>",
    filename: str = "<unknown file>",
    line: int = 0,
    function: str = "<unknown function>",
    extra: Optional[dict[str, Any]] = None,
    exc_type: type[AppBaseError] = ValidationError,
) -> None:
    """Explicitly checks a condition and calls the failure handler if it fails.

    Args:
        condition: The condition to check (evaluated as bool).
        message: Custom error message.
        expression: Source code of the condition.
        filename, line, function: Caller location info.
        extra: Additional context for logs/exceptions.
        exc_type: Exception type to raise on failure.
    """
    if condition:
        return

    extra = extra or {}

    # Fallback message if none provided
    if not message or message == "Failed condition":
        message = f"Assertion failed: {expression}"

    # Call the configured handler
    _failure_handler(message, expression, filename, line, function, extra)

    # Optional: raise in production (configurable)
    if not __debug__:
        raise exc_type(
            message=message,
            context={
                "expression": expression,
                "location": f"{filename}:{line}",
                "function": function,
                **extra,
            },
        )


def _split_captured_args(captured: str) -> tuple[str, str]:
    """Attempts to split the captured arguments into condition and message.

    Assumes the message is the last positional argument if it's a string literal.
    Handles simple cases but may not cover complex expressions or keyword args.

    Returns:
        (condition_str, message_str) - message_str is empty if no valid split.
    """
    if "," not in captured:
        return captured, ""

    # Split from the right, assuming last part is message
    parts = captured.rsplit(",", maxsplit=1)
    cond_part = parts[0].strip()
    msg_part = parts[1].strip()

    # Check if msg_part is a string literal (basic check)
    if (msg_part.startswith('"') and msg_part.endswith('"')) or (
        msg_part.startswith("'") and msg_part.endswith("'")
    ):
        message = msg_part[1:-1]  # Strip quotes
        return cond_part, message

    # No valid message split (e.g., keyword args or complex)
    return captured, ""


def extract_assert_arg(lines: list[str]) -> Optional[str]:
    """Extracts the arguments inside the last ASSERT(...) call from the code context.

    This is a best-effort parser to capture the expression for better logs.
    Handles common cases but may fail on complex or multi-line expressions.
    """
    if not lines:
        return None

    full_src = "".join(lines).strip()
    if not full_src:
        return None

    # Find positions of "ASSERT(" (skipping likely strings/comments)
    positions = []
    i = 0
    while True:
        pos = full_src.find("ASSERT(", i)
        if pos == -1:
            break

        # Basic filter for comments/strings
        before = full_src[max(0, pos - 20) : pos]
        last_line = before.split("\n")[-1]
        if "#" in last_line or (before.count('"') % 2 == 1) or (before.count("'") % 2 == 1):
            i = pos + 7
            continue

        positions.append(pos)
        i = pos + 7

    if not positions:
        return None

    # Use the last position
    start = positions[-1]
    i = start + 7
    depth = 1
    while i < len(full_src) and depth > 0:
        ch = full_src[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        i += 1

    if depth != 0:
        # Fallback for unclosed (multi-line?)
        line_start = full_src.rfind("\n", 0, start) + 1
        line_end = full_src.find("\n", start)
        if line_end == -1:
            line_end = len(full_src)
        candidate = full_src[line_start:line_end].strip()
        if candidate.startswith("ASSERT("):
            return candidate[7:].rstrip(")").strip()
        return None

    # Extract inner content
    captured = full_src[start + 7 : i - 1].strip()

    # Remove trailing comments
    return captured.split("#", 1)[0].rstrip()


def ASSERT(
    condition: bool,
    message: str = "",
    *,
    extra: Optional[dict[str, Any]] = None,
    exc_type: type[AppBaseError] = ValidationError,
) -> None:
    """Assertion with automatic source capture for expression and location.

    This is a convenience function that automatically captures the source code
    expression, filename, line number, and function name. Use for development-time
    assertions that benefit from detailed context.

    Usage examples:
        ASSERT(x > 0)
        ASSERT(len(users) > 0, "No users registered")
        ASSERT(isinstance(data, dict), extra={"data_type": type(data).__name__})

    Features:
        - Automatically captures the expression from source code
        - Separates condition from message if possible
        - Falls back gracefully if capture fails
        - Provides rich context for debugging

    Args:
        condition: The condition to check (any value, evaluated as bool).
        message: Custom error message (optional).
        extra: Additional context to include in logs/exceptions.
        exc_type: Exception type to raise on failure.
    """
    if bool(condition):
        return

    frame = inspect.currentframe()
    if frame is None or frame.f_back is None:
        enforce(
            condition=False,
            message=message or "Assertion without context",
            expression="<expression not captured>",
        )
        return

    caller = frame.f_back
    expression = "<expression not captured>"
    captured_message = ""  # For fallback if no message provided

    try:
        info = inspect.getframeinfo(caller, context=12)  # Increased context for reliability
        code_lines = info.code_context or []

        captured = extract_assert_arg(code_lines)
        if captured:
            # Split into condition and possible message
            expr_part, captured_message = _split_captured_args(captured)
            expression = expr_part
        else:
            # Fallback: try to get the exact line
            target_lineno = caller.f_lineno
            base_lineno = info.lineno - len(code_lines) + 1
            for offset, ln in enumerate(code_lines):
                if base_lineno + offset == target_lineno:
                    stripped = ln.strip()
                    if stripped.startswith("ASSERT("):
                        inner = stripped[7:].rstrip(")").strip()
                        expr_part, captured_message = _split_captured_args(inner)
                        expression = expr_part
                    else:
                        expression = stripped
                    break

    except Exception as e:
        assertion_logger.exception(f"Failed to capture expression: {e}")
        expression = "<failed to capture expression>"

    # Use captured message if no explicit message provided
    final_message = message or captured_message or "Assertion failed"

    # Auto-capture local variables if extra is not provided (opt-in via empty dict)
    if extra is None and caller:
        try:
            # Capture relevant local variables (primitives and simple types)
            locals_dict = caller.f_locals
            captured_vars = {}
            for var_name, var_value in locals_dict.items():
                # Skip private, dunder, and complex objects
                if not var_name.startswith("_") and isinstance(
                    var_value, (int, float, str, bool, type(None), list, dict, tuple)
                ):
                    # Limit size to avoid huge logs
                    str_val = str(var_value)
                    if len(str_val) <= MAX_VAR_VALUE_LENGTH:
                        captured_vars[var_name] = var_value
            if captured_vars and len(captured_vars) <= MAX_LOCALS_CAPTURED:
                extra = {"locals": captured_vars}
        except Exception:
            pass  # Silently fail if can't capture

    enforce(
        condition=condition,
        message=final_message,
        expression=expression,
        filename=inspect.getfile(caller),
        line=caller.f_lineno,
        function=caller.f_code.co_name,
        extra=extra,
        exc_type=exc_type,
    )


# ══════════════════════════════════════════════════════════════════════════════
# Convenient assertion helpers
# ══════════════════════════════════════════════════════════════════════════════


def ASSERT_TYPE(obj: Any, expected_type: Union[type, tuple[type, ...]], message: str = "") -> None:
    """Assert that obj is an instance of expected_type.

    Args:
        obj: Object to check.
        expected_type: Expected type or tuple of types.
        message: Custom error message.

    Example:
        ASSERT_TYPE(user_id, int)
        ASSERT_TYPE(data, (dict, list), "Data must be dict or list")
    """
    type_names = (
        expected_type.__name__
        if isinstance(expected_type, type)
        else " or ".join(t.__name__ for t in expected_type)
    )
    default_msg = f"Expected type {type_names}, got {type(obj).__name__}"
    ASSERT(
        isinstance(obj, expected_type),
        message or default_msg,
        extra={"expected": type_names, "actual": type(obj).__name__, "value": obj},
    )


def ASSERT_IN(item: Any, container: Any, message: str = "") -> None:
    """Assert that item is in container.

    Args:
        item: Item to check.
        container: Container to check in.
        message: Custom error message.

    Example:
        ASSERT_IN(status, ["active", "pending", "closed"])
        ASSERT_IN("user_id", request.json)
    """
    default_msg = f"{item!r} not found in container"
    ASSERT(
        item in container,
        message or default_msg,
        extra={"item": item, "container_type": type(container).__name__},
    )


def ASSERT_NOT_EMPTY(obj: Any, message: str = "") -> None:
    """Assert that obj is not empty (len > 0 or truthy).

    Args:
        obj: Object to check.
        message: Custom error message.

    Example:
        ASSERT_NOT_EMPTY(users, "No users found")
        ASSERT_NOT_EMPTY(username)
    """
    default_msg = f"{type(obj).__name__} is empty"
    ASSERT(
        bool(obj) and (not hasattr(obj, "__len__") or len(obj) > 0),
        message or default_msg,
        extra={"type": type(obj).__name__, "length": len(obj) if hasattr(obj, "__len__") else None},
    )


def ASSERT_RANGE(
    value: Union[int, float],
    min_val: Union[int, float],
    max_val: Union[int, float],
    message: str = "",
) -> None:
    """Assert that value is within [min_val, max_val] range.

    Args:
        value: Value to check.
        min_val: Minimum allowed value (inclusive).
        max_val: Maximum allowed value (inclusive).
        message: Custom error message.

    Example:
        ASSERT_RANGE(age, 0, 150)
        ASSERT_RANGE(temperature, -273.15, 1000)
    """
    default_msg = f"Value {value} not in range [{min_val}, {max_val}]"
    ASSERT(
        min_val <= value <= max_val,
        message or default_msg,
        extra={"value": value, "min": min_val, "max": max_val},
    )


def ASSERT_EQUALS(actual: Any, expected: Any, message: str = "") -> None:
    """Assert that actual equals expected.

    Args:
        actual: Actual value.
        expected: Expected value.
        message: Custom error message.

    Example:
        ASSERT_EQUALS(response.status_code, 200)
        ASSERT_EQUALS(len(results), 5, "Should return 5 results")
    """
    default_msg = f"Expected {expected!r}, got {actual!r}"
    ASSERT(
        actual == expected,
        message or default_msg,
        extra={"actual": actual, "expected": expected},
    )


def ASSERT_NONE(obj: Any, message: str = "") -> None:
    """Assert that obj is None.

    Args:
        obj: Object to check.
        message: Custom error message.

    Example:
        ASSERT_NONE(error, "Unexpected error occurred")
    """
    default_msg = f"Expected None, got {type(obj).__name__}"
    ASSERT(obj is None, message or default_msg, extra={"actual": obj})


def ASSERT_NOT_NONE(obj: Any, message: str = "") -> None:
    """Assert that obj is not None.

    Args:
        obj: Object to check.
        message: Custom error message.

    Example:
        ASSERT_NOT_NONE(user, "User not found")
    """
    default_msg = "Value is None"
    ASSERT(obj is not None, message or default_msg, extra={"value": obj})


__all__ = [
    "ASSERT",
    "enforce",
    "set_failure_handler",
    # Helpers
    "ASSERT_TYPE",
    "ASSERT_IN",
    "ASSERT_NOT_EMPTY",
    "ASSERT_RANGE",
    "ASSERT_EQUALS",
    "ASSERT_NONE",
    "ASSERT_NOT_NONE",
    # Exceptions
    "ValidationError",
    "FatalAssertionError",
]
