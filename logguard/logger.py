"""Logging utilities and a convenience logger configuration helper.

This module provides ``AppLogger``, a simple helper to configure the Python
logging subsystem with sensible defaults (file rotation, console handler,
optional rich formatting, and optional JSON output).

Usage example::

    from logguard.logger import AppLogger

    AppLogger.setup(log_file="logs/app.log", console_level="INFO")
    logger = AppLogger.get_logger(__name__)
    logger.info("Hello world")

The helper is intended for applications and simple libraries that want a
centralized logging configuration without repeating boilerplate.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

try:
    from rich.console import Console
    from rich.logging import RichHandler

    RICH_AVAILABLE = True
except ImportError:
    # Ensure name exists even if rich is not installed (avoids linter complaints)
    Console = None  # type: ignore[assignment,misc]
    RichHandler = None  # type: ignore[assignment,misc]
    RICH_AVAILABLE = False


class AppLogger:
    """
    Standalone logging configuration.

    Usage:

        AppLogger.setup(
            log_file="logs/app.log",
            console_level="INFO",
            file_level="DEBUG",
            json_logs=False,
        )
        logger = AppLogger.get_logger(__name__)
        logger.info("This is an info message")

    If setup() is not called, the first call to get_logger() will configure
    logging with default settings.
    """

    DEFAULT_LOG_FILE = "app.log"
    DEFAULT_MAX_BYTES = 5_000_000
    DEFAULT_BACKUP_COUNT = 3

    _configured = False

    @classmethod
    def setup(
        cls,
        log_file: str | None = None,
        console_level: str | int = logging.INFO,
        file_level: str | int = logging.DEBUG,
        json_logs: bool = os.getenv("JSON_LOGS", "false").lower() == "true",
        max_bytes: int | None = None,
        backup_count: int | None = None,
        force: bool = False,
    ) -> None:
        """Configure the Python logging system with sensible defaults.

        Sets up file rotation (RotatingFileHandler), console output with optional
        rich formatting, and optional JSON log output. Silences noisy libraries.
        Only runs once unless force=True.

        Args:
            log_file: Path to log file (default: 'app.log').
            console_level: Console handler log level as int or string (e.g., 'INFO').
            file_level: File handler log level as int or string (e.g., 'DEBUG').
            json_logs: Enable JSON-formatted logging (requires python-json-logger).
            max_bytes: Max file size before rotation (default: 5MB).
            backup_count: Number of backup files to keep (default: 3).
            force: If True, reconfigure even if already configured.
        """
        if cls._configured and not force:
            return

        log_file = log_file or cls.DEFAULT_LOG_FILE
        max_bytes = max_bytes or cls.DEFAULT_MAX_BYTES
        backup_count = backup_count or cls.DEFAULT_BACKUP_COUNT

        def resolve_level(value: str | int, default: int) -> int:
            """Convert log level string or int to int, falling back to default if invalid."""
            if isinstance(value, int):
                return value
            if isinstance(value, str):
                lv = getattr(logging, value.upper(), None)
                if isinstance(lv, int):
                    return lv
            # Fallback to default if level is invalid
            logging.warning("Invalid log level %r. Falling back to %s", value, logging.getLevelName(default))
            return default

        console_level = resolve_level(console_level, logging.INFO)
        file_level = resolve_level(file_level, logging.DEBUG)

        root = logging.getLogger()

        # Clear existing handlers if force=True
        if force:
            root.handlers.clear()
        else:
            # Check if we already have our handlers to avoid duplicates
            has_file_handler = any(isinstance(h, RotatingFileHandler) for h in root.handlers)
            # Console handler can be RichHandler or StreamHandler (but not RotatingFileHandler)
            has_console_handler = any(
                isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in root.handlers
            )
            # If we already have both handlers, don't add duplicates
            if has_file_handler and has_console_handler:
                cls._configured = True
                return

        root.setLevel(logging.DEBUG)  # The handlers will filter

        # File handler (human-readable)
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
            delay=False,  # Create file immediately for testing and immediate logging
        )
        file_handler.setLevel(file_level)

        # Format for file logs (includes logger name and thread info)
        file_fmt = logging.Formatter(
            "%(asctime)s | %(name)-17s | %(levelname)-7s | %(message)s  [%(threadName)s]",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_fmt)

        root.addHandler(file_handler)

        # Console handler with rich formatting if available
        if RICH_AVAILABLE and RichHandler is not None and Console is not None:
            console_handler: logging.Handler = RichHandler(
                level=console_level,
                console=Console(force_terminal=True, soft_wrap=True),
                show_time=True,  # Display timestamp
                log_time_format="%H:%M:%S",  # Time format for console logs
                omit_repeated_times=True,  # Don't repeat time if unchanged
                show_level=True,  # Display log level
                show_path=False,  # Don't show file:line info
                rich_tracebacks=True,  # Enable rich traceback formatting
                tracebacks_show_locals=True,  # Show local variables in tracebacks
                markup=False,  # Disable markup parsing in messages
            )
        else:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s [%(levelname)s] %(name)-17s: %(message)s",
                    datefmt="%H:%M:%S",
                )
            )

        console_handler.setLevel(console_level)
        root.addHandler(console_handler)

        # Optionally add JSON-formatted logging (requires python-json-logger package)
        if json_logs:
            try:
                from pythonjsonlogger.json import JsonFormatter

                json_file = str(log_path.with_suffix(".json"))
                json_handler = RotatingFileHandler(
                    json_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding="utf-8",
                )
                json_handler.setLevel(file_level)
                json_handler.setFormatter(
                    JsonFormatter(
                        fmt=(
                            "%(asctime)s %(name)s %(levelname)s %(message)s "
                            "%(pathname)s %(lineno)d %(funcName)s %(threadName)s"
                        ),
                        timestamp=True,
                    )
                )
                root.addHandler(json_handler)
            except ImportError:
                logging.warning("python-json-logger not installed: JSON logs disabled")

        # Suppress verbose logging from common third-party libraries
        noisy_modules = [
            "PIL",
            "matplotlib",
            "urllib3",
            "asyncio",
            "pdf2image",
            "httpcore",
            "httpx",
            "charset_normalizer",
            "openai",
            "anthropic",
        ]
        for mod in noisy_modules:
            logging.getLogger(mod).setLevel(logging.WARNING)
            logging.getLogger(mod).propagate = False  # Prevent logs from propagating up

        logging.captureWarnings(True)  # Capture Python warnings as logs
        cls._configured = True

    @classmethod
    def get_logger(cls, name: str | None = None, auto_name: bool = True) -> logging.Logger:
        """Get or create a logger with the given name.

        If name is None and auto_name is True, automatically uses the caller's module name.
        Calls setup() with default settings if logging has not been configured yet.

        Args:
            name: Logger name. If None and auto_name=True, uses the calling module's name.
            auto_name: If True and name is None, auto-detect the caller's module name.

        Returns:
            A logging.Logger instance.
        """
        if not cls._configured:
            cls.setup()

        if name is None and auto_name:
            try:
                import inspect

                frame = inspect.currentframe()
                if frame and frame.f_back:
                    module = inspect.getmodule(frame.f_back)
                    name = module.__name__ if module else "__main__"
            except Exception:
                # Suppress errors in special contexts (frozen apps, optimized mode, etc.)
                name = "__main__"
        return logging.getLogger(name or "__root__")

    @classmethod
    def set_level(
        cls,
        level: str | int,
        handler_type: str = "all",
        logger_name: str | None = None,
    ) -> None:
        """Dynamically change log level without reconfiguring.

        Args:
            level: New log level (e.g., 'DEBUG', 'INFO', logging.DEBUG).
            handler_type: Which handlers to update ('all', 'console', 'file').
            logger_name: Specific logger name, or None for root logger.
        """
        if isinstance(level, str):
            resolved = getattr(logging, level.upper(), None)
            if resolved is None or not isinstance(resolved, int):
                logging.warning("Invalid log level %r. Falling back to INFO", level)
                level = logging.INFO
            else:
                level = resolved

        target_logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()

        if handler_type == "all":
            target_logger.setLevel(level)
            for handler in target_logger.handlers:
                handler.setLevel(level)

        elif handler_type == "console":
            for handler in target_logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
                    handler.setLevel(level)

        elif handler_type == "file":
            for handler in target_logger.handlers:
                if isinstance(handler, RotatingFileHandler):
                    handler.setLevel(level)

        else:
            logging.warning("Invalid handler_type %r. Use 'all', 'console', or 'file'.", handler_type)

    @classmethod
    def reset(cls) -> None:
        """Reset logging configuration and handlers (useful for testing).

        Clears all handlers from the root logger and marks the logger as not configured,
        allowing setup() to run again.
        """
        logging.getLogger().handlers.clear()
        cls._configured = False
