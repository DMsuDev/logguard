"""
LogGuard Demo - Complete Feature Showcase

This script demonstrates all LogGuard capabilities:
- Logging with AppLogger
- Environment-aware assertions (CHECK, ASSERT, ENSURE, VERIFY)
- Specialized assertion helpers
- Custom exception handling

Run: python examples/demo.py
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from logguard import (
    ASSERT,
    ASSERT_BETWEEN_EXCLUSIVE,
    ASSERT_EQUALS,
    ASSERT_GREATER,
    ASSERT_IN,
    ASSERT_IN_RANGE,
    ASSERT_LESS,
    ASSERT_NOT_EMPTY,
    ASSERT_NOT_NULL,
    ASSERT_NULL,
    ASSERT_TYPE,
    CHECK,
    ENSURE,
    VERIFY,
    AppLogger,
    AssertFailure,
    AssertionConfig,
    AssertionManager,
    ComparisonError,
    ConfigurationError,
    EmptyError,
    EqualsError,
    LogGuardError,
    MembershipError,
    NullError,
    RangeError,
    ResourceNotFoundError,
    TypeErrorAssert,
    ValidationError,
)

# Rich console for beautiful output
console = Console()


def section(number: int, title: str, icon: str = "📦") -> None:
    """Print a styled section header."""
    console.print()
    console.print(
        Panel(
            f"[bold white]{title}[/]",
            title=f"[cyan]{icon} Section {number}[/]",
            border_style="blue",
            padding=(0, 2),
        )
    )
    console.print()


def success(message: str) -> None:
    """Print a success message."""
    console.print(f"  [green][+][/] {message}")


def failure(message: str, detail: str = "") -> None:
    """Print a failure message."""
    if detail:
        console.print(f"  [red][x][/] {message}")
        console.print(rf"    [dim]\- {detail}[/]")
    else:
        console.print(f"  [red][x][/] {message}")


def info(message: str) -> None:
    """Print an info message."""
    console.print(f"  [blue]i[/] {message}")


def warn(message: str) -> None:
    """Print a warning message."""
    console.print(f"  [yellow][!][/] {message}")


def code(text: str) -> str:
    """Format text as inline code."""
    return f"[cyan]{text}[/]"


# ========================================================================
# 1. LOGGING DEMO
# ========================================================================


def demo_logging() -> None:
    """Demonstrate AppLogger functionality."""
    section(1, "LOGGING DEMO", "[#]")

    # Setup logging (only needs to be done once)
    AppLogger.setup(
        log_file="logs/demo.log",
        console_level="DEBUG",
        file_level="DEBUG",
    )

    # Get a logger instance
    logger = AppLogger.get_logger(__name__)

    info("Demonstrating different log levels:")
    console.print()

    # Different log levels
    logger.debug("This is a DEBUG message - detailed diagnostic info")
    logger.info("This is an INFO message - general information")
    logger.warning("This is a WARNING message - something unexpected")
    logger.error("This is an ERROR message - something went wrong")

    console.print()

    # Logging with extra context
    info("Logging with extra context:")
    logger.info("User action completed", extra={"user_id": 123, "action": "login"})

    console.print()

    # Change log level dynamically
    warn("Changing console level to WARNING...")
    AppLogger.set_level("WARNING", handler_type="console")
    logger.info("This INFO won't show on console (but will be in file)")
    logger.warning("This WARNING will show")

    # Reset for next demos
    AppLogger.set_level("DEBUG", handler_type="console")
    info("Console level restored to DEBUG")


# ========================================================================
# 2. CORE ASSERTIONS DEMO
# ========================================================================


def demo_core_assertions() -> None:
    """Demonstrate CHECK, ASSERT, ENSURE, VERIFY behavior."""
    section(2, "CORE ASSERTIONS DEMO", "🛡️")

    # Ensure we're in development mode
    AssertionManager.reset()
    info("Environment: [bold green]development[/] (assertions enabled)")
    console.print()

    # Create a table to show assertion types
    table = Table(title="Assertion Types", show_header=True, header_style="bold magenta")
    table.add_column("Type", style="cyan", width=10)
    table.add_column("Dev Behavior", style="green")
    table.add_column("Prod Behavior", style="yellow")
    table.add_column("Use Case", style="dim")

    table.add_row("CHECK", "Raises", "Raises", "Critical invariants")
    table.add_row("ASSERT", "Raises", "Ignored", "Debug checks")
    table.add_row("ENSURE", "Raises", "Logs", "Preconditions")
    table.add_row("VERIFY", "Raises", "Logs", "Postconditions")

    console.print(table)
    console.print()

    # CHECK - Always raises (fatal)
    console.print("  [bold cyan]CHECK[/] - Testing critical invariant:")
    try:
        CHECK(True, "This passes - config is valid")
        success(f"{code('CHECK(True)')} -> Passed")

        CHECK(False, "Critical failure!", component="auth", user_id=123)
    except AssertFailure as e:
        failure(f"{code('CHECK(False)')} -> Raised {code('AssertFailure')}", e.message)
        console.print(f"    [dim]   Context: {e.context}[/]")

    console.print()

    # ASSERT - Raises in dev, ignored in prod
    console.print("  [bold cyan]ASSERT[/] - Debug-time validation:")
    try:
        value = -5
        ASSERT(value > 0, "Value must be positive", value=value)
    except AssertFailure as e:
        failure(f"{code('ASSERT(value > 0)')} where value=-5", e.message)

    console.print()

    # ENSURE - Precondition validation
    console.print("  [bold cyan]ENSURE[/] - Validating preconditions:")
    try:

        def process_order(order_id: int | None) -> None:
            ENSURE(order_id is not None, "Order ID required", order_id=order_id)
            if order_id is not None:
                ENSURE(order_id > 0, "Order ID must be positive", order_id=order_id)

        process_order(None)
    except AssertFailure as e:
        failure(f"{code('ENSURE(order_id is not None)')}", e.message)

    console.print()

    # VERIFY - Postcondition validation
    console.print("  [bold cyan]VERIFY[/] - Validating postconditions:")
    try:

        def calculate_discount(price: float) -> float:
            discount = price * 1.5  # Bug: should be * 0.1
            VERIFY(discount < price, "Discount cannot exceed price", discount=discount, price=price)
            return discount

        calculate_discount(100.0)
    except AssertFailure as e:
        failure(f"{code('VERIFY(discount < price)')}", e.message)


# ========================================================================
# 3. ENVIRONMENT SWITCHING DEMO
# ========================================================================


def demo_environment_switching() -> None:
    """Show how assertions behave differently by environment."""
    section(3, "ENVIRONMENT SWITCHING DEMO", "🔄")

    # Development mode
    AssertionManager.reset()
    console.print("  [bold green]● Development Mode[/]")
    try:
        ASSERT(False, "Dev assertion")
    except AssertFailure:
        failure(f"{code('ASSERT(False)')} -> Raised [dim](expected in dev)[/]")

    console.print()

    # Production mode
    AssertionManager.configure(AssertionConfig(environment="production"))
    console.print("  [bold yellow]● Production Mode[/]")
    ASSERT(False, "This is silently ignored in production")
    success(f"{code('ASSERT(False)')} -> Ignored [dim](no exception)[/]")

    console.print()

    # CHECK still raises in production
    console.print("  [bold red]● CHECK in Production[/]")
    try:
        CHECK(False, "Critical error")
    except AssertFailure:
        failure(f"{code('CHECK(False)')} -> Still raises! [dim](CHECK is always fatal)[/]")

    console.print()

    # Reset for other demos
    AssertionManager.reset()
    info("Reset to development mode")


# ========================================================================
# 4. SPECIALIZED ASSERTIONS DEMO
# ========================================================================


def demo_specialized_assertions() -> None:
    """Demonstrate all specialized assertion helpers."""
    section(4, "SPECIALIZED ASSERTIONS DEMO", "🔧")

    AssertionManager.reset()

    # Create a reference table
    table = Table(title="Specialized Assertion Helpers", show_header=True, header_style="bold magenta")
    table.add_column("Function", style="cyan", width=28)
    table.add_column("Exception", style="yellow", width=18)
    table.add_column("Purpose", style="dim")

    table.add_row("ASSERT_NOT_NULL", "NullError", "Value is not None")
    table.add_row("ASSERT_NULL", "NullError", "Value is None")
    table.add_row("ASSERT_EQUALS", "EqualsError", "a == b")
    table.add_row("ASSERT_GREATER", "ComparisonError", "a > b")
    table.add_row("ASSERT_LESS", "ComparisonError", "a < b")
    table.add_row("ASSERT_IN_RANGE", "RangeError", "min <= x <= max")
    table.add_row("ASSERT_BETWEEN_EXCLUSIVE", "RangeError", "min < x < max")
    table.add_row("ASSERT_TYPE", "TypeErrorAssert", "isinstance(x, type)")
    table.add_row("ASSERT_NOT_EMPTY", "EmptyError", "len(x) > 0")
    table.add_row("ASSERT_IN", "MembershipError", "x in container")

    console.print(table)
    console.print()

    # ASSERT_NOT_NULL / ASSERT_NULL
    console.print("  [bold]Null Checks[/]")
    try:
        user = None
        ASSERT_NOT_NULL(user, "User is required")
    except NullError as e:
        failure(f"{code('ASSERT_NOT_NULL(None)')} -> [yellow]NullError[/]", e.message)

    try:
        cache_entry = "cached_value"
        ASSERT_NULL(cache_entry, "Cache should be empty")
    except NullError as e:
        assert_null_call = 'ASSERT_NULL("value")'
        failure(f"{code(assert_null_call)} -> [yellow]NullError[/]", e.message)

    console.print()

    # ASSERT_EQUALS
    console.print("  [bold]Equality Check[/]")
    try:
        ASSERT_EQUALS(200, 404, "Expected success status")
    except EqualsError as e:
        failure(f"{code('ASSERT_EQUALS(200, 404)')} -> [yellow]EqualsError[/]", e.message)

    console.print()

    # ASSERT_GREATER / ASSERT_LESS
    console.print("  [bold]Comparison Checks[/]")
    try:
        balance = -50
        ASSERT_GREATER(balance, 0, "Balance must be positive")
    except ComparisonError as e:
        failure(f"{code('ASSERT_GREATER(-50, 0)')} -> [yellow]ComparisonError[/]", e.message)

    try:
        retries = 10
        ASSERT_LESS(retries, 5, "Too many retries")
    except ComparisonError as e:
        failure(f"{code('ASSERT_LESS(10, 5)')} -> [yellow]ComparisonError[/]", e.message)

    console.print()

    # ASSERT_IN_RANGE / ASSERT_BETWEEN_EXCLUSIVE
    console.print("  [bold]Range Checks[/]")
    try:
        percentage = 150
        ASSERT_IN_RANGE(percentage, 0, 100, "Invalid percentage")
    except RangeError as e:
        failure(f"{code('ASSERT_IN_RANGE(150, 0, 100)')} -> [yellow]RangeError[/]", e.message)

    try:
        ratio = 1.0  # Exactly on boundary (exclusive fails)
        ASSERT_BETWEEN_EXCLUSIVE(ratio, 0.0, 1.0, "Ratio must be between 0 and 1")
    except RangeError as e:
        failure(f"{code('ASSERT_BETWEEN_EXCLUSIVE(1.0, 0, 1)')} -> [yellow]RangeError[/]", e.message)

    console.print()

    # ASSERT_TYPE
    console.print("  [bold]Type Check[/]")
    try:
        config = "not a dict"
        ASSERT_TYPE(config, dict, "Config must be a dictionary")
    except TypeErrorAssert as e:
        assert_type_call = 'ASSERT_TYPE("str", dict)'
        failure(f"{code(assert_type_call)} -> [yellow]TypeErrorAssert[/]", e.message)

    console.print()

    # ASSERT_NOT_EMPTY
    console.print("  [bold]Empty Check[/]")
    try:
        items: list[str] = []
        ASSERT_NOT_EMPTY(items, "Items list cannot be empty")
    except EmptyError as e:
        failure(f"{code('ASSERT_NOT_EMPTY([])')} -> [yellow]EmptyError[/]", e.message)

    console.print()

    # ASSERT_IN
    console.print("  [bold]Membership Check[/]")
    try:
        status = "unknown"
        ASSERT_IN(status, ["pending", "active", "completed"], "Invalid status")
    except MembershipError as e:
        assert_in_call = 'ASSERT_IN("unknown", [...])'
        failure(f"{code(assert_in_call)} -> [yellow]MembershipError[/]", e.message)


# ========================================================================
# 5. EXCEPTION HANDLING DEMO
# ========================================================================


def demo_exceptions() -> None:
    """Demonstrate the exception hierarchy and serialization."""
    section(5, "EXCEPTION HIERARCHY DEMO", "[#]")

    # Show exception hierarchy as tree
    tree = Tree("[bold]LogGuardError[/] [dim](base)[/]")
    config_branch = tree.add("[yellow]ConfigurationError[/]")
    config_branch.add("[dim]MissingConfigError[/]")

    validation_branch = tree.add("[yellow]ValidationError[/]")
    assert_branch = validation_branch.add("[cyan]AssertFailure[/]")
    assert_branch.add("[dim]NullError[/]")
    assert_branch.add("[dim]RangeError[/]")
    assert_branch.add("[dim]TypeErrorAssert[/]")
    assert_branch.add("[dim]EmptyError[/]")
    assert_branch.add("[dim]EqualsError[/]")
    assert_branch.add("[dim]ComparisonError[/]")
    assert_branch.add("[dim]MembershipError[/]")

    resource_branch = tree.add("[yellow]ResourceError[/]")
    resource_branch.add("[dim]ResourceNotFoundError[/]")
    resource_branch.add("[dim]ForbiddenError[/]")

    console.print(tree)
    console.print()

    # ValidationError with context
    console.print("  [bold]ValidationError with rich context:[/]")
    try:
        raise ValidationError(
            "Invalid email format",
            context={"field": "email", "value": "bad@", "pattern": r"^[\w\.-]+@[\w\.-]+$"},
        )
    except ValidationError as e:
        console.print(f"    [dim]Message:[/]  {e.message}")
        console.print(f"    [dim]Context:[/]  {e.context}")
        console.print(f"    [dim]to_dict():[/] {e.to_dict()}")

    console.print()

    # ConfigurationError
    console.print("  [bold]ConfigurationError:[/]")
    try:
        raise ConfigurationError("Invalid configuration", context={"file": "config.yaml", "line": 42})
    except ConfigurationError as e:
        console.print(f"    {e}")

    console.print()

    # ResourceNotFoundError
    console.print("  [bold]ResourceNotFoundError:[/]")
    try:
        raise ResourceNotFoundError("User", identifier=12345)
    except ResourceNotFoundError as e:
        console.print(f"    {e}")

    console.print()

    # Catching base class
    console.print("  [bold]Catching all with LogGuardError (polymorphism):[/]")
    errors = [
        ValidationError("Validation failed"),
        ConfigurationError("Config error"),
        AssertFailure("Assertion failed"),
    ]
    for err in errors:
        if isinstance(err, LogGuardError):
            console.print(f"    [green][+][/] Caught [cyan]{type(err).__name__}[/]: {err.message}")


# ========================================================================
# 6. CUSTOM FAILURE STRATEGY DEMO
# ========================================================================


def demo_custom_strategy() -> None:
    """Show how to customize assertion failure handling."""
    section(6, "CUSTOM FAILURE STRATEGY", "⚙️")

    AssertionManager.reset()

    failure_log: list[dict] = []

    def custom_raise_handler(
        message: str,
        context: dict,
        exception_class: type[AssertFailure],
    ) -> None:
        """Custom handler that logs before raising."""
        failure_log.append({"message": message, "context": context, "type": exception_class.__name__})
        console.print(f"    [magenta]-> CUSTOM HANDLER[/] Logged: [italic]{message}[/]")
        raise exception_class(message, context=context)

    # Set custom strategy
    AssertionManager.set_failure_strategy(raise_strategy=custom_raise_handler)

    info("Using custom failure handler that logs before raising:")
    console.print()
    try:
        ASSERT_IN_RANGE(999, 0, 100, "Value out of bounds")
    except RangeError:
        console.print()
        console.print(f"  [dim]Failure log:[/] {failure_log}")

    console.print()

    # Reset to default
    AssertionManager.reset()
    info("Reset to default strategy")


# ========================================================================
# 7. REAL-WORLD USAGE EXAMPLE
# ========================================================================


def demo_real_world() -> None:
    """Simulate a real-world use case with logging and assertions."""
    section(7, "REAL-WORLD USAGE EXAMPLE", "🚀")

    logger = AppLogger.get_logger("user_service")
    AssertionManager.reset()

    class User:
        def __init__(self, user_id: int, name: str, email: str, age: int) -> None:
            # Validate on construction
            CHECK(user_id > 0, "User ID must be positive", user_id=user_id)
            ASSERT_NOT_NULL(name, "Name is required")
            ASSERT_NOT_EMPTY(name.strip(), "Name cannot be blank")
            ASSERT_TYPE(email, str, "Email must be a string")
            ASSERT_IN_RANGE(age, 0, 150, "Invalid age")

            self.user_id = user_id
            self.name = name
            self.email = email
            self.age = age

        def __repr__(self) -> str:
            return f"User(id={self.user_id}, name={self.name!r})"

    def create_user(data: dict) -> User | None:
        """Create a user with validation."""
        logger.info("Creating user", extra={"data": data})

        try:
            ASSERT_TYPE(data, dict, "Input must be a dictionary")
            ASSERT_IN("user_id", data, "Missing user_id")
            ASSERT_IN("name", data, "Missing name")
            ASSERT_IN("email", data, "Missing email")
            ASSERT_IN("age", data, "Missing age")

            user = User(
                user_id=data["user_id"],
                name=data["name"],
                email=data["email"],
                age=data["age"],
            )

            logger.info("User created successfully", extra={"user": str(user)})
            return user

        except AssertFailure as e:
            logger.error("User creation failed", extra={"error": e.message, "context": e.context})
            return None

    # Test cases with visual output
    console.print("  [bold]Test Case 1:[/] Valid user data")
    user = create_user({"user_id": 1, "name": "Alice", "email": "alice@example.com", "age": 30})
    if user:
        success(f"Created: {user}")
    else:
        failure("Creation failed")

    console.print()

    console.print("  [bold]Test Case 2:[/] Missing required field")
    user = create_user({"user_id": 2, "name": "Bob"})
    if user:
        success(f"Created: {user}")
    else:
        failure("Creation failed [dim](missing email and age)[/]")

    console.print()

    console.print("  [bold]Test Case 3:[/] Invalid age value")
    user = create_user({"user_id": 3, "name": "Charlie", "email": "c@test.com", "age": 200})
    if user:
        success(f"Created: {user}")
    else:
        failure("Creation failed [dim](age=200 out of range 0-150)[/]")


# ========================================================================
# MAIN
# ========================================================================


def main() -> None:
    """Run all demos."""
    console.print()
    console.print(
        Panel(
            "[bold white]Complete Feature Showcase[/]\n[dim]Logging - Assertions - Exceptions - Custom Strategies[/]",
            title="[bold cyan]🛡️ LOGGUARD DEMO[/]",
            border_style="cyan",
            padding=(1, 4),
        )
    )

    demo_logging()
    demo_core_assertions()
    demo_environment_switching()
    demo_specialized_assertions()
    demo_exceptions()
    demo_custom_strategy()
    demo_real_world()

    console.print()
    console.print(
        Panel(
            "[bold green]All features demonstrated successfully![/]\n"
            "[dim]Check [cyan]logs/demo.log[/cyan] for file output[/]",
            title="[bold green]✅ DEMO COMPLETE[/]",
            border_style="green",
            padding=(1, 4),
        )
    )
    console.print()


if __name__ == "__main__":
    main()
