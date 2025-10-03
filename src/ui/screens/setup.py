"""Setup/Configuration Screen for Crypto Trading Bot"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Static, Input, Select, RadioSet, RadioButton, Label
from textual.validation import Function, Number
from typing import Optional
import sys
import os

# Add parent directory to path to import helper modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from helper import Config
from coinbasepro import CoinbasePro


class SetupScreen(Screen):
    """Interactive setup screen for configuring the trading bot."""

    CSS = """
    SetupScreen {
        align: center middle;
    }

    #setup-container {
        width: 80;
        height: auto;
        background: $surface;
        border: heavy $primary;
        padding: 2;
    }

    #title {
        text-align: center;
        color: $primary;
        text-style: bold;
        margin: 0 0 2 0;
    }

    .setup-section {
        margin: 1 0;
        padding: 1;
        background: $background;
        border: round $accent;
    }

    .section-label {
        color: $accent;
        text-style: bold;
        margin: 0 0 1 0;
    }

    #button-row {
        margin-top: 2;
        align: center middle;
    }

    Input {
        margin: 1 0;
    }

    RadioSet {
        padding: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.trade_type = "sell"
        self.mode = "dca"
        self.dca_type = "default"
        self.stop_mode = "absolute"
        self.sellable_assets = []

    def compose(self) -> ComposeResult:
        """Create the setup form widgets."""
        yield Header()

        with Container(id="setup-container"):
            yield Static("🚀 Crypto Trailing DCA Bot - Configuration", id="title")

            # Trade Type Section
            with Vertical(classes="setup-section"):
                yield Label("Trade Type", classes="section-label")
                with RadioSet(id="trade-type-radio"):
                    yield RadioButton("Buy - Wait for dips, execute buy when price crosses stop", value=False)
                    yield RadioButton("Sell - Wait for peaks, execute sell when price crosses stop", value=True)

            # Symbol Section
            with Vertical(classes="setup-section"):
                yield Label("Trading Symbol", classes="section-label")
                yield Input(
                    placeholder="e.g., BTC/USD, ETH/USD, DOGE/USD",
                    id="symbol-input"
                )

            # Mode Section
            with Vertical(classes="setup-section"):
                yield Label("Trading Mode", classes="section-label")
                with RadioSet(id="mode-radio"):
                    yield RadioButton("Simple - Use full balance with trailing stop (no threshold ladder)", value=False)
                    yield RadioButton("DCA - Use threshold ladder for partial exits at different prices", value=True)

            # DCA Configuration (shown when DCA mode selected)
            with Vertical(classes="setup-section", id="dca-section"):
                yield Label("DCA Configuration", classes="section-label")
                with RadioSet(id="dca-type-radio"):
                    yield RadioButton("Default - Auto 4-tier ladder (+10%/+20%/+30%/+50%, 25% each)", value=True)
                    yield RadioButton("Custom - Define your own price thresholds", value=False)
                yield Input(
                    placeholder="e.g., '+10%:100,+20%:150,+30%:200' or '0.30:100,0.40:150'",
                    id="dca-custom-input",
                    disabled=True
                )

            # Stop Loss Configuration
            with Vertical(classes="setup-section"):
                yield Label("Trailing Stop Distance", classes="section-label")
                with RadioSet(id="stop-mode-radio"):
                    yield RadioButton("Percentage - Distance as % of price (e.g., 5%)", value=False)
                    yield RadioButton("Absolute - Distance in dollar amount (e.g., $0.01 or $100)", value=True)
                yield Input(
                    placeholder="e.g., 0.05 for 5% or 0.01 for $0.01",
                    id="stop-value-input",
                    validators=[Number(minimum=0.0)]
                )

            # Buttons
            with Horizontal(id="button-row"):
                yield Button("Cancel", variant="default", id="cancel-btn")
                yield Button("Start Trading →", variant="primary", id="start-btn")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the setup screen."""
        # Set default selections
        self.query_one("#trade-type-radio").query_one("RadioButton:nth-child(2)").value = True  # Sell
        self.query_one("#mode-radio").query_one("RadioButton:nth-child(2)").value = True  # DCA
        self.query_one("#dca-type-radio").query_one("RadioButton:nth-child(1)").value = True  # Default
        self.query_one("#stop-mode-radio").query_one("RadioButton:nth-child(2)").value = True  # Absolute

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle radio button changes."""
        if event.radio_set.id == "trade-type-radio":
            self.trade_type = "sell" if event.index == 1 else "buy"
        elif event.radio_set.id == "mode-radio":
            self.mode = "dca" if event.index == 1 else "simple"
            # Show/hide DCA section
            dca_section = self.query_one("#dca-section")
            dca_section.display = self.mode == "dca"
        elif event.radio_set.id == "dca-type-radio":
            self.dca_type = "default" if event.index == 0 else "custom"
            # Enable/disable custom input
            custom_input = self.query_one("#dca-custom-input")
            custom_input.disabled = self.dca_type == "default"
        elif event.radio_set.id == "stop-mode-radio":
            self.stop_mode = "percentage" if event.index == 0 else "absolute"
            # Update placeholder
            stop_input = self.query_one("#stop-value-input")
            if self.stop_mode == "percentage":
                stop_input.placeholder = "e.g., 0.05 for 5%, 0.10 for 10%"
            else:
                stop_input.placeholder = "e.g., 0.01 for $0.01, 100 for $100"

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "cancel-btn":
            self.app.exit()
        elif event.button.id == "start-btn":
            self.validate_and_start()

    def validate_and_start(self) -> None:
        """Validate inputs and start trading."""
        # Get values
        symbol = self.query_one("#symbol-input").value.strip().upper()
        stop_value_str = self.query_one("#stop-value-input").value.strip()

        # Validate symbol
        if not symbol:
            self.app.bell()
            self.notify("Please enter a trading symbol", severity="error", timeout=3)
            return

        if '/' not in symbol:
            self.app.bell()
            self.notify("Symbol should be in format ASSET/USD (e.g., BTC/USD)", severity="error", timeout=3)
            return

        # Validate stop value
        if not stop_value_str:
            self.app.bell()
            self.notify("Please enter a stop loss distance value", severity="error", timeout=3)
            return

        try:
            stop_value = float(stop_value_str)
            if stop_value <= 0:
                raise ValueError("Must be positive")
        except ValueError:
            self.app.bell()
            self.notify("Stop loss value must be a positive number", severity="error", timeout=3)
            return

        # Validate custom DCA if needed
        dca_config = None
        if self.mode == "dca":
            if self.dca_type == "default":
                dca_config = "DEFAULT"
            else:
                dca_custom = self.query_one("#dca-custom-input").value.strip()
                if not dca_custom:
                    self.app.bell()
                    self.notify("Please enter custom DCA thresholds", severity="error", timeout=3)
                    return
                # Basic validation
                if ':' not in dca_custom:
                    self.app.bell()
                    self.notify("DCA format should be 'PRICE:AMOUNT,PRICE:AMOUNT'", severity="error", timeout=3)
                    return
                dca_config = dca_custom

        # Build configuration
        config = {
            'symbol': symbol,
            'type': self.trade_type,
            'mode': self.mode,
            'dca_config': dca_config,
            'stop_mode': self.stop_mode,
            'stop_value': stop_value,
            'interval': 5.0,  # Default 5 seconds
            'split': 1,  # Default single coin
        }

        # Switch to trading screen
        self.app.switch_to_trading(config)
