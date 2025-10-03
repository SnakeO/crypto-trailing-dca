"""Price Chart Widget using Plotext"""

from textual.widgets import Static
from textual_plotext import PlotextPlot
from collections import deque
from typing import Optional, List, Tuple
from datetime import datetime


class PriceChart(PlotextPlot):
    """Interactive price chart showing price history and stop loss."""

    def __init__(self, max_points: int = 100):
        super().__init__()
        self.max_points = max_points
        self.price_history: deque = deque(maxlen=max_points)
        self.stop_history: deque = deque(maxlen=max_points)
        self.timestamps: deque = deque(maxlen=max_points)

    def add_data_point(self, price: float, stop_loss: Optional[float] = None, timestamp: Optional[datetime] = None):
        """Add a new data point to the chart."""
        self.price_history.append(price)
        self.stop_history.append(stop_loss if stop_loss is not None else price * 0.95)  # Default fallback
        self.timestamps.append(timestamp or datetime.now())
        self.update_chart()

    def update_chart(self):
        """Refresh the chart with current data."""
        if len(self.price_history) == 0:
            return

        plt = self.plt
        plt.clear_data()
        plt.clear_figure()

        # Create x-axis (simple indices for now)
        x_vals = list(range(len(self.price_history)))

        # Plot price line
        plt.plot(
            x_vals,
            list(self.price_history),
            label="Price",
            color="green",
            marker="dot"
        )

        # Plot stop loss line
        valid_stops = [s for s in self.stop_history if s is not None]
        if valid_stops:
            plt.plot(
                x_vals,
                list(self.stop_history),
                label="Stop Loss",
                color="red",
                marker="dot"
            )

        # Styling
        plt.title("Price Movement")
        plt.xlabel("Time")
        plt.ylabel("Price ($)")

        # Set y-axis limits with some padding
        if self.price_history:
            min_val = min(min(self.price_history), min(self.stop_history))
            max_val = max(max(self.price_history), max(self.stop_history))
            padding = (max_val - min_val) * 0.1
            plt.ylim(min_val - padding, max_val + padding)

        # Grid
        plt.grid(True, True)

        self.refresh()

    def clear_chart(self):
        """Clear all data from the chart."""
        self.price_history.clear()
        self.stop_history.clear()
        self.timestamps.clear()
        if hasattr(self, 'plt'):
            self.plt.clear_data()
            self.plt.clear_figure()
            self.refresh()


class StaticPriceChart(Static):
    """Fallback static price chart using ASCII art if plotext unavailable."""

    def __init__(self):
        super().__init__()
        self.price_history: deque = deque(maxlen=50)

    def add_data_point(self, price: float, stop_loss: Optional[float] = None, timestamp: Optional[datetime] = None):
        """Add a new price point."""
        self.price_history.append(price)
        self.render_ascii_chart()

    def render_ascii_chart(self):
        """Render a simple ASCII sparkline."""
        if len(self.price_history) < 2:
            self.update("Collecting data...")
            return

        # Simple ASCII sparkline
        min_price = min(self.price_history)
        max_price = max(self.price_history)
        price_range = max_price - min_price if max_price > min_price else 1

        sparkline = ""
        bars = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']

        for price in self.price_history:
            normalized = (price - min_price) / price_range
            index = int(normalized * (len(bars) - 1))
            sparkline += bars[index]

        chart_text = f"""
Price Chart
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{sparkline}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
High: ${max_price:.4f}  Low: ${min_price:.4f}
Last 50 price points
        """
        self.update(chart_text)
