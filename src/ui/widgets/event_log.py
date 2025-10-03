"""Event Log Widget for displaying trading events"""

from textual.widgets import RichLog
from datetime import datetime
from collections import deque


class EventLog(RichLog):
    """Scrolling log of trading events with color coding."""

    def __init__(self, max_lines: int = 100):
        super().__init__(
            highlight=True,
            markup=True,
            max_lines=max_lines,
            wrap=True,
        )
        self.auto_scroll = True

    def log_event(self, message: str, level: str = "info"):
        """Log an event with timestamp and color coding.

        Args:
            message: The message to log
            level: Log level (info, success, warning, error)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color code based on level
        if level == "success":
            prefix = "[bold green]✓[/bold green]"
            color = "green"
        elif level == "warning":
            prefix = "[bold yellow]⚠[/bold yellow]"
            color = "yellow"
        elif level == "error":
            prefix = "[bold red]✗[/bold red]"
            color = "red"
        elif level == "trade":
            prefix = "[bold cyan]💰[/bold cyan]"
            color = "cyan"
        else:  # info
            prefix = "[bold blue]ℹ[/bold blue]"
            color = "white"

        formatted_message = f"[dim]{timestamp}[/dim] {prefix} [{color}]{message}[/{color}]"
        self.write(formatted_message)

    def log_price_update(self, price: float):
        """Log a price update."""
        self.log_event(f"Price: ${price:.4f}", "info")

    def log_stop_update(self, stop_loss: float, direction: str = "raised"):
        """Log a stop loss update."""
        self.log_event(f"{direction.capitalize()} stop loss to ${stop_loss:.4f}", "success")

    def log_threshold_hit(self, threshold: float, amount: float, symbol: str):
        """Log a threshold being hit."""
        base = symbol.split("/")[0] if "/" in symbol else "COIN"
        self.log_event(
            f"Hit threshold at ${threshold:.4f}! Added {amount:.4f} {base} to hopper",
            "warning"
        )

    def log_trade_executed(self, trade_type: str, amount: float, price: float, symbol: str):
        """Log a trade execution."""
        base = symbol.split("/")[0] if "/" in symbol else "COIN"
        self.log_event(
            f"{trade_type.upper()} executed: {amount:.4f} {base} at ${price:.4f}",
            "trade"
        )

    def log_balance_update(self, amount: float, action: str):
        """Log a balance update."""
        self.log_event(f"Balance {action}: ${amount:.2f}", "info")

    def log_new_high(self, price: float):
        """Log a new high price."""
        self.log_event(f"New high observed: ${price:.4f}", "success")

    def log_new_low(self, price: float):
        """Log a new low price."""
        self.log_event(f"New low observed: ${price:.4f}", "warning")

    def log_error(self, error_message: str):
        """Log an error."""
        self.log_event(error_message, "error")

    def log_status(self, message: str):
        """Log a general status message."""
        self.log_event(message, "info")
