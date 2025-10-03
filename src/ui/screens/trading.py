"""Trading Dashboard Screen"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static
from textual.reactive import reactive
from datetime import datetime
import threading
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ui.widgets.price_chart import PriceChart
from ui.widgets.stats_panel import StatsPanel
from ui.widgets.threshold_tracker import ThresholdTracker
from ui.widgets.event_log import EventLog
from trail import StopTrail


class TradingScreen(Screen):
    """Main trading dashboard showing real-time price, charts, and stats."""

    CSS = """
    TradingScreen {
        layout: grid;
        grid-size: 2 3;
        grid-columns: 3fr 1fr;
        grid-rows: auto auto 1fr;
    }

    #header-info {
        column-span: 2;
        height: 3;
        background: $surface;
        border: heavy $primary;
        content-align: center middle;
    }

    #chart-container {
        row-span: 2;
        background: $surface;
        border: heavy $accent;
        padding: 1;
        height: 100%;
    }

    #stats-container {
        background: $surface;
        border: heavy $success;
        padding: 1;
    }

    #threshold-container {
        background: $surface;
        border: heavy $warning;
        padding: 1;
    }

    #log-container {
        column-span: 2;
        background: $surface;
        border: heavy $text-muted;
        padding: 1;
        height: 14;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]

    last_update_time = reactive(datetime.now())
    status_message = reactive("Initializing...")

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.bot: StopTrail = None
        self.bot_thread: threading.Thread = None
        self.running = False

    def compose(self) -> ComposeResult:
        """Create the trading dashboard widgets."""
        yield Header()

        # Header with symbol, type, mode info
        header_text = f"🔥 {self.config['symbol']}  |  {self.config['type'].upper()} MODE  |  "
        header_text += "DCA ACTIVE" if self.config['mode'] == 'dca' else "SIMPLE MODE"
        yield Static(header_text, id="header-info")

        # Price chart (left side, spans 2 rows)
        with Container(id="chart-container"):
            yield PriceChart()

        # Stats panel (right top)
        with Container(id="stats-container"):
            yield StatsPanel()

        # Threshold tracker (right middle) - only show if DCA mode
        if self.config['mode'] == 'dca':
            with Container(id="threshold-container"):
                yield ThresholdTracker()

        # Event log (bottom, spans 2 columns)
        with Container(id="log-container"):
            yield EventLog()

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the trading bot when screen mounts."""
        self.log_event("Initializing trading bot...")

        # Initialize stats panel
        stats_panel = self.query_one(StatsPanel)
        stats_panel.update_stats(
            mode=self.config['type'],
            symbol=self.config['symbol'],
            trailing_distance=f"${self.config['stop_value']:.4f} {self.config['stop_mode']}"
        )

        # Start the trading bot in a separate thread
        self.start_trading_bot()

    def start_trading_bot(self):
        """Start the trading bot with UI callbacks."""
        try:
            # Create bot instance with UI callback
            self.bot = StopTrail(
                market=self.config['symbol'],
                type=self.config['type'],
                stopsize=self.config['stop_value'],
                interval=self.config['interval'],
                split=self.config['split'],
                simple_mode=(self.config['mode'] == 'simple'),
                dca_config=self.config.get('dca_config'),
                stop_mode=self.config['stop_mode'],
                ui_callback=self.handle_bot_event
            )

            # If DCA mode, initialize threshold tracker
            if self.config['mode'] == 'dca' and not self.bot.simple_mode:
                self.initialize_threshold_tracker()

            # Start bot in background thread
            self.running = True
            self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
            self.bot_thread.start()

            self.log_event("Trading bot started successfully!", "success")

        except Exception as e:
            self.log_event(f"Failed to start bot: {str(e)}", "error")

    def run_bot(self):
        """Run the bot in background thread."""
        try:
            self.bot.run()
        except Exception as e:
            self.call_from_thread(self.log_event, f"Bot error: {str(e)}", "error")

    def initialize_threshold_tracker(self):
        """Initialize the threshold tracker with DCA thresholds."""
        try:
            tracker = self.query_one(ThresholdTracker)

            # Fetch thresholds from database
            cursor = self.bot.con.cursor()
            cursor.execute(
                "SELECT price, amount, threshold_hit FROM thresholds WHERE symbol = ? ORDER BY price",
                (self.bot.market,)
            )
            rows = cursor.fetchall()
            cursor.close()

            thresholds = [(row[2], row[3], row[4] == 'Y') for row in rows]
            tracker.set_thresholds(thresholds, self.config['symbol'])

        except Exception as e:
            self.log_event(f"Failed to load thresholds: {str(e)}", "error")

    def handle_bot_event(self, event_type: str, data: dict):
        """Handle events from the trading bot."""
        # Use call_from_thread to safely update UI from bot thread
        self.call_from_thread(self.process_bot_event, event_type, data)

    def process_bot_event(self, event_type: str, data: dict):
        """Process bot events (called on main thread)."""
        try:
            if event_type == "price_update":
                self.handle_price_update(data)
            elif event_type == "stop_update":
                self.handle_stop_update(data)
            elif event_type == "threshold_hit":
                self.handle_threshold_hit(data)
            elif event_type == "balance_update":
                self.handle_balance_update(data)
            elif event_type == "trade_executed":
                self.handle_trade_executed(data)
            elif event_type == "status_message":
                self.log_event(data.get('message', ''), data.get('level', 'info'))

            # Update last update time
            self.last_update_time = datetime.now()

        except Exception as e:
            self.log_event(f"Error processing event: {str(e)}", "error")

    def handle_price_update(self, data: dict):
        """Handle price update event."""
        price = data.get('price')
        stop_loss = data.get('stop_loss')

        # Update chart
        chart = self.query_one(PriceChart)
        chart.add_data_point(price, stop_loss)

        # Update stats
        stats = self.query_one(StatsPanel)
        stats.update_stats(
            price=price,
            stop_loss=stop_loss,
            stop_initialized=data.get('stop_initialized', False),
            balance=data.get('balance'),
            hopper=data.get('hopper')
        )

        # Update threshold tracker if DCA mode
        if self.config['mode'] == 'dca':
            try:
                tracker = self.query_one(ThresholdTracker)
                tracker.update_price(price)
            except:
                pass  # Tracker might not exist

    def handle_stop_update(self, data: dict):
        """Handle stop loss update event."""
        stop_loss = data.get('stop_loss')
        direction = data.get('direction', 'updated')

        event_log = self.query_one(EventLog)
        event_log.log_stop_update(stop_loss, direction)

        # Update stats
        stats = self.query_one(StatsPanel)
        stats.update_stats(stop_loss=stop_loss, stop_initialized=True)

    def handle_threshold_hit(self, data: dict):
        """Handle DCA threshold hit event."""
        threshold = data.get('threshold')
        amount = data.get('amount')

        event_log = self.query_one(EventLog)
        event_log.log_threshold_hit(threshold, amount, self.config['symbol'])

        # Update threshold tracker
        if self.config['mode'] == 'dca':
            try:
                tracker = self.query_one(ThresholdTracker)
                tracker.mark_threshold_hit(threshold)
            except:
                pass

    def handle_balance_update(self, data: dict):
        """Handle balance update event."""
        amount = data.get('amount')
        action = data.get('action', 'updated')

        event_log = self.query_one(EventLog)
        event_log.log_balance_update(amount, action)

        # Update stats
        stats = self.query_one(StatsPanel)
        stats.update_stats(balance=data.get('balance'), hopper=data.get('hopper'))

    def handle_trade_executed(self, data: dict):
        """Handle trade execution event."""
        trade_type = data.get('type')
        amount = data.get('amount')
        price = data.get('price')

        event_log = self.query_one(EventLog)
        event_log.log_trade_executed(trade_type, amount, price, self.config['symbol'])

    def log_event(self, message: str, level: str = "info"):
        """Log an event to the event log."""
        event_log = self.query_one(EventLog)
        event_log.log_event(message, level)

    def action_quit(self) -> None:
        """Quit the application."""
        if self.bot:
            self.running = False
            self.bot.running = False
        self.app.exit()

    def action_refresh(self) -> None:
        """Refresh the display."""
        self.refresh()
        self.log_event("Display refreshed", "info")
