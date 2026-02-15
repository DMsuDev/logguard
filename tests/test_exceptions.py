# tests/test_exceptions.py

import pytest

from logguard.exceptions import (
    AppBaseError,
    ConfigurationError,
    ForbiddenError,
    MissingConfigError,
    ResourceError,
    ResourceNotFoundError,
    ValidationError,
)


def test_base_error_str_and_repr() -> None:
    err = AppBaseError("algo falló", context={"code": 42, "user": "alice"})
    assert "algo falló | context: code=42, user='alice'" in str(err)
    assert repr(err).startswith("AppBaseError(")


def test_to_dict() -> None:
    err = ValidationError("dato inválido", field="email", value="no@valido")
    d = err.to_dict()
    assert d["type"] == "ValidationError"
    assert d["message"] == "dato inválido"
    assert d["context"]["field"] == "email"


def test_specific_exceptions_context() -> None:
    err1 = MissingConfigError("API_KEY", source="dotenv")
    assert "API_KEY" in str(err1)
    assert err1.context["config_key"] == "API_KEY"
    assert err1.context["source"] == "dotenv"

    err2 = ResourceNotFoundError("user", "u-12345", extra_info="deleted")
    assert "user not found: 'u-12345'" in str(err2)
    assert err2.context["id"] == "u-12345"


@pytest.mark.parametrize(
    "exc_class, exc_args, exc_kwargs, expected_in_str",
    [
        (ForbiddenError, ("admin panel",), {"user_id": "user123"}, "admin panel"),
        (ConfigurationError, ("Invalid config",), {"config_key": "DATABASE_URL", "file_path": "/etc/app.conf"}, "Invalid config"),
        (ResourceError, ("Resource access failed",), {"context": {"resource_type": "file", "path": "/data/missing.txt"}}, "Resource access"),
        (ValidationError, ("Invalid email format",), {"field": "email", "value": "not-an-email"}, "Invalid email"),
    ],
)
def test_exception_creation_and_context(exc_class, exc_args, exc_kwargs, expected_in_str) -> None:
    """Test that various exception classes create context correctly."""
    err = exc_class(*exc_args, **exc_kwargs)
    assert expected_in_str in str(err)
    assert isinstance(err.context, dict)


def test_base_error_without_context() -> None:
    """Test AppBaseError without context."""
    err = AppBaseError("Simple error")
    assert str(err) == "Simple error"
    assert err.context == {}
