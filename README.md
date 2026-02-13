# Logguard

**Structured logging and assertion utilities for Python**

Logguard provides a powerful yet simple logging configuration system with rich formatting support, automatic file rotation, and assertion utilities that capture context automatically.

## Features

- **🔧 Easy Configuration**: Set up logging in one line with `AppLogger`
- **📝 File Rotation**: Automatic log rotation with configurable size and backup count
- **🎨 Rich Console Output**: Beautiful console logs with [Rich](https://github.com/Textualize/rich) support
- **📊 JSON Logging**: Optional structured JSON output for log aggregation systems
- **✅ Smart Assertions**: `ASSERT` and `enforce` with automatic source capture and logging
- **🎯 Semantic Exceptions**: Clear exception hierarchy (`ValidationError`, `ConfigurationError`, etc.)
- **⚡ Fast Startup**: Lazy imports for minimal performance impact
- **🔇 Library Silencing**: Automatically suppresses noisy third-party library logs

## Installation

```bash
pip install logguard
```

For development with optional dependencies:

```bash
pip install -e ".[dev]"
```

For JSON logging support:

```bash
pip install -e ".[json]"
```

## Quick Start

### Basic Logging

```python
from logguard import AppLogger

# Configure logging (optional - auto-configures on first use)
AppLogger.setup(
    log_file="logs/app.log",
    console_level="INFO",
    file_level="DEBUG"
)

# Get a logger
logger = AppLogger.get_logger(__name__)

# Use it
logger.info("Application started")
logger.debug("Debug information")
logger.warning("Warning message")
logger.error("Error occurred")
```

### Assertions with Context

```python
from logguard import ASSERT, AppLogger
from logguard.exceptions import ValidationError

logger = AppLogger().get_logger("validation_example")

def process_user(name: str, age: int) -> dict:
    # ASSERT captures context automatically:
    # - Expression from source code
    # - Filename, line number, function name
    # - Local variables (optional)
    ASSERT(bool(name), "Name cannot be empty")
    ASSERT(len(name) >= 2, "Name must have at least 2 characters")
    ASSERT(age >= 0, "Age cannot be negative")
    ASSERT(age <= 150, "Age seems unrealistic")

    return {"name": name, "age": age, "valid": True}

# Assertions raise ValidationError on failure
try:
    process_user("", 25)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
```

### Manual Assertions with `enforce`

For cases where you need explicit control over assertion parameters, use `enforce`:

```python
from logguard import enforce

# enforce() requires you to provide all context manually
enforce(
    condition=value > 0,
    message="Value must be positive",
    expression="value > 0",
    filename=__file__,
    line=10,
    function="my_function",
    extra={"value": value}
)
```

### Custom Exceptions

```python
from logguard.exceptions import (
    ValidationError,
    ConfigurationError,
    ResourceNotFoundError,
    AuthenticationError,
    ExternalServiceError
)

# Use semantic exceptions for clearer error handling
def load_config(path: str):
    if not os.path.exists(path):
        raise ConfigurationError(f"Config file not found: {path}")

# Catch resource errors
try:
    get_user(user_id)
except ResourceNotFoundError as e:
    logger.error(f"User not found: {e}")

# External service error handling
try:
    # Your code that calls an external API
    api_call(...)
except ExternalServiceError as e:
    logger.error(f"Service error: {e}")
```

## Advanced Usage

### Logger Configuration Options

```python
AppLogger.setup(
    log_file="logs/myapp.log",      # Path to log file
    console_level="INFO",             # Console log level
    file_level="DEBUG",               # File log level
    json_logs=False,                  # Enable JSON formatting
    max_bytes=5_000_000,              # Max file size (5MB)
    backup_count=3,                   # Number of backup files
    force=False                       # Force reconfiguration
)
```

### Dynamic Log Level Changes

```python
# Change log level at runtime
AppLogger.set_level("DEBUG", handler_type="console")
AppLogger.set_level("WARNING", handler_type="file")
AppLogger.set_level("INFO", handler_type="all")
```

### Auto-detection of Logger Name

```python
# Automatically uses the module name
logger = AppLogger.get_logger()  # Uses __name__ of calling module

# Or explicitly specify
logger = AppLogger.get_logger("myapp.services")
```

### JSON Logging for Production

```python
import os

from logguard.logger import AppLogger

# Enable JSON logs via environment variable
os.environ["JSON_LOGS"] = "true"

# Or directly in setup
AppLogger.setup(json_logs=True)

logger = AppLogger().get_logger("example")
logger.info("This is an info message with JSON formatting!")
logger.error("This is an error message with JSON formatting!")

# Installed via: pip install -e ".[json]" or pip install python-json-logger>=2.0
```

## Exception Hierarchy

Logguard provides a semantic exception hierarchy for clearer error handling:

- **`AppBaseError`** - Base exception for all logguard errors
- **`ValidationError`** - Data validation failures (raised by ASSERT)
- **`ConfigurationError`** - Configuration or setup issues
- **`ResourceError`** - Base for resource-related errors
  - **`ResourceNotFoundError`** - Requested resource doesn't exist
  - **`AuthenticationError`** - Authentication/authorization failed
  - **`PermissionError`** - Permission denied
- **`OperationError`** - Business operation failures
- **`ExternalServiceError`** - External service failures
  - **`RateLimitError`** - Rate limit exceeded

## API Reference

### AppLogger

**Setup Method:**

```python
AppLogger.setup(
    log_file: str | None = None,
    console_level: str = "INFO",
    file_level: str = "DEBUG", 
    json_logs: bool = False,
    max_bytes: int = 5_000_000,
    backup_count: int = 3,
    force: bool = False
) -> None
```

**Main Methods:**

- `setup(...)` - Configure the logging system
- `get_logger(name: str | None = None)` - Get or create a logger instance
- `set_level(level: str, handler_type: str = "all")` - Change log level dynamically
- `reset()` - Reset logging configuration (useful for testing)

### Assertions

**Basic Assertions:**

- `ASSERT(condition, message="")` - Raise `ValidationError` if condition is False (auto-captures expression, file, line)
- `enforce(condition, message="", ...)` - Explicit assertion (requires manual parameters: expression, filename, line, function)

**Specialized Assertions:**

- `ASSERT_TYPE(value, expected_type, message="")` - Assert value is of expected type
- `ASSERT_NOT_NONE(value, message="")` - Assert value is not None
- `ASSERT_NOT_EMPTY(value, message="")` - Assert string/collection is not empty
- `ASSERT_IN(value, collection, message="")` - Assert value is in collection
- `ASSERT_RANGE(value, min_val, max_val, message="")` - Assert value is in range
- `ASSERT_EQUALS(actual, expected, message="")` - Assert values are equal

**Configuration:**

- `set_failure_handler(handler)` - Custom handler for assertion failures

### Exceptions

All exceptions inherit from `AppBaseError` and include:
- `message` - Description of the error
- `context` - Additional context data (dict)
- `status_code` - Suggested HTTP status code
- `to_dict()` - Serialize exception to dictionary

**Exception Classes:**

```
AppBaseError (base for all)
├── ConfigurationError
│   └── MissingConfigError
├── ValidationError
│   └── DataFormatError
├── ResourceError
│   ├── ResourceNotFoundError
│   ├── AuthenticationError
│   └── PermissionError (custom exception - see note below)
├── OperationError
│   ├── RetryableError
│   └── FatalOperationError
└── ExternalServiceError
    └── RateLimitError
```

**Note on PermissionError:** Logguard provides a custom `PermissionError` exception for application-level permission errors. This is distinct from Python's built-in `PermissionError` (used for OS-level errors). Always import explicitly from logguard to use this exception.

**Usage Examples:**

```python
# Configuration errors
raise ConfigurationError("Invalid config", file_path="config.json")
raise MissingConfigError("DATABASE_URL", source=".env")

# Validation errors
raise ValidationError("Invalid input", field="email")
raise DataFormatError("Malformed JSON")

# Resource errors
raise ResourceNotFoundError("User", identifier=123)
raise AuthenticationError("Invalid credentials")
raise PermissionError("Access denied")

# Operation errors
raise RetryableError("Network timeout", retry_after=5)
raise FatalOperationError("Critical failure")

# External service errors
raise ExternalServiceError("API", "Service unavailable")
raise RateLimitError("GitHub", reset_time=1234567890)
```

## Examples

Check the `examples/` directory for complete examples:

- `basic_usage.py` - Basic logging and assertions
- `advanced_asserts.py` - Advanced assertion patterns
- `test_improvements.py` - Using logguard in tests
- `rich_exceptions_demo.py` - Rich-formatted exceptions & logger exceptions in a simple banking system simulator

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=logguard --cov-report=html

# Format code (use Ruff formatter)
ruff format .

# Auto-fix lintable issues
ruff check --fix .

# Type checking
mypy logguard/

# Lint
ruff check .
```

## Requirements

- Python 3.9+
- Optional: `rich` for beautiful console output
- Optional: `python-json-logger` for JSON formatting

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
