"""
Basic Usage Example of logguard.

Demonstrates:
- Basic logger configuration
- Use of ASSERT for validations
- Basic exception handling
- Different log levels
"""

from logguard import ASSERT, AppLogger
from logguard.exceptions import ValidationError


def validate_user(name: str, age: int) -> dict:
    """Validates user data and returns a dictionary."""
    logger = AppLogger.get_logger(__name__)

    logger.info(f"Validating user: name={name}, age={age}")

    # Use ASSERT for simple validations
    try:
        ASSERT(bool(name), "Name cannot be empty")
        ASSERT(len(name) >= 2, "Name must have at least 2 characters")
        ASSERT(age >= 0, "Age cannot be negative")
        ASSERT(age <= 150, "Age cannot be greater than 150")

        logger.info(f"Valid user: {name}")
        return {"name": name, "age": age, "valid": True}

    except ValidationError as e:
        logger.error(f"[ERROR] Validation error: {e}")
        return {"name": name, "age": age, "valid": False, "error": str(e)}


def process_numbers(numbers: list) -> float:
    """Calculates the average of a list of numbers."""
    logger = AppLogger.get_logger(__name__)

    logger.debug(f"Processing {len(numbers)} numbers: {numbers}")

    ASSERT(isinstance(numbers, list), "Expected a list")
    ASSERT(len(numbers) > 0, "List cannot be empty")
    ASSERT(all(isinstance(n, (int, float)) for n in numbers), "All elements must be numbers")

    average = sum(numbers) / len(numbers)
    logger.info(f"Calculated average: {average:.2f}")

    return average


def main() -> None:
    """Main function demonstrating basic usage."""
    # Configure the logger (only once at the start of your application)
    AppLogger.setup(log_file="logs/basic_example.log", console_level="INFO", file_level="DEBUG")

    logger = AppLogger.get_logger(__name__)
    logger.info("=== Starting basic example ===")

    # Example 1: Successful validation
    print("\n--- Example 1: Valid user ---")
    result1 = validate_user("Ana", 25)
    print(f"Result: {result1}")

    # Example 2: Failed validation
    print("\n--- Example 2: Invalid user (negative age) ---")
    result2 = validate_user("Bob", -5)
    print(f"Result: {result2}")

    # Example 3: Processing numbers
    print("\n--- Example 3: Average of numbers ---")
    try:
        average = process_numbers([10, 20, 30, 40, 50])
        print(f"Average: {average}")
    except ValidationError as e:
        print(f"[ERROR] {e}")

    # Example 4: Empty list (will fail)
    print("\n--- Example 4: Empty list (expected error) ---")
    try:
        process_numbers([])
    except ValidationError as e:
        print(f"[ERROR] Error captured correctly: {e}")


if __name__ == "__main__":
    main()
