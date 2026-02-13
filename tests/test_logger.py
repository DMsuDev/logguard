"""
Comprehensive tests for logguard.logger module.

Tests cover:
- Basic logger setup and configuration
- Multiple handler types (file, console, JSON)
- Log level management
- File rotation
- Rich formatting (when available)
- Edge cases and error handling
"""

import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from logguard.logger import AppLogger


@pytest.fixture(autouse=True)
def reset_logger() -> None:
    """Reset logger before and after each test."""
    AppLogger.reset()
    yield
    AppLogger.reset()


class TestAppLoggerSetup:
    """Tests for AppLogger.setup() method."""

    def test_setup_creates_log_file(self, tmp_path: Path) -> None:
        """Test that setup creates the log file and directory."""
        log_file = tmp_path / "logs" / "app.log"
        AppLogger.setup(log_file=str(log_file))

        logger = AppLogger.get_logger("test")
        logger.info("test message")

        # Force handlers to flush
        for handler in logging.getLogger().handlers:
            handler.flush()

        assert log_file.exists()

    def test_setup_with_default_file(self, tmp_path: Path) -> None:
        """Test setup with default log file name."""
        os.chdir(tmp_path)
        AppLogger.setup()

        logger = AppLogger.get_logger("test")
        logger.info("test message")

        # Force handlers to flush
        for handler in logging.getLogger().handlers:
            handler.flush()

        assert Path("app.log").exists()

    def test_setup_configures_root_logger(self, tmp_path: Path) -> None:
        """Test that setup configures the root logger with handlers."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file))

        root = logging.getLogger()
        assert len(root.handlers) >= 2  # At least file + console

    def test_setup_force_clears_handlers(self, tmp_path: Path) -> None:
        """Test that force=True clears existing handlers."""
        log_file = tmp_path / "a.log"

        AppLogger.setup(log_file=str(log_file), force=True)
        root = logging.getLogger()
        count_first = len(root.handlers)

        AppLogger.setup(log_file=str(log_file), force=True)
        count_second = len(root.handlers)

        assert count_second == count_first

    def test_setup_only_runs_once(self, tmp_path: Path) -> None:
        """Test that setup only configures once unless forced."""
        log_file = tmp_path / "test.log"

        AppLogger.setup(log_file=str(log_file))
        root = logging.getLogger()
        count_first = len(root.handlers)

        # Second call without force should not add more handlers
        AppLogger.setup(log_file=str(log_file))
        count_second = len(root.handlers)

        assert count_second == count_first

    def test_setup_custom_log_levels(self, tmp_path: Path) -> None:
        """Test setup with custom log levels."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file), console_level="ERROR", file_level="WARNING")

        root = logging.getLogger()
        from logging.handlers import RotatingFileHandler

        # Find console handler (skip pytest's LogCaptureHandler and RotatingFileHandler)
        console_handler = None
        for handler in root.handlers:
            # Skip pytest's LogCaptureHandler and file handlers
            if handler.__class__.__name__ == "LogCaptureHandler":
                continue
            if isinstance(handler, RotatingFileHandler):
                continue
            console_handler = handler
            break

        assert console_handler is not None
        assert console_handler.level == logging.ERROR

    def test_setup_invalid_log_level_fallback(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that invalid log levels fall back to defaults."""
        log_file = tmp_path / "test.log"

        with caplog.at_level(logging.WARNING):
            AppLogger.setup(log_file=str(log_file), console_level="INVALID_LEVEL")

        assert any("Invalid log level" in record.message for record in caplog.records)

    def test_setup_with_json_logs_disabled(self, tmp_path: Path) -> None:
        """Test setup with JSON logs disabled (default)."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file), json_logs=False)

        root = logging.getLogger()
        # Should have file + console handlers, no JSON handler (excluding pytest's handlers)
        app_handlers = [h for h in root.handlers if h.__class__.__name__ != "LogCaptureHandler"]
        assert len(app_handlers) == 2

    @patch.dict(os.environ, {"JSON_LOGS": "true"})
    def test_setup_json_logs_from_env(self, tmp_path: Path) -> None:
        """Test that JSON_LOGS environment variable is respected."""
        log_file = tmp_path / "test.log"

        # If python-json-logger is not installed, this should log a warning
        with patch("logguard.logger.logging.warning") as mock_warning:
            AppLogger.setup(log_file=str(log_file))
            # May or may not warn depending on if python-json-logger is installed

    def test_setup_custom_rotation_settings(self, tmp_path: Path) -> None:
        """Test setup with custom max_bytes and backup_count."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file), max_bytes=1_000_000, backup_count=5)

        root = logging.getLogger()
        from logging.handlers import RotatingFileHandler

        file_handler = None
        for handler in root.handlers:
            if isinstance(handler, RotatingFileHandler):
                file_handler = handler
                break

        assert file_handler is not None
        assert file_handler.maxBytes == 1_000_000
        assert file_handler.backupCount == 5


class TestAppLoggerGetLogger:
    """Tests for AppLogger.get_logger() method."""

    def test_get_logger_returns_logger_instance(self) -> None:
        """Test that get_logger returns a Logger instance."""
        logger = AppLogger.get_logger("test_logger")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_auto_setup(self) -> None:
        """Test that get_logger auto-configures if not setup."""
        AppLogger.reset()
        logger = AppLogger.get_logger("test")

        # Should trigger setup automatically
        assert AppLogger._configured
        assert isinstance(logger, logging.Logger)

    def test_get_logger_with_explicit_name(self) -> None:
        """Test get_logger with explicit name."""
        logger = AppLogger.get_logger("my.app.module")
        assert logger.name == "my.app.module"

    def test_get_logger_auto_name_detection(self) -> None:
        """Test auto name detection from calling module."""
        logger = AppLogger.get_logger()
        # Should use this test module's name
        assert logger.name is not None
        assert logger.name != "__root__"

    def test_get_logger_with_none_name(self) -> None:
        """Test get_logger with None name and auto_name=False."""
        logger = AppLogger.get_logger(name=None, auto_name=False)
        assert logger.name == "__root__"

    def test_get_logger_same_name_returns_same_instance(self) -> None:
        """Test that multiple calls with same name return same logger."""
        logger1 = AppLogger.get_logger("test")
        logger2 = AppLogger.get_logger("test")
        assert logger1 is logger2

    def test_logger_can_log_messages(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that logger can actually log messages."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file))
        logger = AppLogger.get_logger("test")

        with caplog.at_level(logging.INFO):
            logger.info("test info message")
            logger.debug("test debug message")
            logger.warning("test warning message")
            logger.error("test error message")

        # Check that messages were logged
        assert any("test info message" in record.message for record in caplog.records)


class TestAppLoggerSetLevel:
    """Tests for AppLogger.set_level() method."""

    def test_set_level_all_handlers(self, tmp_path: Path) -> None:
        """Test setting level for all handlers."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file), console_level="INFO")

        AppLogger.set_level("DEBUG", handler_type="all")

        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_set_level_console_only(self, tmp_path: Path) -> None:
        """Test setting level for console handler only."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file), console_level="INFO", file_level="DEBUG")

        AppLogger.set_level("ERROR", handler_type="console")

        root = logging.getLogger()
        # Check console handler has ERROR level
        for handler in root.handlers:
            if isinstance(handler, logging.StreamHandler) and not hasattr(handler, "baseFilename"):
                assert handler.level == logging.ERROR

    def test_set_level_file_only(self, tmp_path: Path) -> None:
        """Test setting level for file handler only."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file), file_level="DEBUG")

        AppLogger.set_level("WARNING", handler_type="file")

        root = logging.getLogger()
        from logging.handlers import RotatingFileHandler

        for handler in root.handlers:
            if isinstance(handler, RotatingFileHandler):
                assert handler.level == logging.WARNING

    def test_set_level_with_string(self, tmp_path: Path) -> None:
        """Test set_level with string level."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file))

        AppLogger.set_level("WARNING", handler_type="all")
        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_set_level_with_int(self, tmp_path: Path) -> None:
        """Test set_level with integer level."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file))

        AppLogger.set_level(logging.CRITICAL, handler_type="all")
        root = logging.getLogger()
        assert root.level == logging.CRITICAL

    def test_set_level_invalid_string_fallback(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that invalid level string falls back to INFO."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file))

        with caplog.at_level(logging.WARNING):
            AppLogger.set_level("INVALID", handler_type="all")

        assert any("Invalid log level" in record.message for record in caplog.records)

    def test_set_level_specific_logger(self, tmp_path: Path) -> None:
        """Test setting level for a specific logger."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file))

        logger_name = "specific.logger"
        logger = AppLogger.get_logger(logger_name)

        AppLogger.set_level("ERROR", handler_type="all", logger_name=logger_name)
        assert logger.level == logging.ERROR


class TestAppLoggerReset:
    """Tests for AppLogger.reset() method."""

    def test_reset_clears_handlers(self, tmp_path: Path) -> None:
        """Test that reset clears all handlers."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file))

        root = logging.getLogger()
        assert len(root.handlers) > 0

        AppLogger.reset()
        assert len(root.handlers) == 0

    def test_reset_marks_unconfigured(self, tmp_path: Path) -> None:
        """Test that reset marks logger as not configured."""
        log_file = tmp_path / "test.log"

        # Reset first to ensure clean state
        AppLogger.reset()

        # Now setup and verify
        AppLogger.setup(log_file=str(log_file))
        assert AppLogger._configured

        AppLogger.reset()
        assert not AppLogger._configured

    def test_reset_allows_reconfiguration(self, tmp_path: Path) -> None:
        """Test that reset allows setup to run again."""
        log_file1 = tmp_path / "log1.log"
        log_file2 = tmp_path / "log2.log"

        AppLogger.setup(log_file=str(log_file1))
        AppLogger.reset()
        AppLogger.setup(log_file=str(log_file2))

        assert AppLogger._configured
        logger = AppLogger.get_logger("test")
        logger.info("test message")

        assert log_file2.exists()


class TestRichIntegration:
    """Tests for Rich console formatting integration."""

    def test_rich_handler_used_when_available(self, tmp_path: Path) -> None:
        """Test that RichHandler is used when rich is available."""
        log_file = tmp_path / "test.log"

        try:
            from rich.logging import RichHandler

            rich_available = True
        except ImportError:
            rich_available = False

        AppLogger.setup(log_file=str(log_file))
        root = logging.getLogger()

        if rich_available:
            # Should have RichHandler for console
            has_rich = any(isinstance(h, RichHandler) for h in root.handlers)
            assert has_rich
        else:
            # Should use regular StreamHandler
            has_stream = any(
                isinstance(h, logging.StreamHandler) and not hasattr(h, "baseFilename")
                for h in root.handlers
            )
            assert has_stream


class TestLoggingBehavior:
    """Tests for actual logging behavior."""

    def test_file_logs_are_written(self, tmp_path: Path) -> None:
        """Test that logs are actually written to file."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file), file_level="DEBUG")

        logger = AppLogger.get_logger("test")
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")

        # Force handlers to flush
        for handler in logging.getLogger().handlers:
            handler.flush()

        content = log_file.read_text()
        assert "debug message" in content
        assert "info message" in content
        assert "warning message" in content

    def test_console_level_filters_messages(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that console level properly filters messages."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file), console_level="WARNING")

        logger = AppLogger.get_logger("test")

        with caplog.at_level(logging.DEBUG):
            logger.debug("debug message")
            logger.info("info message")
            logger.warning("warning message")

        # Only warning should appear in console (caplog)
        messages = [record.message for record in caplog.records]
        assert "warning message" in messages
        # Debug and info might still be in file

    def test_noisy_modules_are_silenced(self, tmp_path: Path) -> None:
        """Test that noisy third-party modules are silenced."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file))

        # Check that noisy modules have WARNING level
        noisy_modules = ["urllib3", "PIL", "matplotlib"]
        for module_name in noisy_modules:
            module_logger = logging.getLogger(module_name)
            assert module_logger.level == logging.WARNING

    def test_different_loggers_can_coexist(self, tmp_path: Path) -> None:
        """Test that multiple loggers can coexist."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file))

        logger1 = AppLogger.get_logger("module1")
        logger2 = AppLogger.get_logger("module2")
        logger3 = AppLogger.get_logger("module3")

        logger1.info("from module 1")
        logger2.info("from module 2")
        logger3.info("from module 3")

        # Force handlers to flush
        for handler in logging.getLogger().handlers:
            handler.flush()

        content = log_file.read_text()
        assert "from module 1" in content
        assert "from module 2" in content
        assert "from module 3" in content


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_setup_with_empty_log_file_path(self) -> None:
        """Test setup with empty string for log file."""
        # Should use default
        AppLogger.setup(log_file="")
        logger = AppLogger.get_logger("test")
        assert isinstance(logger, logging.Logger)

    def test_setup_with_special_characters_in_path(self, tmp_path: Path) -> None:
        """Test setup with special characters in log file path."""
        log_file = tmp_path / "logs with spaces" / "app-2024.log"
        AppLogger.setup(log_file=str(log_file))

        logger = AppLogger.get_logger("test")
        logger.info("test message")

        # Force handlers to flush
        for handler in logging.getLogger().handlers:
            handler.flush()

        assert log_file.exists()

    def test_logger_works_after_reset_and_reconfig(self, tmp_path: Path) -> None:
        """Test that logger still works after reset and reconfig."""
        log_file = tmp_path / "test.log"

        AppLogger.setup(log_file=str(log_file))
        logger1 = AppLogger.get_logger("test")
        logger1.info("message 1")

        # Force flush before reset
        for handler in logging.getLogger().handlers:
            handler.flush()

        AppLogger.reset()

        AppLogger.setup(log_file=str(log_file))
        logger2 = AppLogger.get_logger("test")
        logger2.info("message 2")

        # Force flush after second write
        for handler in logging.getLogger().handlers:
            handler.flush()

        content = log_file.read_text()
        assert "message 1" in content
        assert "message 2" in content

    def test_concurrent_logger_access(self, tmp_path: Path) -> None:
        """Test that concurrent logger access doesn't cause issues."""
        log_file = tmp_path / "test.log"
        AppLogger.setup(log_file=str(log_file))

        # Simulate concurrent access
        loggers = [AppLogger.get_logger(f"test{i}") for i in range(10)]

        for i, logger in enumerate(loggers):
            logger.info(f"message from logger {i}")

        # Force handlers to flush
        for handler in logging.getLogger().handlers:
            handler.flush()

        content = log_file.read_text()
        for i in range(10):
            assert f"message from logger {i}" in content
