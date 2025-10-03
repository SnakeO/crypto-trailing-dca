"""Stats Panel Widget for displaying trading statistics"""

from textual.widgets import Static
from textual.containers import Vertical
from typing import Optional


class StatsPanel(Vertical):
    """Panel displaying current trading statistics."""

    def __init__(self):
        super().__init__(classes="stats-container")
        self.current_price: Optional[float] = None
        self.stop_loss: Optional[float] = None
        self.stop_initialized: bool = False
        self.balance: Optional[float] = None
        self.hopper: Optional[float] = None
        self.trailing_distance: str = ""
        self.mode: str = "sell"
        self.symbol: str = ""
        self.win_rate: Optional[str] = None

    def compose(self):
        """Create the stats display."""
        yield Static("", id="stats-content")

    def update_stats(
        self,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        stop_initialized: Optional[bool] = None,
        balance: Optional[float] = None,
        hopper: Optional[float] = None,
        trailing_distance: Optional[str] = None,
        mode: Optional[str] = None,
        symbol: Optional[str] = None,
        win_rate: Optional[str] = None,
    ):
        """Update the displayed statistics."""
        if price is not None:
            self.current_price = price
        if stop_loss is not None:
            self.stop_loss = stop_loss
        if stop_initialized is not None:
            self.stop_initialized = stop_initialized
        if balance is not None:
            self.balance = balance
        if hopper is not None:
            self.hopper = hopper
        if trailing_distance is not None:
            self.trailing_distance = trailing_distance
        if mode is not None:
            self.mode = mode
        if symbol is not None:
            self.symbol = symbol
        if win_rate is not None:
            self.win_rate = win_rate

        self.render_stats()

    def render_stats(self):
        """Render the stats display."""
        base_currency = self.symbol.split("/")[0] if "/" in self.symbol else "COIN"
        quote_currency = self.symbol.split("/")[1] if "/" in self.symbol else "USD"

        # Determine stop loss status indicator
        if self.stop_initialized and self.stop_loss is not None and self.current_price is not None:
            distance_pct = abs(self.current_price - self.stop_loss) / self.current_price * 100
            if distance_pct < 2:
                status_indicator = "🔴"  # Close to trigger
            elif distance_pct < 5:
                status_indicator = "🟡"  # Getting close
            else:
                status_indicator = "🟢"  # Safe
        else:
            status_indicator = "⏸"  # Not initialized

        content = f"""[bold cyan]STATS[/bold cyan]
━━━━━━━━━━━━━━━━━━━

[bold]Current Price[/bold]
[bold green]${self.current_price:.4f if self.current_price else 0}[/bold green]

[bold]Stop Loss[/bold]
${self.stop_loss:.4f if self.stop_loss else 0}  {status_indicator}

[bold]Trailing Distance[/bold]
{self.trailing_distance}
"""

        if self.mode == "sell":
            content += f"""
[bold]Balance[/bold]
{self.balance:.4f if self.balance else 0} {base_currency}

[bold]Hopper (Ready)[/bold]
{self.hopper:.4f if self.hopper else 0} {base_currency}
"""
        else:  # buy mode
            content += f"""
[bold]Balance[/bold]
${self.balance:.2f if self.balance else 0}

[bold]Available[/bold]
${self.hopper:.2f if self.hopper else 0}
"""

        if self.win_rate:
            content += f"""
[bold]Win Rate[/bold]
{self.win_rate}
"""

        content += "\n━━━━━━━━━━━━━━━━━━━"

        stats_widget = self.query_one("#stats-content")
        stats_widget.update(content)
