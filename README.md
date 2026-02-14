# Logguard

[![Python](https://img.shields.io/badge/Language-Python-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/py-logguard)](https://pypi.org/project/py-logguard/)
[![PyPI](https://img.shields.io/pypi/v/py-logguard?style=flat&logo=pypi&logoColor=white)](https://pypi.org/project/py-logguard/)

![Status](https://img.shields.io/badge/Status-Stable-success?style=flat)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

Logguard is a lightweight logging and assertion library designed to make it easy to capture rich context and structured logs in Python applications. It provides a simple API for logging with automatic source capture, flexible configuration, and a semantic exception hierarchy.

It is built on top of the `logging` and `rich` libraries for enhanced logging capabilities.

## ⭐ Features

- **Easy Configuration**: Set up logging in one line with `AppLogger`
- **File Rotation**: Automatic log rotation with configurable size and backup count
- **Rich Console Output**: Beautiful console logs with [Rich](https://github.com/Textualize/rich) support
- **JSON Logging**: Optional structured JSON output for log aggregation systems
- **Smart Assertions**: `ASSERT` and `enforce` with automatic source capture and logging
- **Semantic Exceptions**: Clear exception hierarchy (`ValidationError`, `ConfigurationError`, etc.)
- **Fast Startup**: Lazy imports for minimal performance impact
- **Library Silencing**: Automatically suppresses noisy third-party library logs

## Installation

Install with pip or your favorite PyPI package manager.

```bash
python -m pip install py-logguard
```

For development with optional dependencies:

```bash
python -m pip install py-logguard[dev]
```

For JSON logging support:

```bash
python -m pip install py-logguard[json]
```

## 🚩 Quick Start

<details>
<summary>Logging</summary>

Logguard provides a simple way to configure logging with sensible defaults. Just call `setup()` once and you're ready to go.

```python
from logguard import AppLogger

AppLogger.setup(log_file="logs/app.log", console_level="INFO")
logger = AppLogger.get_logger(__name__)

logger.info("Application started")
logger.debug("Debug info")
logger.warning("Warning")
logger.error("Error occurred")
```

Logging will output to both console and file, with automatic rotation when files get too large.

</details>

<details>
<summary>Assertions</summary>

Use `ASSERT` to validate conditions while automatically capturing context like file, line, function, and the expression itself.

```python
from logguard import ASSERT
from logguard.exceptions import ValidationError

def validate_user(name: str, age: int):
    ASSERT(bool(name), "Name cannot be empty")
    ASSERT(len(name) >= 2, "Name must have at least 2 characters")
    ASSERT(age >= 0, "Age must be positive")
    ASSERT(age <= 150, "Age seems unrealistic")

try:
    validate_user("", 25)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
```

When an assertion fails, logguard logs the full context and raises a `ValidationError` with rich details for debugging.

</details>

<details>
<summary>Specialized Assertions</summary>

Logguard includes helpers for common validation patterns:

```python
from logguard import (
    ASSERT_TYPE, ASSERT_NOT_NONE, ASSERT_NOT_EMPTY,
    ASSERT_IN, ASSERT_RANGE, ASSERT_EQUALS
)

ASSERT_TYPE(user, dict, "Expected a dictionary")
ASSERT_NOT_NONE(email, "Email is required")
ASSERT_NOT_EMPTY(name, "Name cannot be empty")
ASSERT_IN(status, ["active", "inactive"], "Invalid status")
ASSERT_RANGE(age, 0, 150, "Age out of range")
ASSERT_EQUALS(total, 100, "Total must be 100")
```

These functions provide cleaner, more readable assertions for specific use cases.

</details>

<details>
<summary>Custom Exceptions</summary>

Logguard provides a semantic exception hierarchy for clearer error handling:

```python
from logguard.exceptions import (
    ValidationError, ConfigurationError, ResourceNotFoundError
)

# Validation errors (from ASSERT failures)
raise ValidationError("Invalid input", field="email")

# Configuration errors
raise ConfigurationError("Invalid config", file_path="config.json")

# Resource errors
raise ResourceNotFoundError("User", identifier=123)
```

All exceptions include rich context information accessible via `.to_dict()` for logging.

</details>

<details>
<summary>JSON Logging</summary>

For production environments, enable JSON logs for structured log aggregation:

```python
from logguard import AppLogger

AppLogger.setup(json_logs=True)
logger = AppLogger.get_logger(__name__)

logger.info("User logged in", extra={"user_id": 123})
logger.error("Database error", extra={"error_code": "DB_001"})
```

Enable via environment variable: `export JSON_LOGS=true`

Requires: `pip install py-logguard[json]`

</details>

<br>

> See the `examples/` folder for more complete demonstrations.

## 📚 API Reference

<details>
<summary><strong>AppLogger</strong> - Logging Configuration & Management</summary>

`AppLogger` is the main interface for logging. Configure it once and get loggers throughout your application.

**Setup:**

```python
AppLogger.setup(
    log_file="logs/app.log",      # Path to log file
    console_level="INFO",          # Console output level
    file_level="DEBUG",            # File output level
    json_logs=False,               # Enable JSON formatting
    max_bytes=5_000_000,           # Max file size before rotation (bytes)
    backup_count=3,                # Number of rotated backups to keep
    force=False                    # 'True' will override existing handlers
)
```

**Methods:**

- `get_logger(name: str | None = None)` - Get or create a logger instance
- `set_level(level: str, handler_type: str = "all")` - Dynamically change log level ("console", "file", or "all")
- `reset()` - Reset configuration (useful for testing)

**Example:**

```python
AppLogger.setup(log_file="logs/app.log")
logger = AppLogger.get_logger(__name__)
logger.info("Starting application")
AppLogger.set_level("DEBUG")  # Change all handlers to DEBUG
```

</details>

<details>
<summary><strong>Assertions</strong> - Validation with Auto-Context</summary>

Assertions validate conditions and automatically capture context (file, line, function, expression) for debugging.

**Basic:**

- `ASSERT(condition, message="")` - Validate condition, auto-captures source context
- `enforce(condition, message, expression, filename, line, function, extra=None)` - Manual assertion with explicit context

**Specialized:**

```python
ASSERT_TYPE(value, dict, "Expected dictionary")          # Type checking
ASSERT_NOT_NONE(email, "Email required")                 # Non-None check
ASSERT_NOT_EMPTY(name, "Name cannot be empty")           # Non-empty check
ASSERT_IN(status, ["active", "inactive"], "Invalid")     # Membership check
ASSERT_RANGE(age, 18, 65, "Age out of range")            # Range check
ASSERT_EQUALS(count, 5, "Expected 5 items")              # Equality check
```

**Configuration:**

```python
from logguard import set_failure_handler

def custom_handler(message, expression, filename, line, function, extra):
    # Handle assertion failure your way
    print(f"Failed: {expression} at {filename}:{line}")

set_failure_handler(custom_handler)
```

**On Failure:**

- Logs the assertion details with context
- Raises `ValidationError` with full debugging information

</details>

<details>
<summary><strong>Exceptions</strong> - Semantic Error Hierarchy</summary>

All exceptions inherit from `AppBaseError` and include rich context information.

**Properties:**

- `message` - Error description
- `context` - Additional context data (dict)
- `.to_dict()` - Serialize to dictionary for logging

**Hierarchy:**

```txt
AppBaseError
├── ConfigurationError
│   └── MissingConfigError
├── ValidationError              (raised by ASSERT)
└── ResourceError
    ├── ResourceNotFoundError
    └── ForbiddenError
```

**Usage Examples:**

```python
from logguard.exceptions import (
    ValidationError,
    ConfigurationError,
    ResourceNotFoundError,
)

# Configuration errors
raise ConfigurationError("Invalid config", file_path="config.json")
raise MissingConfigError("DATABASE_URL", source=".env")

# Validation errors
raise ValidationError("Invalid email", field="email", value="invalid")

# Resource errors
raise ResourceNotFoundError("User", identifier=123)
raise ForbiddenError("Access denied for user", user_id=456)

# Serialize for logging
try:
    raise ValidationError("Invalid input", field="username")
except ValidationError as e:
    logger.exception(f"Error details: {e.to_dict()}")
```

</details>

## 🤝 Contributing

Contributions, issues and feature requests are welcome. </br>
Feel free to check the issues page.

## 📜 License

[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

Happy coding! ❤️
