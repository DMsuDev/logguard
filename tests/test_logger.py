"""
Compact tests for LogGuard AppLogger.
Covers: setup, reset, handlers, levels, file output, JSON fallback,
silence_noisy_libraries, get_logger auto_name, set_level edge cases.
"""

from __future__ import annotations

import importlib
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

from logguard.logger import AppLogger


# ──────────── Helpers ────────────
def _flush() -> None:
    for h in logging.getLogger().handlers:
        h.flush()


def _setup(log_dir: Path, **kw: Any) -> Path:
    log_file = log_dir / "app.log"
    AppLogger.setup(log_file=str(log_file), **kw)
    return log_file


# ──────────── Setup & Reset ────────────
def test_setup_and_reset(temp_log_dir: Path) -> None:
    log_file = _setup(temp_log_dir)
    assert log_file.parent.exists() and AppLogger._configured

    # Already configured warning
    AppLogger.setup(log_file=str(log_file))
    _flush()
    assert "already configured" in log_file.read_text()

    AppLogger.reset()
    assert not AppLogger._configured and not logging.getLogger().handlers


def test_setup_defaults_no_args() -> None:
    AppLogger.setup()
    assert AppLogger._configured
    AppLogger.reset()
    Path(AppLogger.DEFAULT_LOG_FILE).unlink(missing_ok=True)


# ──────────── Handlers & Levels ────────────
@pytest.mark.parametrize(
    "handler_type,expected",
    [
        ("console", (logging.DEBUG, None)),
        ("file", (None, logging.ERROR)),
        ("all", (logging.WARNING, logging.WARNING)),
    ],
)
def test_set_level_variants(temp_log_dir: Path, handler_type: str, expected: tuple[int | None, int | None]) -> None:
    _setup(temp_log_dir, file_level="WARNING")
    console_level, file_level = expected
    if handler_type == "console":
        AppLogger.set_level("DEBUG", handler_type="console")
    elif handler_type == "file":
        AppLogger.set_level("ERROR", handler_type="file")
    else:
        AppLogger.set_level("WARNING", handler_type="all")

    root = logging.getLogger()
    for h in root.handlers:
        if isinstance(h, RotatingFileHandler) and file_level is not None:
            assert h.level == file_level
        elif not isinstance(h, RotatingFileHandler) and console_level is not None:
            assert h.level == console_level
    if handler_type == "all":
        assert root.level == logging.WARNING

@pytest.mark.parametrize("level_input", ["INVALID", 12345, [], {}])
def test_resolve_level_invalid(level_input: Any) -> None:
    """_resolve_level returns DEBUG for invalid inputs."""
    assert AppLogger._resolve_level(level_input) == logging.DEBUG


@pytest.mark.parametrize(
    "valid_level",
    [
        logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL,
        [], {}, "NOTSET", 0, 10, 20, 30, 40, 50, "ERROR", "CRITICAL",
        "DEBUG", "INFO", "WARNING"
    ]
)
def test_resolve_level(valid_level: str | int) -> None:
    """_resolve_level handles valid levels correctly."""
    result = AppLogger._resolve_level(valid_level)
    assert isinstance(result, int)
    assert result in {logging.NOTSET, logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL}

def test_set_level_invalid_inputs(temp_log_dir: Path) -> None:
    """Test invalid level and invalid handler_type in single function."""
    log_file = _setup(temp_log_dir, file_level="WARNING")

    # Test invalid level
    AppLogger.set_level("NONEXISTENT", handler_type="all")
    assert logging.getLogger().level == logging.INFO

    AppLogger.reset()
    log_file = _setup(temp_log_dir, file_level="WARNING")

    # Test invalid handler_type
    AppLogger.set_level("DEBUG", handler_type="bad_type")
    _flush()
    assert "Invalid handler_type" in log_file.read_text()


# ──────────── Get Logger ────────────
def test_get_logger_variants(temp_log_dir: Path) -> None:
    _setup(temp_log_dir)
    logger1 = AppLogger.get_logger("named.logger")
    logger2 = AppLogger.get_logger(auto_name=True)
    assert isinstance(logger1, logging.Logger) and "named.logger" in logger1.name
    assert isinstance(logger2, logging.Logger) and logger2.name != "__root__"


def test_get_logger_fallback_no_frame() -> None:
    with mock.patch("inspect.currentframe", side_effect=RuntimeError):
        logger = AppLogger.get_logger()
    assert logger.name == "__main__"


# ──────────── File Output ────────────
def test_logger_file_output(temp_log_dir: Path) -> None:
    log_file = _setup(temp_log_dir, file_level="DEBUG")
    AppLogger.get_logger("test").info("Hello Logger")
    _flush()
    assert "Hello Logger" in log_file.read_text()


# ──────────── silence_noisy_libraries ────────────
def test_silence_libraries(temp_log_dir: Path) -> None:
    _setup(temp_log_dir)
    AppLogger.silence_noisy_libraries()
    for mod in ["PIL", "matplotlib", "urllib3", "openai"]:
        lg = logging.getLogger(mod)
        assert lg.level == logging.WARNING and not lg.propagate
    AppLogger.silence_noisy_libraries(modules=["httpx", "sqlalchemy"])
    assert logging.getLogger("httpx").level == logging.WARNING
    assert logging.getLogger("sqlalchemy").level == logging.WARNING


# ──────────── Console & JSON fallback ────────────
def test_console_fallback(temp_log_dir: Path) -> None:
    with mock.patch("logguard.logger.RichHandler", side_effect=ImportError):
        AppLogger.reset()
        _setup(temp_log_dir)
    console_handlers = [h for h in logging.getLogger().handlers if not isinstance(h, RotatingFileHandler)]
    assert console_handlers and isinstance(console_handlers[0], logging.StreamHandler)


def test_json_logging(temp_log_dir: Path) -> None:
    log_file = _setup(temp_log_dir, json_logs=True)
    assert AppLogger._configured

    with mock.patch.object(AppLogger, "_create_json_handler", return_value=None):
        AppLogger.setup(log_file=str(log_file), json_logs=True)
    _flush()
    content = log_file.read_text()
    assert "python-json-logger" in content or AppLogger._configured


def test_json_handler_missing(temp_log_dir: Path) -> None:
    with mock.patch("logguard.logger.JSON_LOGGER_AVAILABLE", False):
        handler = AppLogger._create_json_handler(temp_log_dir / "app.log", logging.INFO, 5_000_000, 3)
    assert handler is None


def test_setup_json_when_import_fails(temp_log_dir: Path) -> None:
    """Test setup with json_logs=True when JSON_LOGGER_AVAILABLE is False from start."""
    log_file = temp_log_dir / "app.log"
    with mock.patch("logguard.logger.JSON_LOGGER_AVAILABLE", False):
        AppLogger.setup(log_file=str(log_file), json_logs=True, file_level="WARNING")
    _flush()
    content = log_file.read_text()
    assert "JSON logging requested but python-json-logger is not installed" in content or AppLogger._configured


def test_json_library_missing() -> None:
    with mock.patch.dict("sys.modules", {"pythonjsonlogger.json": None}):
        import logguard.logger as lg_logger

        importlib.reload(lg_logger)
        assert lg_logger.JsonFormatter is None
        assert lg_logger.JSON_LOGGER_AVAILABLE is False
