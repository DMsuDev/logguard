"""
Advanced example demonstrating the use of LogGuard's AppLogger and ASSERT in a more complex application flow.

Shows:
- Multiple custom exception types
- ASSERT with additional context (extra)
- Cascading error handling
- Configuration, resource, and external service exceptions
- Structured logging with enriched context
"""

import time
from typing import Any

from logguard import ASSERT, AppLogger
from logguard.exceptions import (
    AuthenticationError,
    ConfigurationError,
    ExternalServiceError,
    MissingConfigError,
    OperationError,
    ResourceNotFoundError,
    RetryableError,
    ValidationError,
)


# Simulation of an application configuration manager, database service, authentication service, and payment processor.
# Each component demonstrates the use of ASSERT for validations and raises custom exceptions with context.
class AppConfig:
    """Configuration manager with validations."""

    def __init__(self) -> None:
        self._config = {}
        self.logger = AppLogger.get_logger(__name__)

    def load(self, config: dict) -> None:
        """Loads and validates the configuration."""
        self.logger.info("Loading configuration", extra={"config_keys": list(config.keys())})

        # Validate required keys
        required_keys = ["database_url", "api_key", "max_retries", "timeout"]

        for key in required_keys:
            if key not in config:
                raise MissingConfigError(key=key, source="config_dict")

        # Validations with ASSERT and extra context
        ASSERT(
            isinstance(config["max_retries"], int),
            "max_retries must be an integer",
            extra={"received_type": type(config["max_retries"]).__name__},
        )

        ASSERT(
            config["max_retries"] > 0,
            "max_retries must be positive",
            extra={"value": config["max_retries"]},
        )

        ASSERT(
            config["timeout"] > 0,
            "timeout must be positive",
            extra={"value": config["timeout"], "unit": "seconds"},
        )

        ASSERT(
            len(config["api_key"]) >= 10,
            "api_key too short",
            extra={"length": len(config["api_key"]), "min_length": 10},
        )

        self._config = config
        self.logger.info("Configuration loaded successfully", extra=self._config)

    def get(self, key: str) -> Any:
        """Gets a configuration value."""
        if key not in self._config:
            raise ConfigurationError(f"Configuration key not found: {key}", config_key=key)
        return self._config[key]


# Simulation of a database service
class DatabaseService:
    """Database service with error handling."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.logger = AppLogger.get_logger(__name__)
        self._connected = False
        self._users = {
            1: {"id": 1, "name": "Alice", "role": "admin"},
            2: {"id": 2, "name": "Bob", "role": "user"},
        }

    def connect(self) -> None:
        """Simulates database connection."""
        db_url = self.config.get("database_url")

        self.logger.info(f"Connecting to database: {db_url}")

        # Simulation: validate URL format
        ASSERT(
            db_url.startswith(("postgresql://", "mysql://", "sqlite://")),
            "Invalid database URL format",
            extra={"url": db_url, "supported": ["postgresql://", "mysql://", "sqlite://"]},
        )

        # Simulate random connection failure
        import random

        if random.random() < 0.3:  # 30% chance of failure
            raise ExternalServiceError(
                service="PostgreSQL",
                message="Failed to connect to the database",
                original_exc=ConnectionError("Connection timeout"),
            )

        self._connected = True
        self.logger.info("Successful database connection")

    def get_user(self, user_id: int) -> dict:
        """Gets a user by ID."""
        ASSERT(self._connected, "Database not connected")

        self.logger.debug(f"Searching for user with ID: {user_id}")

        ASSERT(
            isinstance(user_id, int),
            "User ID must be an integer",
            extra={"received_type": type(user_id).__name__},
        )

        ASSERT(user_id > 0, "User ID must be positive", extra={"value": user_id})

        if user_id not in self._users:
            raise ResourceNotFoundError(
                resource_type="User", identifier=user_id, available_ids=list(self._users.keys())
            )

        user = self._users[user_id]
        self.logger.info(f"User found: {user['name']}", extra={"user_id": user_id})
        return user


# Simulation of an authentication service
class AuthService:
    """Authentication service."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.logger = AppLogger.get_logger(__name__)
        self._valid_tokens = {"secret-token-123", "admin-token-456"}

    def authenticate(self, token: str) -> bool:
        """Validates an authentication token."""
        self.logger.debug(f"Authenticating token: {token[:10]}...")

        ASSERT(
            isinstance(token, str),
            "Token must be a string",
            extra={"received_type": type(token).__name__},
        )

        ASSERT(len(token) > 0, "Token must not be empty")

        if token not in self._valid_tokens:
            raise AuthenticationError(
                "Invalid or expired token",
                token_prefix=token[:10],
                reason="Token not found in valid tokens",
            )

        self.logger.info("Successful authentication", extra={"token_prefix": token[:10]})
        return True


# Simulation of a payment processor with retry logic
class PaymentProcessor:
    """Payment processor with retry logic."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.logger = AppLogger.get_logger(__name__)
        self.max_retries = config.get("max_retries")

    def process_payment(self, amount: float, user_id: int) -> dict:
        """Processes a payment with retries."""
        ASSERT(amount > 0, "Amount must be positive", extra={"amount": amount, "user_id": user_id})

        ASSERT(
            amount <= 10000,
            "Amount exceeds the allowed limit",
            extra={"amount": amount, "limit": 10000},
        )

        for attempt in range(1, self.max_retries + 1):
            try:
                self.logger.info(
                    f"Payment attempt {attempt}/{self.max_retries}",
                    extra={"amount": amount, "user_id": user_id},
                )

                # Simulate transient failures with a random chance
                import random

                if random.random() < 0.5 and attempt < self.max_retries:
                    raise RetryableError(
                        "Payment service temporarily unavailable",
                        retry_after=2,
                        attempt=attempt,
                        max_retries=self.max_retries,
                    )

                # Success
                self.logger.info(
                    "Payment processed successfully",
                    extra={"amount": amount, "user_id": user_id, "attempt": attempt},
                )
                return {
                    "status": "success",
                    "amount": amount,
                    "user_id": user_id,
                    "attempts": attempt,
                }

            except RetryableError as e:
                self.logger.warning(f"Retry {attempt}: {e}")
                if attempt == self.max_retries:
                    raise OperationError(
                        f"Payment failed after {self.max_retries} attempts",
                    ) from e
                time.sleep(e.context.get("retry_after", 1))

        # Should never reach here
        return {"status": "error", "amount": amount, "user_id": user_id}


def run_full_flow() -> None:
    """Runs a full application flow."""
    logger = AppLogger.get_logger(__name__)

    logger.debug("Starting full application flow", extra={"flow": "full_app_flow"})

    try:
        # 1. Load configuration
        print("\n[1] Loading configuration...")
        config = AppConfig()
        config.load(
            {
                "database_url": "postgresql://localhost:5432/mydb",
                "api_key": "super-secret-key-12345",
                "max_retries": 3,
                "timeout": 30,
            }
        )
        print("[OK] Configuration loaded successfully")

        # 2. Authentication
        print("\n[2] Authenticating user...")
        auth_service = AuthService(config)
        auth_service.authenticate("secret-token-123")
        print("[OK] Authentication successful")

        # 3. Connecting to database
        print("\n[3] Connecting to database...")
        db = DatabaseService(config)
        db.connect()
        print("[OK] Connection successful")

        # 4. Getting user
        print("\n[4] Getting user information...")
        user = db.get_user(1)
        print(f"[OK] User: {user['name']} ({user['role']})")

        # 5. Processing payment
        print("\n[5] Processing payment...")
        payment_processor = PaymentProcessor(config)
        result = payment_processor.process_payment(150.50, user["id"])
        print(f"[OK] Payment processed: ${result['amount']} in {result['attempts']} attempt(s)")

        logger.debug(
            "Flow completed successfully",
            extra={
                "flow": "full_app_flow",
                "user_id": user["id"],
                "payment_amount": result["amount"],
            },
        )
        print("\nFLOW COMPLETED SUCCESSFULLY" + "-" * 30)

    except MissingConfigError as e:
        logger.error(f"Missing configuration error: {e}", extra=e.context)
        print(f"\n[ERROR] Missing configuration: {e}")

    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}", extra=e.context)
        print(f"\n[ERROR] Invalid configuration: {e}")

    except AuthenticationError as e:
        logger.error(f"Authentication error: {e}", extra=e.context)
        print(f"\n[ERROR] Authentication failed: {e}")

    except ResourceNotFoundError as e:
        logger.error(f"Resource not found: {e}", extra=e.context)
        print(f"\n[ERROR] Resource not found: {e}")

    except ExternalServiceError as e:
        logger.error(f"External service error: {e}", extra=e.context)
        print(f"\n[ERROR] External service unavailable: {e}")

    except OperationError as e:
        logger.error(f"Operation error: {e}", extra=e.context)
        print(f"\n[ERROR] Operation failed: {e}")

    except ValidationError as e:
        logger.error(f"Validation error: {e}", extra=e.context)
        print(f"\n[ERROR] Validation failed: {e}")

    except Exception as e:
        logger.exception("Unexpected error")
        print(f"\n[ERROR] Unexpected error: {e}")


def main() -> None:
    """Main function."""
    # Configure logging
    AppLogger.setup(log_file="logs/advanced_example.log", console_level="INFO", file_level="DEBUG")

    # Run multiple times to see different scenarios (success, different failures, retries)
    print("\n" + "=" * 60)
    print("ADVANCED LOGGUARD EXAMPLE")
    print("=" * 60)
    print("\nThis example demonstrates:")
    print("- Multiple custom exception types")
    print("- ASSERT with additional context")
    print("- Cascading error handling")
    print("- Automatic retries")
    print("- Structured logging with enriched context")

    for i in range(1, 4):
        print(f"\n\nRUN {i}/3" + "-" * 50)
        run_full_flow()
        if i < 3:
            time.sleep(0.5)  # Short pause between runs


if __name__ == "__main__":
    main()
