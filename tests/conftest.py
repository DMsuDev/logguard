# tests/conftest.py
import logging
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from logguard.logger import AppLogger


@pytest.fixture(autouse=True)
def reset_logger() -> Generator[None, None, None]:
    """Limpia la configuración del logger antes y después de cada test"""
    AppLogger.reset()
    yield
    AppLogger.reset()


@pytest.fixture
def temp_log_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Directorio temporal para logs"""
    log_dir: Path = tmp_path / "logs"
    log_dir.mkdir()
    yield log_dir
    # cleanup opcional


@pytest.fixture
def capture_logs(caplog: pytest.LogCaptureFixture) -> pytest.LogCaptureFixture:
    """Usa caplog de pytest para capturar logs"""
    caplog.set_level(logging.DEBUG, logger="logguard")
    caplog.set_level(logging.DEBUG, logger="assertions")
    return caplog


@pytest.fixture
def no_rich(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simula que rich no está instalado"""
    monkeypatch.setattr("logguard.logger.RICH_AVAILABLE", False)
    monkeypatch.setattr("logguard.logger.RichHandler", None)
    monkeypatch.setattr("logguard.logger.Console", None)


@pytest.fixture
def no_json_logger(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simula que python-json-logger no está instalado"""

    original_import = __import__

    def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name.startswith("pythonjsonlogger"):
            raise ImportError(f"No module named '{name}'")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", mock_import)
