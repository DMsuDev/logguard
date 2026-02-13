"""
Simple Banking System Demo - LogGuard Exceptions with Logger & Rich Formatting
"""

from rich import print as rprint
from rich.table import Table

from logguard import AppLogger
from logguard.exceptions import (
    AuthenticationError,
    ResourceNotFoundError,
    ValidationError,
)


class BankAccount:
    def __init__(self, account_id: str, owner: str, balance: float) -> None:
        self.account_id = account_id
        self.owner = owner
        self.balance = balance


class Bank:
    def __init__(self) -> None:
        self.logger = AppLogger.get_logger(__name__)
        self.accounts = {
            "ACC001": BankAccount("ACC001", "Alice", 1000.0),
            "ACC002": BankAccount("ACC002", "Bob", 500.0),
        }

    def get_account(self, account_id: str) -> BankAccount:
        """Get account or raise exception."""
        if account_id not in self.accounts:
            raise ResourceNotFoundError(
                resource_type="Account",
                identifier=account_id,
                available=len(self.accounts),
            )
        return self.accounts[account_id]

    def login(self, username: str, password: str) -> bool:
        """Login or raise exception."""
        if not username or not password:
            raise ValidationError(
                message="Username and password required",
                field="credentials",
            )
        if password != "secret123":
            raise AuthenticationError(
                message=f"Invalid password for {username}",
                username=username,
            )
        return True

    def transfer(self, from_id: str, to_id: str, amount: float) -> None:
        """Transfer money between accounts."""
        source = self.get_account(from_id)
        dest = self.get_account(to_id)

        if source.balance < amount:
            raise ValidationError(
                message="Insufficient funds",
                available=source.balance,
                requested=amount,
            )

        source.balance -= amount
        dest.balance += amount
        self.logger.info(f"Transferred ${amount} from {from_id} to {to_id}")


def show_rich_exception(exc: Exception) -> None:
    """Display exception in Rich format."""
    table = Table(title=f"[bold red]{exc.__class__.__name__}[/bold red]")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="yellow")

    if hasattr(exc, "message"):
        table.add_row("Message", str(exc.message))

    if hasattr(exc, "status_code"):
        table.add_row("Status", f"[bold]{exc.status_code}[/bold]")

    if hasattr(exc, "context"):
        for key, value in exc.context.items():
            table.add_row(key, str(value))

    rprint(table)


def main() -> None:
    """Run demo scenarios."""
    AppLogger.setup(log_file="logs/demo.log", console_level="INFO")
    logger = AppLogger.get_logger(__name__)
    bank = Bank()

    rprint("\n[bold cyan]LogGuard Exception Demo[/bold cyan]\n")

    # 1. Rich formatted validation error
    rprint("[bold]Scenario 1: Validation Error (with Rich formatter)[/bold]")
    try:
        bank.login("", "")
    except ValidationError as e:
        show_rich_exception(e)

    # 2. Logger captures exception
    rprint("[bold]Scenario 2: Authentication Error (with logger.exception)[/bold]")
    try:
        bank.login("alice", "wrongpass")
    except AuthenticationError:
        logger.exception("Invalid credentials")

    # 3. Rich formatted not found
    rprint("[bold]Scenario 3: Resource Not Found (with Rich formatter)[/bold]")
    try:
        bank.get_account("ACC999")
    except ResourceNotFoundError as e:
        show_rich_exception(e)

    # 4. Logger captures insufficient funds
    rprint("[bold]Scenario 4: Insufficient Funds (with logger.exception)[/bold]")
    try:
        bank.transfer("ACC002", "ACC001", 1000.0)
    except ValidationError:
        logger.exception("Transfer failed")

    # 5. Successful transfer
    rprint("[bold]Scenario 5: Successful Transfer[/bold]")
    try:
        bank.login("alice", "secret123")
        bank.transfer("ACC001", "ACC002", 250.0)
        rprint("[bold green]✅ Transfer completed successfully[/bold green]")
    except Exception:
        logger.exception("Transfer error")

    rprint("\n[dim]Check logs/demo.log for full details[/dim]\n")


if __name__ == "__main__":
    main()
