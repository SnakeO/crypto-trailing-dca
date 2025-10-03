"""Threshold Tracker Widget for DCA mode"""

from textual.widgets import Static, ProgressBar
from textual.containers import Vertical
from typing import List, Tuple, Optional


class ThresholdTracker(Vertical):
    """Tracks and displays DCA threshold progress."""

    def __init__(self):
        super().__init__(classes="thresholds-container")
        self.thresholds: List[Tuple[float, float, bool]] = []  # (price, amount, hit)
        self.current_price: float = 0
        self.symbol: str = ""

    def compose(self):
        """Create the threshold display."""
        yield Static("[bold yellow]DCA THRESHOLDS[/bold yellow]", id="threshold-title")
        yield Static("", id="threshold-content")

    def set_thresholds(self, thresholds: List[Tuple[float, float, bool]], symbol: str):
        """Set the threshold data."""
        self.thresholds = thresholds
        self.symbol = symbol
        self.render_thresholds()

    def update_price(self, price: float):
        """Update current price and re-render."""
        self.current_price = price
        self.render_thresholds()

    def mark_threshold_hit(self, threshold_price: float):
        """Mark a threshold as hit."""
        for i, (price, amount, hit) in enumerate(self.thresholds):
            if abs(price - threshold_price) < 0.01:  # Close enough
                self.thresholds[i] = (price, amount, True)
                break
        self.render_thresholds()

    def render_thresholds(self):
        """Render the threshold display with progress bars."""
        if not self.thresholds:
            content = "\n[dim]No thresholds configured[/dim]"
        else:
            base_currency = self.symbol.split("/")[0] if "/" in self.symbol else "COIN"
            content = "\n"

            for price, amount, hit in self.thresholds:
                # Calculate progress percentage
                if hit:
                    progress = 100
                    status = "✅"
                    bar = "█" * 12
                elif self.current_price >= price * 0.95:  # Within 5% of threshold
                    progress = int((self.current_price / price) * 100)
                    progress = min(progress, 99)  # Cap at 99% until actually hit
                    status = "🎯"
                    filled = int(progress / 100 * 12)
                    bar = "█" * filled + "░" * (12 - filled)
                else:
                    progress = 0
                    status = "⏸"
                    bar = "░" * 12

                content += f"{status} [bold]${price:.4f}[/bold]  {amount:.2f} {base_currency}  [{bar}] {progress}%\n"

        threshold_widget = self.query_one("#threshold-content")
        threshold_widget.update(content)
