"""
Pytest fixtures for LogGuard tests.

Provides reusable fixtures for:
- Logger reset and configuration
- Assertion manager reset
- Temporary directories
- Log capture
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from logguard.asserts import AssertionConfig, AssertionManager
from logguard.logger import AppLogger

# ========================================================================
# Logger Fixtures
# ========================================================================


@pytest.fixture(autouse=True)
def reset_logger() -> Generator[None, None, None]:
    """Reset logger configuration before and after each test."""
    AppLogger.reset()
    yield
    AppLogger.reset()


@pytest.fixture
def temp_log_dir(tmp_path: Path) -> Path:
    """Create a temporary directory for log files."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def configured_logger(temp_log_dir: Path) -> logging.Logger:
    """Setup AppLogger and return a configured logger instance."""
    log_file = temp_log_dir / "test.log"
    AppLogger.setup(log_file=str(log_file), console_level="DEBUG", file_level="DEBUG")
    return AppLogger.get_logger("test")


# ========================================================================
# Assertion Fixtures
# ========================================================================


@pytest.fixture(autouse=True)
def reset_assertions() -> Generator[None, None, None]:
    """Reset assertion manager before and after each test."""
    AssertionManager.reset()
    yield
    AssertionManager.reset()


@pytest.fixture
def dev_environment() -> Generator[None, None, None]:
    """Configure assertions for development environment."""
    AssertionManager.configure(AssertionConfig(environment="development", enable_asserts=True))
    yield
    AssertionManager.reset()


@pytest.fixture
def prod_environment() -> Generator[None, None, None]:
    """Configure assertions for production environment."""
    AssertionManager.configure(AssertionConfig(environment="production", enable_asserts=True))
    yield
    AssertionManager.reset()


@pytest.fixture
def disabled_asserts() -> Generator[None, None, None]:
    """Configure assertions with enable_asserts=False."""
    AssertionManager.configure(AssertionConfig(environment="development", enable_asserts=False))
    yield
    AssertionManager.reset()


# ========================================================================
# Log Capture Fixtures
# ========================================================================


@pytest.fixture
def capture_logs(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Capture logs from logguard loggers."""
    caplog.set_level(logging.DEBUG, logger="logguard")
    caplog.set_level(logging.DEBUG, logger="logguard.assertions")
    return caplog


# ========================================================================
# Mock Fixtures
# ========================================================================


@pytest.fixture
def no_json_logger(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate python-json-logger not being installed."""
    original_import = __import__

    def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.startswith("pythonjsonlogger"):
            raise ImportError(f"No module named '{name}'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", mock_import)
