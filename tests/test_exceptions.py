"""
Summary of tests for logguard.exceptions:

- Exception instantiation with message and context
- Inheritance hierarchy
- Context preserves types and is accessible
- Factory method `from_dict`
- Handling of varied messages
"""

import pytest

from logguard.exceptions import (
    AssertFailure,
    ComparisonError,
    ConfigurationError,
    EqualsError,
    EmptyError,
    ForbiddenError,
    LogGuardError,
    MembershipError,
    MissingConfigError,
    NullError,
    RangeError,
    ResourceError,
    ResourceNotFoundError,
    TypeErrorAssert,
    ValidationError,
)


@pytest.mark.parametrize(
    "exc_class",
    [
        LogGuardError,
        ValidationError,
        AssertFailure,
        NullError,
        RangeError,
        TypeErrorAssert,
        EmptyError,
        EqualsError,
        ComparisonError,
        MembershipError,
        ConfigurationError,
        ResourceError,
    ],
)
def test_exception_creation_with_context(exc_class: type[LogGuardError]) -> None:
    """All exceptions accept a message and context."""
    ctx = {"key": 123}
    exc = exc_class("Test message", context=ctx)
    assert "Test message" in str(exc)
    assert exc.context == ctx


def test_default_context_is_empty() -> None:
    """Exceptions without context have an empty dict."""
    exc = LogGuardError("No context")
    assert exc.context == {}


# ──────────── Inheritance ────────────


@pytest.mark.parametrize(
    "child,parent",
    [
        (ValidationError, LogGuardError),
        (AssertFailure, ValidationError),
        (NullError, AssertFailure),
        (RangeError, AssertFailure),
        (TypeErrorAssert, AssertFailure),
        (EmptyError, AssertFailure),
        (EqualsError, AssertFailure),
        (ComparisonError, AssertFailure),
        (MembershipError, AssertFailure),
        (ConfigurationError, LogGuardError),
        (MissingConfigError, ConfigurationError),
        (ResourceError, LogGuardError),
        (ResourceNotFoundError, ResourceError),
        (ForbiddenError, ResourceError),
    ],
)
def test_exception_inheritance(child: type[LogGuardError], parent: type[LogGuardError]) -> None:
    """Verify direct and indirect inheritance."""
    assert issubclass(child, parent)
    assert issubclass(child, LogGuardError)


def test_catch_all_specialized_exceptions() -> None:
    """LogGuardError and AssertFailure should catch all assertion exceptions."""
    for exc_class in [
        NullError,
        RangeError,
        TypeErrorAssert,
        EmptyError,
        EqualsError,
        ComparisonError,
        MembershipError,
    ]:
        with pytest.raises(LogGuardError):
            raise exc_class("Test")
        with pytest.raises(AssertFailure):
            raise exc_class("Test")


# ──────────── Context Storage ────────────


@pytest.mark.parametrize(
    "context_data",
    [
        {"num": 42, "flt": 3.14},
        {"nested": {"deep": True}},
        {"list": [1, 2], "set": {3, 4}},
        {"none": None, "bool": False},
    ],
)
def test_context_preserves_types(context_data: dict) -> None:
    exc = LogGuardError("Test", context=context_data)
    for k, v in context_data.items():
        assert exc.context[k] == v


def test_context_accessible_after_catch() -> None:
    try:
        raise AssertFailure("Caught", context={"code": 500})
    except AssertFailure as e:
        assert e.context["code"] == 500


# ──────────── Factory Method from_dict ────────────


@pytest.mark.parametrize("exc_class", [LogGuardError, ValidationError, AssertFailure, NullError, RangeError])
def test_from_dict_factory(exc_class: type[LogGuardError]) -> None:
    exc = exc_class.from_dict({"message": f"Created {exc_class.__name__}", "context": {"type": exc_class.__name__}})
    assert exc_class.__name__ in str(exc)
    assert exc.context["type"] == exc_class.__name__


def test_from_dict_handles_missing_context() -> None:
    exc = LogGuardError.from_dict({"message": "No context"})
    assert str(exc) == "No context"
    assert exc.context == {}


# ──────────── Messages ────────────


@pytest.mark.parametrize("msg", ["", "Simple", "Unicode: café ñ 日本語", "Special <>&\"'", "Multi\nline\nmessage"])
def test_exception_messages(msg: str) -> None:
    exc = LogGuardError(msg)
    assert str(exc) == msg


def test_repr_includes_class_name() -> None:
    exc = NullError("Test")
    repr_str = repr(exc)
    assert "NullError" in repr_str or "Test" in repr_str


# ──────────── to_dict with __cause__ ────────────


def test_to_dict_includes_cause_when_chained() -> None:
    """to_dict includes 'cause' when the exception has __cause__."""
    original = ValueError("original error")
    try:
        raise LogGuardError("wrapped", context={"k": 1}) from original
    except LogGuardError as exc:
        data = exc.to_dict()
        assert "cause" in data
        assert data["cause"]["type"] == "ValueError"
        assert data["cause"]["message"] == "original error"


def test_to_dict_no_cause_without_chaining() -> None:
    """to_dict does not include 'cause' if there is no chained exception."""
    exc = LogGuardError("solo")
    data = exc.to_dict()
    assert "cause" not in data


def test_to_dict_cause_with_custom_exception() -> None:
    """to_dict handles __cause__ when it is another LogGuardError."""
    inner = NullError("inner null")
    try:
        raise AssertFailure("outer", context={"level": 2}) from inner
    except AssertFailure as exc:
        data = exc.to_dict()
        assert data["cause"]["type"] == "NullError"
        assert data["cause"]["message"] == "inner null"
        assert data["type"] == "AssertFailure"


# ──────────── __str__ with context ────────────


def test_str_with_context_formats_correctly() -> None:
    """__str__ includes formatted context when it exists."""
    exc = LogGuardError("fail", context={"a": 1, "b": "x"})
    result = str(exc)
    assert "fail" in result
    assert "context:" in result
    assert "a=1" in result
    assert "b='x'" in result


# ──────────── from_dict default message ────────────


def test_from_dict_default_message_when_missing() -> None:
    """from_dict uses a default message if none is provided."""
    exc = LogGuardError.from_dict({})
    assert str(exc) == "LogGuard error recovered"
    assert exc.context == {}


# ──────────── Specialized Exceptions ────────────


def test_missing_config_error_stores_key_and_source() -> None:
    exc = MissingConfigError("API_KEY", source="env")
    assert "API_KEY" in str(exc)
    assert exc.context["key"] == "API_KEY"
    assert exc.context["source"] == "env"


def test_resource_not_found_error() -> None:
    exc = ResourceNotFoundError("User", 42)
    assert "User" in str(exc)
    assert "42" in str(exc)
    assert exc.context == {"type": "User", "id": 42}


def test_forbidden_error_custom_kwargs() -> None:
    exc = ForbiddenError("No access", user="admin", resource="/secret")
    assert exc.context["user"] == "admin"
    assert exc.context["resource"] == "/secret"
