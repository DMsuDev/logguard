"""
Comprehensive tests for logguard.exceptions module.

Tests cover:
- Base exception class (AppBaseError)
- All exception subclasses
- Exception hierarchy
- Context and metadata
- to_dict() serialization
- String representations
- Integration scenarios
"""

import pytest

from logguard.exceptions import (
    AppBaseError,
    AuthenticationError,
    ConfigurationError,
    DataFormatError,
    ExternalServiceError,
    MissingConfigError,
    OperationError,
    PermissionError,
    ResourceNotFoundError,
    RetryableError,
    ValidationError,
)


class TestAppBaseError:
    """Tests for base AppBaseError class."""

    def test_basic_error_creation(self) -> None:
        """Test creating basic AppBaseError."""
        error = AppBaseError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.context == {}
        assert error.status_code == 500

    def test_error_with_context(self) -> None:
        """Test AppBaseError with context dictionary."""
        error = AppBaseError("Error occurred", context={"user_id": 123, "action": "delete"})
        assert error.message == "Error occurred"
        assert error.context["user_id"] == 123
        assert error.context["action"] == "delete"

    def test_error_with_custom_status_code(self) -> None:
        """Test AppBaseError with custom status code."""
        error = AppBaseError("Not found", status_code=404)
        assert error.status_code == 404

    def test_error_str_includes_context(self) -> None:
        """Test that str() representation includes context."""
        error = AppBaseError("Test error", context={"key": "value", "count": 42})
        error_str = str(error)
        assert "Test error" in error_str
        assert "key=" in error_str or "count=" in error_str

    def test_error_repr(self) -> None:
        """Test repr() representation."""
        error = AppBaseError("Test", context={"x": 1})
        error_repr = repr(error)
        assert "AppBaseError" in error_repr
        assert "Test" in error_repr

    def test_error_to_dict(self) -> None:
        """Test to_dict() serialization."""
        error = AppBaseError("Test error", context={"key": "value"}, status_code=400)
        error_dict = error.to_dict()

        assert error_dict["type"] == "AppBaseError"
        assert error_dict["message"] == "Test error"
        assert error_dict["context"]["key"] == "value"
        assert error_dict["status_code"] == 400

    def test_error_with_cause(self) -> None:
        """Test error with __cause__ (exception chaining)."""
        original = ValueError("Original error")
        error = None
        try:
            try:
                raise original
            except ValueError as e:
                raise AppBaseError("Wrapped error") from e
        except AppBaseError as app_err:
            error = app_err

        assert error is not None
        assert error.cause is original
        assert str(error.cause) == "Original error"
        error_dict = error.to_dict()
        assert error_dict["cause"] is not None

    def test_error_default_message(self) -> None:
        """Test AppBaseError with default message."""
        error = AppBaseError()
        assert error.message == "Application error"
        assert error.status_code == 500

    def test_error_inheritance(self) -> None:
        """Test that AppBaseError is an Exception."""
        error = AppBaseError("Test")
        assert isinstance(error, Exception)
        assert isinstance(error, AppBaseError)


class TestConfigurationError:
    """Tests for ConfigurationError and related exceptions."""

    def test_configuration_error_basic(self) -> None:
        """Test basic ConfigurationError creation."""
        error = ConfigurationError("Config failed")
        assert error.message == "Config failed"
        assert isinstance(error, AppBaseError)

    def test_configuration_error_with_config_key(self) -> None:
        """Test ConfigurationError with config_key parameter."""
        error = ConfigurationError("Invalid configuration", config_key="DATABASE_URL")
        assert error.context["config_key"] == "DATABASE_URL"

    def test_configuration_error_with_file_path(self) -> None:
        """Test ConfigurationError with file_path parameter."""
        error = ConfigurationError("Config file error", file_path="/etc/app/config.json")
        assert error.context["file_path"] == "/etc/app/config.json"

    def test_configuration_error_with_kwargs(self) -> None:
        """Test ConfigurationError with additional kwargs."""
        error = ConfigurationError("Error", config_key="API_KEY", environment="production")
        assert error.context["config_key"] == "API_KEY"
        assert error.context["environment"] == "production"

    def test_missing_config_error(self) -> None:
        """Test MissingConfigError subclass."""
        error = MissingConfigError(key="API_KEY", source=".env")
        assert "API_KEY" in error.message
        assert error.context["config_key"] == "API_KEY"
        assert error.context["source"] == ".env"
        assert isinstance(error, ConfigurationError)

    def test_missing_config_error_default_source(self) -> None:
        """Test MissingConfigError with default source."""
        error = MissingConfigError(key="SECRET_KEY")
        assert error.context["source"] == "config"


class TestValidationError:
    """Tests for ValidationError and related exceptions."""

    def test_validation_error_basic(self) -> None:
        """Test basic ValidationError creation."""
        error = ValidationError("Validation failed")
        assert error.message == "Validation failed"
        assert error.status_code == 422
        assert isinstance(error, AppBaseError)

    def test_validation_error_with_field(self) -> None:
        """Test ValidationError with field parameter."""
        error = ValidationError("Invalid value", field="age")
        assert error.context["field"] == "age"

    def test_validation_error_with_value(self) -> None:
        """Test ValidationError with value parameter."""
        error = ValidationError("Out of range", value=150)
        assert error.context["value"] == 150

    def test_validation_error_with_field_and_value(self) -> None:
        """Test ValidationError with both field and value."""
        error = ValidationError("Invalid email", field="email", value="invalid@")
        assert error.context["field"] == "email"
        assert error.context["value"] == "invalid@"

    def test_validation_error_default_message(self) -> None:
        """Test ValidationError with default message."""
        error = ValidationError()
        assert error.message == "Validation failed"

    def test_data_format_error(self) -> None:
        """Test DataFormatError subclass."""
        error = DataFormatError("Invalid JSON", field="data")
        assert "Invalid JSON" in error.message
        assert isinstance(error, ValidationError)
        assert isinstance(error, AppBaseError)

    def test_validation_error_subclass(self) -> None:
        """Test ValidationError with field information."""
        error = ValidationError("Invalid input", field="email")
        assert error.status_code == 422
        assert error.context["field"] == "email"
        assert isinstance(error, AppBaseError)


class TestResourceErrors:
    """Tests for resource-related exceptions."""

    def test_resource_not_found_error(self) -> None:
        """Test ResourceNotFoundError basic creation."""
        error = ResourceNotFoundError(resource_type="User", identifier=123)
        assert "User" in error.message
        assert "123" in error.message
        assert error.status_code == 404
        assert error.context["type"] == "User"
        assert error.context["id"] == 123

    def test_resource_not_found_with_string_identifier(self) -> None:
        """Test ResourceNotFoundError with string identifier."""
        error = ResourceNotFoundError(resource_type="File", identifier="/path/to/file.txt")
        assert "File" in error.message
        assert "/path/to/file.txt" in error.message

    def test_resource_not_found_with_kwargs(self) -> None:
        """Test ResourceNotFoundError with additional kwargs."""
        error = ResourceNotFoundError(
            resource_type="Document", identifier="doc-123", tenant="acme-corp"
        )
        assert error.context["id"] == "doc-123"
        assert error.context["tenant"] == "acme-corp"

    def test_authentication_error(self) -> None:
        """Test AuthenticationError basic creation."""
        error = AuthenticationError()
        assert error.message == "Authentication failed"
        assert error.status_code == 401
        assert isinstance(error, AppBaseError)

    def test_authentication_error_custom_message(self) -> None:
        """Test AuthenticationError with custom message."""
        error = AuthenticationError("Invalid token")
        assert error.message == "Invalid token"
        assert error.status_code == 401

    def test_authentication_error_with_context(self) -> None:
        """Test AuthenticationError with context."""
        error = AuthenticationError("Token expired", token_type="JWT", expired_at="2024-01-01")
        assert error.context["token_type"] == "JWT"
        assert error.context["expired_at"] == "2024-01-01"

    def test_permission_error(self) -> None:
        """Test PermissionError basic creation."""
        error = PermissionError()
        assert error.message == "Permission denied"
        assert error.status_code == 403

    def test_permission_error_custom(self) -> None:
        """Test PermissionError with custom message and context."""
        error = PermissionError("Insufficient privileges", required_role="admin", user_role="user")
        assert "Insufficient privileges" in error.message
        assert error.context["required_role"] == "admin"
        assert error.context["user_role"] == "user"


class TestOperationErrors:
    """Tests for operation-related exceptions."""

    def test_operation_error_basic(self) -> None:
        """Test basic OperationError creation."""
        error = OperationError("Operation failed")
        assert error.message == "Operation failed"
        assert isinstance(error, AppBaseError)

    def test_operation_error_with_context(self) -> None:
        """Test OperationError with context."""
        error = OperationError("Payment failed", context={"amount": 100, "currency": "USD"})
        assert error.context["amount"] == 100
        assert error.context["currency"] == "USD"

    def test_retryable_error(self) -> None:
        """Test RetryableError creation."""
        error = RetryableError("Network timeout")
        assert error.message == "Network timeout"
        assert error.status_code == 503
        assert isinstance(error, OperationError)

    def test_retryable_error_with_retry_after(self) -> None:
        """Test RetryableError with retry_after parameter."""
        error = RetryableError("Rate limited", retry_after=60)
        assert error.context["retry_after"] == 60

    def test_retryable_error_default_message(self) -> None:
        """Test RetryableError with default message."""
        error = RetryableError()
        assert error.message == "Retryable error"

    def test_retryable_error_with_additional_context(self) -> None:
        """Test RetryableError with additional context."""
        error = RetryableError("Temporary failure", retry_after=30, attempt=3, max_attempts=5)
        assert error.context["retry_after"] == 30
        assert error.context["attempt"] == 3
        assert error.context["max_attempts"] == 5


class TestExternalServiceError:
    """Tests for external service exceptions."""

    def test_external_service_error_basic(self) -> None:
        """Test basic ExternalServiceError creation."""
        error = ExternalServiceError(service="PaymentAPI", message="Service unavailable")
        assert error.message == "Service unavailable"
        assert error.status_code == 502
        assert error.context["service"] == "PaymentAPI"

    def test_external_service_error_with_original_exception(self) -> None:
        """Test ExternalServiceError with original exception."""
        original = ConnectionError("Connection refused")
        error = ExternalServiceError(
            service="Database", message="DB connection failed", original_exc=original
        )
        assert error.context["service"] == "Database"
        assert error.context["original"] is not None
        assert "Connection refused" in error.context["original"]

    def test_external_service_error_default_message(self) -> None:
        """Test ExternalServiceError with default message."""
        error = ExternalServiceError(service="API")
        assert error.message == "Error in external service"
        assert error.context["service"] == "API"

    def test_external_service_error_with_kwargs(self) -> None:
        """Test ExternalServiceError with additional kwargs."""
        error = ExternalServiceError(
            service="S3", message="Upload failed", bucket="my-bucket", key="file.txt"
        )
        assert error.context["service"] == "S3"
        assert error.context["bucket"] == "my-bucket"
        assert error.context["key"] == "file.txt"


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_all_inherit_from_base(self) -> None:
        """Test that all custom exceptions inherit from AppBaseError."""
        exceptions = [
            ConfigurationError("test"),
            MissingConfigError("key"),
            ValidationError("test"),
            DataFormatError("test"),
            ValidationError("test"),
            ResourceNotFoundError("Type", 1),
            AuthenticationError("test"),
            PermissionError("test"),
            OperationError("test"),
            RetryableError("test"),
            ExternalServiceError("Service", "test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, AppBaseError)
            assert isinstance(exc, Exception)

    def test_validation_hierarchy(self) -> None:
        """Test ValidationError inheritance hierarchy."""
        data_error = DataFormatError("test")
        assert isinstance(data_error, DataFormatError)
        assert isinstance(data_error, ValidationError)
        assert isinstance(data_error, AppBaseError)

        validation_error = ValidationError("test", field="email")
        assert isinstance(validation_error, ValidationError)
        assert isinstance(validation_error, AppBaseError)

    def test_operation_hierarchy(self) -> None:
        """Test OperationError inheritance hierarchy."""
        retryable = RetryableError("test")
        assert isinstance(retryable, RetryableError)
        assert isinstance(retryable, OperationError)
        assert isinstance(retryable, AppBaseError)

    def test_config_hierarchy(self) -> None:
        """Test ConfigurationError inheritance hierarchy."""
        missing = MissingConfigError("key")
        assert isinstance(missing, MissingConfigError)
        assert isinstance(missing, ConfigurationError)
        assert isinstance(missing, AppBaseError)


class TestExceptionSerialization:
    """Tests for exception serialization methods."""

    def test_to_dict_all_exceptions(self) -> None:
        """Test to_dict() for all exception types."""
        exceptions = [
            AppBaseError("test"),
            ConfigurationError("test"),
            ValidationError("test", field="x", value=1),
            ResourceNotFoundError("User", 123),
            AuthenticationError("test"),
            OperationError("test"),
            ExternalServiceError("API", "test"),
        ]

        for exc in exceptions:
            exc_dict = exc.to_dict()
            assert "type" in exc_dict
            assert "message" in exc_dict
            assert "context" in exc_dict
            assert "status_code" in exc_dict
            assert exc_dict["type"] == exc.__class__.__name__

    def test_to_dict_preserves_context(self) -> None:
        """Test that to_dict() preserves all context information."""
        error = ValidationError(
            "Invalid data", field="email", value="invalid", reason="missing @ symbol"
        )
        error_dict = error.to_dict()

        assert error_dict["context"]["field"] == "email"
        assert error_dict["context"]["value"] == "invalid"
        assert error_dict["context"]["reason"] == "missing @ symbol"

    def test_str_and_repr_for_all(self) -> None:
        """Test str() and repr() for all exception types."""
        exceptions = [
            ConfigurationError("test"),
            ValidationError("test"),
            ResourceNotFoundError("User", 123),
            RetryableError("test"),
        ]

        for exc in exceptions:
            str_repr = str(exc)
            repr_repr = repr(exc)
            assert len(str_repr) > 0
            assert len(repr_repr) > 0
            assert exc.__class__.__name__ in repr_repr


class TestIntegrationScenarios:
    """Tests for real-world integration scenarios."""

    def test_exception_chaining(self) -> None:
        """Test exception chaining with custom exceptions."""
        with pytest.raises(AppBaseError) as exc_info:
            try:
                raise ValueError("Original")
            except ValueError as e:
                raise AppBaseError("Wrapped") from e

        assert exc_info.value.cause is not None
        assert isinstance(exc_info.value.cause, ValueError)

    def test_catch_by_hierarchy(self) -> None:
        """Test catching exceptions by base class."""

        def raise_validation() -> None:
            raise ValidationError("test")

        def raise_config() -> None:
            raise ConfigurationError("test")

        # Catch specific
        with pytest.raises(ValidationError):
            raise_validation()

        # Catch by base
        try:
            raise_validation()
        except AppBaseError as e:
            assert isinstance(e, ValidationError)

        try:
            raise_config()
        except AppBaseError as e:
            assert isinstance(e, ConfigurationError)

    def test_multiple_exception_handling(self) -> None:
        """Test handling multiple exception types."""

        def operation(error_type: str) -> None:
            if error_type == "validation":
                raise ValidationError("Invalid data")
            if error_type == "auth":
                raise AuthenticationError("Invalid token")
            if error_type == "config":
                raise ConfigurationError("Missing config")

        caught = []

        for error_type in ["validation", "auth", "config"]:
            try:
                operation(error_type)
            except ValidationError as e:
                caught.append(("validation", e))
            except AuthenticationError as e:
                caught.append(("auth", e))
            except ConfigurationError as e:
                caught.append(("config", e))

        assert len(caught) == 3
        assert caught[0][0] == "validation"
        assert caught[1][0] == "auth"
        assert caught[2][0] == "config"

    def test_exception_with_complex_context(self) -> None:
        """Test exception with complex nested context."""
        error = ValidationError(
            "Complex validation failed",
            field="user.profile.email",
            value={"email": "invalid", "verified": False},
            constraints={"format": "email", "required": True, "max_length": 255},
        )

        error_dict = error.to_dict()
        assert error_dict["context"]["field"] == "user.profile.email"
        assert isinstance(error_dict["context"]["value"], dict)
        assert isinstance(error_dict["context"]["constraints"], dict)

    def test_reraise_with_additional_context(self) -> None:
        """Test catching and re-raising with additional context."""
        try:
            try:
                raise ValidationError("Original", field="email")
            except ValidationError as e:
                # Add more context
                e.context["retry_count"] = 3
                e.context["timestamp"] = "2024-01-01"
                raise
        except ValidationError as ve:
            assert ve.context["field"] == "email"
            assert ve.context["retry_count"] == 3
            assert ve.context["timestamp"] == "2024-01-01"
