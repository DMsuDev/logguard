"""
Test script for new logguard improvements.

Tests:
- Auto-capture of local variables
- New assert helpers (ASSERT_TYPE, ASSERT_IN, ASSERT_RANGE, etc.)
- Dynamic log level changes
"""

from logguard import (
    ASSERT,
    ASSERT_EQUALS,
    ASSERT_IN,
    ASSERT_NOT_EMPTY,
    ASSERT_NOT_NONE,
    ASSERT_RANGE,
    ASSERT_TYPE,
    AppLogger,
    ValidationError,
)


def test_assert_helpers() -> None:
    """Test all new assert helpers."""
    logger = AppLogger.get_logger(__name__)
    logger.info("=== Testing Assert Helpers ===")

    # Test ASSERT_TYPE
    print("\n[1] ASSERT_TYPE")
    try:
        user_id = 123
        ASSERT_TYPE(user_id, int)
        print(f"[OK] {user_id} is int")

        ASSERT_TYPE("hello", str)
        print("[OK] 'hello' is str")

        ASSERT_TYPE([1, 2, 3], (list, tuple))
        print("[OK] [1,2,3] is list or tuple")
    except ValidationError as e:
        print(f"[ERROR] {e}")

    # Test ASSERT_IN
    print("\n[2] ASSERT_IN")
    try:
        status = "active"
        ASSERT_IN(status, ["active", "pending", "closed"])
        print(f"[OK] '{status}' in valid statuses")

        ASSERT_IN("name", {"name": "John", "age": 30})
        print("[OK] 'name' in dict keys")
    except ValidationError as e:
        print(f"[ERROR] {e}")

    # Test ASSERT_NOT_EMPTY
    print("\n[3] ASSERT_NOT_EMPTY")
    try:
        users = ["Alice", "Bob"]
        ASSERT_NOT_EMPTY(users)
        print("[OK] users list is not empty")

        name = "John"
        ASSERT_NOT_EMPTY(name)
        print(f"[OK] name '{name}' is not empty")
    except ValidationError as e:
        print(f"[ERROR] {e}")

    # Test ASSERT_RANGE
    print("\n[4] ASSERT_RANGE")
    try:
        age = 25
        ASSERT_RANGE(age, 0, 150)
        print(f"[OK] age {age} in range [0, 150]")

        temperature = 22.5
        ASSERT_RANGE(temperature, -50, 50)
        print(f"[OK] temperature {temperature} in range [-50, 50]")
    except ValidationError as e:
        print(f"[ERROR] {e}")

    # Test ASSERT_EQUALS
    print("\n[5] ASSERT_EQUALS")
    try:
        result = 2 + 2
        ASSERT_EQUALS(result, 4)
        print("[OK] 2 + 2 equals 4")

        ASSERT_EQUALS(len([1, 2, 3]), 3)
        print("[OK] list length equals 3")
    except ValidationError as e:
        print(f"[ERROR] {e}")

    # Test ASSERT_NOT_NONE
    print("\n[6] ASSERT_NOT_NONE")
    try:
        user = {"name": "Alice"}
        ASSERT_NOT_NONE(user)
        print("[OK] user is not None")

        value = 0  # 0 is not None!
        ASSERT_NOT_NONE(value)
        print(f"[OK] value {value} is not None")
    except ValidationError as e:
        print(f"[ERROR] {e}")


def test_auto_capture_locals() -> None:
    """Test automatic capture of local variables."""
    logger = AppLogger.get_logger(__name__)
    logger.info("\n=== Testing Auto-Capture of Local Variables ===")

    print("\n[Auto-capture test]")
    try:
        x = 10
        threshold = 15

        # This will fail and auto-capture x, threshold
        ASSERT(x > threshold, "x should be greater than threshold")
    except ValidationError:
        print("[ERROR] Assertion failed (expected)")
        print("[ERROR] Check logs for captured local variables: x, y, threshold")


def test_dynamic_log_level() -> None:
    """Test dynamic log level changes."""
    logger = AppLogger.get_logger(__name__)
    logger.info("\n=== Testing Dynamic Log Level Changes ===")

    print("\n[Log level test]")
    print("  Current level: INFO")
    logger.debug("This DEBUG message is hidden")
    logger.info("This INFO message is visible")

    print("\n  Changing to DEBUG level...")
    AppLogger.set_level("DEBUG")

    logger.debug("Now this DEBUG message is visible!")
    logger.info("INFO messages still visible")

    print("\n  Changing back to INFO level...")
    AppLogger.set_level("INFO")

    logger.debug("DEBUG hidden again")
    logger.info("INFO still visible")


def test_error_cases() -> None:
    """Test intentional failures with rich context."""
    logger = AppLogger.get_logger(__name__)
    logger.info("\n=== Testing Error Cases (Intentional Failures) ===")

    # Type error
    print("\n[1] Type mismatch")
    try:
        ASSERT_TYPE("123", int)
    except ValidationError as e:
        print(f"[ERROR] Caught: {e.message[:50]}...")

    # Not in container
    print("\n[2] Item not in container")
    try:
        ASSERT_IN("invalid", ["valid", "active"])
    except ValidationError as e:
        print(f"[ERROR] Caught: {e.message[:50]}...")

    # Empty collection
    print("\n[3] Empty collection")
    try:
        ASSERT_NOT_EMPTY([])
    except ValidationError as e:
        print(f"[ERROR] Caught: {e.message[:50]}...")

    # Out of range
    print("\n[4] Value out of range")
    try:
        ASSERT_RANGE(200, 0, 150)
    except ValidationError as e:
        print(f"[ERROR] Caught: {e.message[:50]}...")

    # Not equal
    print("\n[5] Values not equal")
    try:
        ASSERT_EQUALS(5, 10)
    except ValidationError as e:
        print(f"[ERROR] Caught: {e.message[:50]}...")


def main() -> None:
    """Run all tests."""
    AppLogger.setup(
        log_file="logs/test_improvements.log",
        console_level="INFO",
        file_level="DEBUG",
    )

    print("=" * 70)
    print("TESTING LOGGUARD IMPROVEMENTS")
    print("=" * 70)

    test_assert_helpers()
    test_auto_capture_locals()
    test_dynamic_log_level()
    test_error_cases()

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70)
    print("\nCheck 'logs/test_improvements.log' for detailed logs")


if __name__ == "__main__":
    main()
