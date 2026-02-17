"""Logging utilities and a convenience logger configuration helper.

This module provides ``AppLogger``, a simple helper to configure the Python
logging subsystem with sensible defaults (file rotation, console handler with
rich formatting, and optional JSON output).

Usage example:

    from logguard.logger import AppLogger

    AppLogger.setup(log_file="logs/app.log", console_level="INFO")
    logger = AppLogger.get_logger(__name__)
    logger.info("Hello world")

The helper is intended for applications and simple libraries that want a
centralized logging configuration without repeating boilerplate.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

try:
    from pythonjsonlogger.json import JsonFormatter

    JSON_LOGGER_AVAILABLE = True
except ImportError:
    JsonFormatter = None  # type: ignore[assignment,misc]
    JSON_LOGGER_AVAILABLE = False


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

    Note:
        - get_logger() can be called at any time (before or after setup).
          Loggers created before setup() will start working once setup()
          configures the root logger, thanks to Python's log propagation.
        - setup() only runs once per process. Subsequent calls are ignored
          with a warning. Use reset() + setup() to reconfigure.
    """

    DEFAULT_LOG_FILE: str = "app.log"
    DEFAULT_MAX_BYTES: int = 5_000_000
    DEFAULT_BACKUP_COUNT: int = 3

    _configured: bool = False

    @classmethod
    def setup(
        cls,
        log_file: str | None = None,
        console_level: str | int = logging.INFO,
        file_level: str | int = logging.DEBUG,
        json_logs: bool = False,
        max_bytes: int | None = None,
        backup_count: int | None = None,
        delay: bool = True,
    ) -> None:
        """Configure the Python logging system with sensible defaults.

        Sets up file rotation (RotatingFileHandler), console output with beautiful
        rich formatting, and optional JSON log output. Silences noisy libraries.
        Only runs once per process. Use reset() + setup() to reconfigure.

        Args:
            log_file: Path to log file (default: 'app.log').
            console_level: Console handler log level as int or string (e.g., 'INFO').
            file_level: File handler log level as int or string (e.g., 'DEBUG').
            json_logs: Enable JSON-formatted logging (requires python-json-logger).
            max_bytes: Max file size before rotation (default: 5MB).
            backup_count: Number of backup files to keep (default: 3).
            delay: If True, delay file creation until the first log message (default: True).
        """
        if cls._configured:
            logging.getLogger().warning(
                "AppLogger.setup() called but logging is already configured. "
                "Call AppLogger.reset() first if you need to reconfigure."
            )
            return

        log_file = log_file or cls.DEFAULT_LOG_FILE
        max_bytes = max_bytes or cls.DEFAULT_MAX_BYTES
        backup_count = backup_count or cls.DEFAULT_BACKUP_COUNT

        console_level = cls._resolve_level(console_level)
        file_level = cls._resolve_level(file_level)

        root = logging.getLogger()
        root.handlers.clear()
        root.setLevel(logging.DEBUG)  # The handlers will filter

        log_path: Path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # File handler (human-readable)
        file_handler = cls._create_file_handler(log_file, file_level, max_bytes, backup_count, delay)
        root.addHandler(file_handler)

        # Console handler with rich formatting
        console_handler = cls._create_console_handler(console_level)
        root.addHandler(console_handler)

        # Optionally add JSON-formatted logging (requires python-json-logger package)
        if json_logs:
            json_handler = cls._create_json_handler(log_path, file_level, max_bytes, backup_count, delay)
            if json_handler:
                root.addHandler(json_handler)
            else:
                logging.warning(
                    "JSON logging requested but python-json-logger is not installed. "
                    "Falling back to plain text file logging. "
                    "Install with: pip install python-json-logger"
                )
        else:
            logging.debug("JSON logging is disabled. To enable, set json_logs=True")

        logging.captureWarnings(True)  # Capture Python warnings as logs
        cls._configured = True

    @staticmethod
    def _resolve_level(value: str | int) -> int:
        """Convert log level string or int to int, validating it's a recognized level.

        Falls back to DEBUG if the level is invalid.
        Valid levels: 0 (NOTSET), 10 (DEBUG), 20 (INFO), 30 (WARNING), 40 (ERROR), 50 (CRITICAL).
        """
        valid_levels = {logging.NOTSET, logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL}

        default_level: int = logging.DEBUG

        if isinstance(value, int):
            if value in valid_levels:
                return value
            logging.warning("Invalid log level %r. Must be one of %s. Falling back to DEBUG", value, valid_levels)
            return default_level

        if isinstance(value, str):
            resolved = getattr(logging, value.upper(), None)
            if isinstance(resolved, int) and resolved in valid_levels:
                return resolved
            logging.warning("Invalid log level %r. Falling back to DEBUG", value)
            return default_level

        logging.warning("Invalid log level type %r. Falling back to DEBUG", type(value).__name__)
        return default_level

    @classmethod
    def _create_file_handler(
        cls,
        log_file: str | Path,
        level: int,
        max_bytes: int,
        backup_count: int,
        delay: bool = True,
    ) -> RotatingFileHandler:
        """
        Helper to create a RotatingFileHandler with the given settings.

        Ensures the log directory exists and configures the handler with a standard format.

        Args:
            log_file: Path to the log file.
            level: Log level for the handler.
            max_bytes: Max file size before rotation.
            backup_count: Number of backup files to keep.
            delay: If True, delay file creation until the first log message (default: True).

        Returns:
            Configured RotatingFileHandler instance.
        """

        handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
            delay=delay,  # Delay file creation until the first log message
        )
        handler.setLevel(level)

        # Format for file logs (includes logger name and thread info)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(name)-17s | %(levelname)-7s | %(message)s  [%(threadName)s]",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        return handler

    @classmethod
    def _create_console_handler(
        cls,
        level: int,
    ) -> logging.Handler:
        """
        Helper to create a console handler with rich formatting.
        If Rich is not available, falls back to a standard StreamHandler with a simple format.

        Args:
            level: Log level for the console handler.
        Returns:
            Configured logging.Handler instance.
        """
        try:
            return RichHandler(
                level=level,
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
        except ImportError:
            handler = logging.StreamHandler()
            handler.setLevel(level)
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s · %(levelname)-7s · %(name)-18s · %(message)s",
                    datefmt="%H:%M:%S",
                )
            )
            return handler

    @classmethod
    def _create_json_handler(
        cls,
        log_file: str | Path,
        level: int,
        max_bytes: int,
        backup_count: int,
        delay: bool = True,
    ) -> logging.Handler | None:
        """
        Helper to create a JSON-formatted file handler using python-json-logger.

        Args:
            log_file: Path to the log file.
            level: Log level for the handler.
            max_bytes: Max file size before rotation.
            backup_count: Number of backup files to keep.
            delay: If True, delay file creation until the first log message (default: True).

        Returns:
            Configured logging.Handler instance or None if JSON logging is unavailable.
        """
        if not JSON_LOGGER_AVAILABLE or JsonFormatter is None:
            return None

        json_path = str(Path(log_file).with_suffix(".json"))

        json_handler = RotatingFileHandler(
            json_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
            delay=delay,
        )
        json_handler.setLevel(level)
        json_handler.setFormatter(
            JsonFormatter(
                fmt=(
                    "%(asctime)s %(name)s %(levelname)s %(message)s "
                    "%(pathname)s %(lineno)d %(funcName)s %(threadName)s "
                    "%(exc_info)s %(stack_info)s"
                ),
                timestamp=True,
                json_ensure_ascii=False,
            )
        )
        return json_handler

    @classmethod
    def silence_noisy_libraries(cls, modules: list[str] | None = None) -> None:
        """
        Silence noisy third-party libraries by setting their log level to WARNING.
        If no modules are specified, a default list of common noisy libraries is used.
        Args:
            modules: List of module names to silence (default: ['PIL', 'matplotlib', 'urllib3', 'openai']).
        """
        default_noisy: list[str] = [
            "PIL",
            "matplotlib",
            "urllib3",
            "openai",
        ]
        rel_modules: list[str] = modules if modules is not None else default_noisy

        for mod in rel_modules:
            logging.getLogger(mod).setLevel(logging.WARNING)
            logging.getLogger(mod).propagate = False  # Prevent logs from propagating up to root

    @classmethod
    def get_logger(cls, name: str | None = None, auto_name: bool = True) -> logging.Logger:
        """Get or create a logger with the given name.

        Can be called before or after setup(). Loggers created before setup()
        will automatically use the root logger's handlers once setup() runs,
        thanks to Python's built-in log propagation.

        Args:
            name: Logger name. If None and auto_name=True, uses the calling module's name.
            auto_name: If True and name is None, auto-detect the caller's module name.

        Returns:
            A logging.Logger instance.
        """
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
                if isinstance(handler, (logging.StreamHandler, RichHandler)) and not isinstance(
                    handler, RotatingFileHandler
                ):
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
