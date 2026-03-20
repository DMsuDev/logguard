"""
Summary of tests for logguard:

- Verify availability of assertion functions, exception classes, and the logger.
- Test lazy loading and `__getattr__` behavior.
- Verify submodules and their contents.
- Ensure `dir()` includes all public exports.
"""

import pytest

import logguard

# ──────────── Public Exports ────────────


@pytest.mark.parametrize(
    "name",
    [
        # Assertions
        "CHECK",
        "ASSERT",
        "ENSURE",
        "VERIFY",
        "ASSERT_NOT_NULL",
        "ASSERT_NULL",
        "ASSERT_EQUALS",
        "ASSERT_GREATER",
        "ASSERT_LESS",
        "ASSERT_IN_RANGE",
        "ASSERT_BETWEEN_EXCLUSIVE",
        "ASSERT_TYPE",
        "ASSERT_NOT_EMPTY",
        "ASSERT_IN",
        # Logger
        "AppLogger",
        # Exceptions
        "LogGuardError",
        "ValidationError",
        "AssertFailure",
        "NullError",
        "RangeError",
        "TypeErrorAssert",
        "EmptyError",
        "EqualsError",
        "ComparisonError",
        "MembershipError",
    ],
)
def test_public_exports_available(name: str) -> None:
    obj = getattr(logguard, name)
    assert obj is not None
    if name in [
        "AppLogger",
        "CHECK",
        "ASSERT",
        "ENSURE",
        "VERIFY",
        "ASSERT_NOT_NULL",
        "ASSERT_NULL",
        "ASSERT_EQUALS",
        "ASSERT_GREATER",
        "ASSERT_LESS",
        "ASSERT_IN_RANGE",
        "ASSERT_BETWEEN_EXCLUSIVE",
        "ASSERT_TYPE",
        "ASSERT_NOT_EMPTY",
        "ASSERT_IN",
    ]:
        assert callable(obj)
    else:
        assert isinstance(obj, type) and issubclass(obj, Exception)


def test_assertion_manager_and_config() -> None:
    from logguard import AssertionConfig, AssertionManager

    assert hasattr(AssertionManager, "configure")
    assert hasattr(AssertionManager, "reset")
    assert AssertionConfig is not None


# ──────────── Lazy Loading & __getattr__ ────────────


def test_lazy_import_and_getattr_cache() -> None:
    mod1 = logguard._lazy_import("logger")
    mod2 = logguard._lazy_import("logger")
    assert mod1 is mod2
    assert mod1.AppLogger is not None

    # __getattr__ carga lazy
    logger = logguard.AppLogger
    assert logger is logguard.AppLogger


def test_getattr_unknown_raises() -> None:
    with pytest.raises(AttributeError):
        _ = logguard.nonexistent_attribute


def test_lazy_import_unknown_raises() -> None:
    with pytest.raises(ImportError):
        logguard._lazy_import("nonexistent_submodule")


def test_getattr_loads_core_submodules_when_missing() -> None:
    """Force the __getattr__ branch that handles core submodules.

    Remove any cached attributes for `logger`, `asserts` and `exceptions`
    from the `logguard` package and then access them to ensure the
    `_lazy_import` path is executed and the module is cached on the
    package object.
    """
    core_names = ("logger", "asserts", "exceptions")

    for name in core_names:
        # Remove any existing cache to force __getattr__ handling
        if name in logguard.__dict__:
            del logguard.__dict__[name]

        assert name not in logguard.__dict__

        submod = getattr(logguard, name)
        assert submod is not None
        # After access, attribute must be cached on the package
        assert name in logguard.__dict__
        assert getattr(submod, "__name__", "").startswith(f"logguard.{name}")


# ──────────── Submodules ────────────


@pytest.mark.parametrize(
    "submodule_name,attrs",
    [
        ("logger", ["AppLogger"]),
        ("asserts", ["CHECK", "ASSERT", "ENSURE", "VERIFY", "AssertionManager"]),
        ("exceptions", ["LogGuardError", "AssertFailure", "ValidationError"]),
    ],
)
def test_submodule_contents(submodule_name: str, attrs: list[str]) -> None:
    mod = getattr(logguard, submodule_name)
    for attr in attrs:
        assert hasattr(mod, attr)
    assert mod.__name__.startswith(f"logguard.{submodule_name}")


# ──────────── dir() Completeness ────────────


@pytest.mark.parametrize(
    "export",
    [
        "logger",
        "asserts",
        "exceptions",
        "AppLogger",
        "CHECK",
        "ASSERT",
        "ENSURE",
        "VERIFY",
        "ASSERT_NOT_NULL",
        "ASSERT_IN_RANGE",
        "ASSERT_TYPE",
        "AssertionManager",
        "AssertionConfig",
        "LogGuardError",
        "ValidationError",
        "AssertFailure",
    ],
)
def test_dir_includes_all_exports(export: str) -> None:
    assert export in dir(logguard)
