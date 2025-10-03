"""Main Textual Application for Crypto Trading Bot"""

from textual.app import App
from textual.binding import Binding
from ui.screens.setup import SetupScreen
from ui.screens.trading import TradingScreen
import os


class CryptoTradingApp(App):
    """Crypto Trailing DCA Trading Bot - Textual UI."""

    CSS_PATH = os.path.join(os.path.dirname(__file__), "theme.tcss")

    TITLE = "Crypto Trailing DCA Bot"
    SUB_TITLE = "Real-time Trading Dashboard"

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True, priority=True),
        Binding("d", "toggle_dark", "Toggle Dark Mode", show=False),
    ]

    def on_mount(self) -> None:
        """Initialize the app with the setup screen."""
        self.push_screen(SetupScreen())

    def switch_to_trading(self, config: dict) -> None:
        """Switch to the trading screen with given configuration.

        Args:
            config: Configuration dictionary from setup screen
        """
        # Pop setup screen and push trading screen
        self.pop_screen()
        self.push_screen(TradingScreen(config))

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark


def run_ui():
    """Run the Textual UI application."""
    app = CryptoTradingApp()
    app.run()


if __name__ == "__main__":
    run_ui()
