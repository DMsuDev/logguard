"""Tests for the logguard package initialization and exports."""

from unittest.mock import patch

import pytest

import logguard
from logguard import (
    ASSERT,
    ASSERT_IN,
    ASSERT_RANGE,
    ASSERT_TYPE,
    AppBaseError,
    AppLogger,
    ConfigurationError,
    ForbiddenError,
    MissingConfigError,
    ResourceError,
    ResourceNotFoundError,
    ValidationError,
    enforce,
    set_failure_handler,
)


@pytest.mark.parametrize(
    "export_name, export_obj",
    [
        ("AppLogger", AppLogger),
        ("ASSERT", ASSERT),
        ("ASSERT_IN", ASSERT_IN),
        ("ASSERT_RANGE", ASSERT_RANGE),
        ("ASSERT_TYPE", ASSERT_TYPE),
        ("enforce", enforce),
        ("set_failure_handler", set_failure_handler),
    ],
)
def test_imports_available(export_name: str, export_obj) -> None:
    """Test that all main exports are available."""
    assert export_obj is not None


@pytest.mark.parametrize(
    "exception_name, exception_class",
    [
        ("AppBaseError", AppBaseError),
        ("ConfigurationError", ConfigurationError),
        ("MissingConfigError", MissingConfigError),
        ("ValidationError", ValidationError),
        ("ResourceError", ResourceError),
        ("ResourceNotFoundError", ResourceNotFoundError),
        ("ForbiddenError", ForbiddenError),
    ],
)
def test_exception_imports(exception_name: str, exception_class) -> None:
    """Test that all exception classes are importable."""
    assert exception_class is not None


@pytest.mark.parametrize(
    "function_name, function_obj",
    [
        ("ASSERT", ASSERT),
        ("enforce", enforce),
    ],
)
def test_function_callable(function_name: str, function_obj) -> None:
    """Test that functions are callable."""
    assert callable(function_obj)


def test_lazy_import_failure() -> None:
    """Test that _lazy_import raises ImportError when submodule fails to load.

    This tests the exception handling in _lazy_import():
        except Exception as exc:
            raise ImportError(f"Failed to load submodule 'logguard.{submodule}': {exc}") from exc
    """
    with patch("logguard.import_module", side_effect=Exception("Module not found")):
        with pytest.raises(ImportError) as exc_info:
            logguard._lazy_import("nonexistent")

        assert "Failed to load submodule 'logguard.nonexistent'" in str(exc_info.value)
        assert "Module not found" in str(exc_info.value)


def test_lazy_import_success() -> None:
    """Test that _lazy_import successfully caches submodules."""
    # First call should import and cache
    logger_module1 = logguard._lazy_import("logger")
    # Second call should return cached version
    logger_module2 = logguard._lazy_import("logger")

    assert logger_module1 is logger_module2
    assert logger_module1.AppLogger is not None


def test_getattr_lazy_loading() -> None:
    """Test that __getattr__ properly lazy-loads attributes."""
    # Access via __getattr__ should trigger lazy loading
    app_logger = logguard.AppLogger
    assert app_logger is not None

    # Accessing again should work (cached)
    app_logger2 = logguard.AppLogger
    assert app_logger is app_logger2


def test_getattr_invalid_attribute() -> None:
    """Test that __getattr__ raises AttributeError for unknown attributes."""
    with pytest.raises(AttributeError) as exc_info:
        _ = logguard.nonexistent_attribute  # type: ignore[attr-defined]

    assert "has no attribute 'nonexistent_attribute'" in str(exc_info.value)


def test_dir_function() -> None:
    """Test that dir() includes all public exports."""
    exports = dir(logguard)

    # Check that key items are in dir()
    assert "AppLogger" in exports
    assert "ASSERT" in exports
    assert "ValidationError" in exports
    assert "logger" in exports
    assert "asserts" in exports
    assert "exceptions" in exports


@pytest.mark.parametrize(
    "submodule_name, required_attributes",
    [
        ("logger", ["AppLogger"]),
        ("asserts", ["ASSERT", "enforce"]),
        ("exceptions", ["AppBaseError", "ValidationError"]),
    ],
)
def test_getattr_submodule(submodule_name: str, required_attributes: list[str]) -> None:
    """Test that __getattr__ properly returns submodules via lazy loading.

    This tests the line in __getattr__:
        if name in {"logger", "asserts", "exceptions"}:
            return _lazy_import(name)
    """
    # Force __getattr__ to be called by clearing cache
    if submodule_name in logguard.__dict__:
        del logguard.__dict__[submodule_name]

    # Get submodule via __getattr__
    submodule = getattr(logguard, submodule_name)

    assert submodule is not None
    # Verify required attributes exist
    for attr in required_attributes:
        assert hasattr(submodule, attr), f"{submodule_name} missing attribute {attr}"

    # Verify it's the actual submodule
    assert submodule.__name__ == f"logguard.{submodule_name}"
