# Logguard

[![Python](https://img.shields.io/badge/Language-Python-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![Supported Python Versions](https://img.shields.io/pypi/pyversions/py-logguard)](https://pypi.org/project/py-logguard/)
[![PyPI](https://img.shields.io/pypi/v/py-logguard?style=flat&logo=pypi&logoColor=white)](https://pypi.org/project/py-logguard/)

![Status](https://img.shields.io/badge/status-beta-yellow?style=flat)
[![license](https://img.shields.io/badge/license-MIT-blue?logo=opensourceinitiative&logoColor=white)](https://raw.githubusercontent.com/DMsuDev/logguard/main/LICENSE.rst)

Logguard is a lightweight logging and assertion library designed to make it easy to capture rich context and structured logs in Python applications. It provides a simple API for logging with automatic source capture, flexible configuration, and a semantic exception hierarchy.

It is built on top of the `logging` and `rich` libraries for enhanced logging capabilities.

## ⭐ Features

- **Easy Configuration**: Set up logging in one line with `AppLogger`
- **File Rotation**: Automatic log rotation with configurable size and backup count
- **Rich Console Output**: Beautiful console logs with [Rich](https://github.com/Textualize/rich) support
- **JSON Logging**: Optional structured JSON output for log aggregation systems
- **Environment-Aware Assertions**: `CHECK`, `ASSERT`, `ENSURE`, `VERIFY` with context
- **Specialized Helpers**: `ASSERT_TYPE`, `ASSERT_IN_RANGE`, `ASSERT_NOT_NULL`, etc.
- **Semantic Exceptions**: Clear exception hierarchy (`ValidationError`, `AssertFailure`, etc.)
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

Logguard provides environment-aware assertions that adapt their behavior based on `APP_ENV`:

| Assertion | Development | Production | Use Case            |
| --------- | ----------- | ---------- | ------------------- |
| `CHECK`   | Raises      | Raises     | Critical invariants |
| `ASSERT`  | Raises      | Ignored    | Debug checks        |
| `ENSURE`  | Raises      | Logs       | Preconditions       |
| `VERIFY`  | Raises      | Logs       | Postconditions      |

```python
from logguard import CHECK, ASSERT, ENSURE, VERIFY

# CHECK: Always raises - use for critical invariants
CHECK(config is not None, "Configuration required", component="auth")

# ASSERT: Raises in dev, ignored in prod - use for debugging
ASSERT(age > 0, "Age must be positive", age=age)

# ENSURE: Raises in dev, logs in prod - use for preconditions
def process_order(order):
    ENSURE(order.is_valid(), "Invalid order", order_id=order.id)

# VERIFY: Raises in dev, logs in prod - use for postconditions
result = calculate_total(items)
VERIFY(result >= 0, "Total cannot be negative", result=result)
```

Configure environment via `APP_ENV` variable:

- Development: `dev`, `development`, `local`, `test`
- Production: `prod`, `production`

</details>

<details>
<summary>Specialized Assertions</summary>

Logguard includes helpers for common validation patterns:

```python
from logguard import (
    ASSERT_NOT_NULL,
    ASSERT_TYPE,
    ASSERT_IN_RANGE,
    ASSERT_EQUALS,
    ASSERT_IN,
    ASSERT_NOT_EMPTY,
    ASSERT_GREATER,
    ASSERT_LESS,
)

# Null checks
ASSERT_NOT_NULL(user, "User is required")

# Type checking
ASSERT_TYPE(config, dict, "Expected dictionary")

# Range validation (inclusive)
ASSERT_IN_RANGE(percentage, 0, 100, "Invalid percentage")

# Equality
ASSERT_EQUALS(response.status, 200, "Expected success")

# Membership
ASSERT_IN(status, ["pending", "active"], "Invalid status")

# Non-empty
ASSERT_NOT_EMPTY(items, "Items list cannot be empty")

# Comparisons
ASSERT_GREATER(balance, 0, "Balance must be positive")
ASSERT_LESS(retry_count, max_retries, "Too many retries")
```

Each helper raises a specific exception type (`NullError`, `TypeErrorAssert`, `RangeError`, etc.) for precise error handling.

</details>

<details>
<summary>Custom Exceptions</summary>

Logguard provides a semantic exception hierarchy for clearer error handling:

```python
from logguard import (
    LogGuardError,
    ValidationError,
    AssertFailure,
    NullError,
    RangeError,
    ConfigurationError,
    ResourceNotFoundError,
    ForbiddenError,
)

# All exceptions include rich context
try:
    raise ValidationError("Invalid email", context={"field": "email", "value": "bad@"})
except LogGuardError as e:
    print(f"Error: {e}")
    print(f"Details: {e.to_dict()}")
    # {'type': 'ValidationError', 'message': 'Invalid email', 'context': {'field': 'email', 'value': 'bad@'}}

# Catch specific assertion failures
try:
    ASSERT_IN_RANGE(age, 0, 150)
except RangeError as e:
    handle_invalid_age(e.context)

# Resource errors
raise ResourceNotFoundError("User", identifier=123)
raise ForbiddenError("Access denied", user_id=456)
```

**Exception Hierarchy:**

```txt
LogGuardError
├── ConfigurationError
│   └── MissingConfigError
├── ValidationError
│   └── AssertFailure
│       ├── NullError
│       ├── RangeError
│       ├── TypeErrorAssert
│       ├── EmptyError
│       ├── EqualsError
│       ├── ComparisonError
│       └── MembershipError
└── ResourceError
    ├── ResourceNotFoundError
    └── ForbiddenError
```

</details>

<details>
<summary>Configuration</summary>

Configure the assertion system programmatically:

```python
from logguard import AssertionConfig, AssertionManager

# Switch to production mode (ASSERT becomes no-op)
AssertionManager.configure(
    AssertionConfig(environment="production", enable_asserts=True)
)

# Custom failure handlers
def my_raise_handler(message, context, exception_class):
    # Log to Sentry, then raise
    sentry.capture_message(message, extra=context)
    raise exception_class(message, context=context)

def my_log_handler(message, context, exception_class):
    # Custom logging
    metrics.increment("assertion_failures")
    logger.warning(f"{exception_class.__name__}: {message}")

AssertionManager.set_failure_strategy(
    raise_strategy=my_raise_handler,
    log_strategy=my_log_handler,
)

# Reset to defaults (useful for testing)
AssertionManager.reset()
```

</details>

<details>
<summary>JSON Logging</summary>

For production environments, enable JSON logs for structured log aggregation:

```python
from logguard import AppLogger

AppLogger.setup(json_logs=True, log_file="logs/app.json")
logger = AppLogger.get_logger(__name__)

logger.info("User logged in", extra={"user_id": 123})
logger.error("Database error", extra={"error_code": "DB_001"})
```

Requires: `pip install py-logguard[json]`

</details>

<br>

> **💡 Tip**: Check out [`examples/demo.py`](examples/demo.py) for a complete, interactive demonstration of all LogGuard features with Rich console output!

Run it with:

```bash
python examples/demo.py
```

## 📚 API Reference

<details>
<summary><strong>AppLogger</strong> - Logging Configuration</summary>

`AppLogger` is the main interface for logging. Configure it once and get loggers throughout your application.

**Setup:**

```python
AppLogger.setup(
    log_file="logs/app.log",      # Path to log file
    console_level="INFO",          # Console output level
    file_level="DEBUG",            # File output level
    json_logs=False,               # Enable JSON formatting
    max_bytes=5_000_000,           # Max file size before rotation
    backup_count=3,                # Number of backups to keep
    delay=True,                    # Delay file creation until first log
)
```

**Methods:**

- `get_logger(name: str | None = None)` - Get or create a logger instance
- `set_level(level: str, handler_type: str = "all")` - Change log level dynamically
- `silence_noisy_libraries(modules: list[str] | None = None)` - Suppress third-party logs
- `reset()` - Reset configuration (useful for testing)

</details>

<details>
<summary><strong>Assertions</strong> - Environment-Aware Validation</summary>

**Core Assertions:**

| Function                                | Behavior                       |
| --------------------------------------- | ------------------------------ |
| `CHECK(condition, message, **context)`  | Always raises `AssertFailure`  |
| `ASSERT(condition, message, **context)` | Raises in dev, ignored in prod |
| `ENSURE(condition, message, **context)` | Raises in dev, logs in prod    |
| `VERIFY(condition, message, **context)` | Raises in dev, logs in prod    |

**Specialized Helpers:**

| Function                                             | Exception Type    |
| ---------------------------------------------------- | ----------------- |
| `ASSERT_NOT_NULL(value, message)`                    | `NullError`       |
| `ASSERT_NULL(value, message)`                        | `NullError`       |
| `ASSERT_EQUALS(actual, expected, message)`           | `EqualsError`     |
| `ASSERT_GREATER(a, b, message)`                      | `ComparisonError` |
| `ASSERT_LESS(a, b, message)`                         | `ComparisonError` |
| `ASSERT_IN_RANGE(value, min, max, message)`          | `RangeError`      |
| `ASSERT_BETWEEN_EXCLUSIVE(value, min, max, message)` | `RangeError`      |
| `ASSERT_TYPE(value, expected, message)`              | `TypeErrorAssert` |
| `ASSERT_NOT_EMPTY(value, message)`                   | `EmptyError`      |
| `ASSERT_IN(item, container, message)`                | `MembershipError` |

**Configuration Classes:**

- `AssertionConfig(environment, enable_asserts)` - Configuration dataclass
- `AssertionManager` - Central assertion engine with `configure()`, `set_failure_strategy()`, `reset()`

</details>

<details>
<summary><strong>Exceptions</strong> - Semantic Error Hierarchy</summary>

All exceptions inherit from `LogGuardError` and include rich context information.

**Properties:**

- `message` - Error description
- `context` - Additional context data (dict)
- `.to_dict()` - Serialize to dictionary for logging

**Exception Types:**

| Exception               | Description                 |
| ----------------------- | --------------------------- |
| `LogGuardError`         | Base for all exceptions     |
| `ConfigurationError`    | Invalid configuration       |
| `MissingConfigError`    | Required config key missing |
| `ValidationError`       | Validation failures         |
| `AssertFailure`         | Base for assertion failures |
| `NullError`             | Unexpected None value       |
| `RangeError`            | Value out of range          |
| `TypeErrorAssert`       | Wrong type                  |
| `EmptyError`            | Unexpected empty value      |
| `EqualsError`           | Values not equal            |
| `ComparisonError`       | Comparison failed           |
| `MembershipError`       | Item not in container       |
| `ResourceError`         | Resource-related errors     |
| `ResourceNotFoundError` | Resource not found          |
| `ForbiddenError`        | Permission denied           |

</details>

## 🤝 Contributing

Contributions, issues and feature requests are welcome.
Feel free to check the issues page.

## 📜 License

[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

Happy coding! ❤️
