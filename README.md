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
from logguard import ASSERT
from logguard.exceptions import ValidationError

def process_user(name: str, age: int):
    # Assertions that capture context automatically
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

### Custom Exceptions

```python
from logguard.exceptions import (
    ValidationError,
    ConfigurationError,
    ResourceError,
    AuthorizationError
)

# Use semantic exceptions for clearer error handling
def load_config(path: str):
    if not os.path.exists(path):
        raise ConfigurationError(f"Config file not found: {path}")

    # ... load and validate config
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

# Enable JSON logs via environment variable
os.environ["JSON_LOGS"] = "true"

# Or directly in setup
AppLogger.setup(json_logs=True)

# Requires: pip install python-json-logger
```

## Exception Hierarchy

Logguard provides a semantic exception hierarchy for clearer error handling:

- **`LogguardError`** - Base exception for all logguard errors
  - **`ValidationError`** - Data validation failures (raised by ASSERT)
  - **`ConfigurationError`** - Configuration or setup issues
  - **`ResourceError`** - Resource access or availability problems
  - **`AuthorizationError`** - Permission or authentication failures

## API Reference

### AppLogger

**Methods:**

- `setup(...)` - Configure the logging system
- `get_logger(name=None)` - Get or create a logger instance
- `set_level(level, handler_type="all")` - Change log level dynamically
- `reset()` - Reset logging configuration (useful for testing)

### Assertions

- `ASSERT(condition, message="")` - Raise `ValidationError` if condition is False
- `enforce(condition, message="")` - Alias for `ASSERT`

## Examples

Check the `examples/` directory for complete examples:

- `basic_usage.py` - Basic logging and assertions
- `advanced_asserts.py` - Advanced assertion patterns
- `test_improvements.py` - Using logguard in tests

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
