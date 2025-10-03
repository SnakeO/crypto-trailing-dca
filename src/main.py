from trail import StopTrail
from coinbasepro import CoinbasePro
from helper import Config
import argparse
import sys
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

def parse_dca_config(dca_string, current_price):
    """
    Parse comma-delimited DCA threshold configuration.

    Format: 'PRICE:AMOUNT,PRICE:AMOUNT,...'
    Supports:
      - Absolute prices: '0.30:100'
      - Percentages: '+10%:100' (relative to current_price)

    Returns: List of (price, amount) tuples, sorted by price
    """
    if not dca_string:
        return None

    thresholds = []
    pairs = dca_string.split(',')

    for i, pair in enumerate(pairs):
        pair = pair.strip()
        if not pair:
            continue

        try:
            price_str, amount_str = pair.split(':')
            price_str = price_str.strip()
            amount_str = amount_str.strip()

            # Parse amount
            amount = float(amount_str)
            if amount <= 0:
                print(f"Error: Amount must be positive in threshold #{i+1}: '{pair}'")
                sys.exit(1)

            # Parse price (absolute or percentage)
            if price_str.startswith('+') and '%' in price_str:
                # Percentage format: +10%
                percent_str = price_str.replace('+', '').replace('%', '').strip()
                percent = float(percent_str)
                price = current_price * (1 + percent / 100)
            else:
                # Absolute price
                price = float(price_str)
                if price <= 0:
                    print(f"Error: Price must be positive in threshold #{i+1}: '{pair}'")
                    sys.exit(1)

            thresholds.append((price, amount))

        except ValueError as e:
            print(f"Error: Invalid DCA format in threshold #{i+1}: '{pair}'")
            print(f"Expected format: 'PRICE:AMOUNT' or '+PERCENT%:AMOUNT'")
            print(f"Example: --DCA '0.30:100,0.40:150' or --DCA '+10%:100,+20%:150'")
            sys.exit(1)

    # Sort by price ascending
    thresholds.sort(key=lambda x: x[0])

    return thresholds


def generate_default_dca(current_price, balance):
    """
    Generate sane default 4-tier DCA strategy.

    Thresholds: +10%, +20%, +30%, +50% from current price
    Amounts: 25% of balance each

    Returns: List of (price, amount) tuples
    """
    portion = balance / 4
    return [
        (current_price * 1.10, portion),  # +10%
        (current_price * 1.20, portion),  # +20%
        (current_price * 1.30, portion),  # +30%
        (current_price * 1.50, portion),  # +50%
    ]


def get_sellable_assets():
    """
    Get list of assets with non-zero balance that can be sold.

    Returns:
        List of (symbol, balance, currency) tuples for assets with balance > 0
        Excludes USD and other quote currencies
    """
    try:
        # Create temporary Coinbase client to fetch balances
        coinbase = CoinbasePro(
            api_key=Config.get_value('api','api_key_name'),
            api_secret=Config.get_value('api','api_private_key')
        )

        accounts_response = coinbase.client.get_accounts()

        # Convert to dict
        if hasattr(accounts_response, '__dict__'):
            accounts_dict = accounts_response.__dict__
        else:
            accounts_dict = dict(accounts_response)

        sellable = []
        quote_currencies = {'USD', 'USDT', 'USDC', 'EUR', 'GBP'}  # Don't show these as sellable

        for account in accounts_dict.get('accounts', []):
            account_dict = account.__dict__ if hasattr(account, '__dict__') else dict(account)
            currency = account_dict.get('currency')

            # Skip quote currencies
            if currency in quote_currencies:
                continue

            available_balance = account_dict.get('available_balance', {})
            balance_dict = available_balance.__dict__ if hasattr(available_balance, '__dict__') else dict(available_balance)
            balance_value = float(balance_dict.get('value', 0))

            # Only include assets with balance > 0
            if balance_value > 0:
                sellable.append((currency, balance_value, currency))

        return sellable
    except Exception as e:
        print(f"Error fetching sellable assets: {e}")
        return []


def prompt_symbol(trade_type):
    """
    Interactive prompt for trading symbol selection.

    Buy mode: Simple text input
    Sell mode: List of sellable assets + autocomplete

    Args:
        trade_type: 'buy' or 'sell'

    Returns:
        Trading symbol in format 'ASSET/USD' (e.g., 'BTC/USD', 'DOGE/USD')
    """
    print("\n" + "=" * 60)

    if trade_type == 'buy':
        print("TRADING SYMBOL")
        print("=" * 60)
        print("Enter trading pair for buying")
        print("  Examples: BTC/USD, ETH/USD, DOGE/USD, SOL/USD")
        print()

        while True:
            symbol = input("Symbol: ").strip().upper()
            if not symbol:
                print("Error: Symbol cannot be empty.")
                continue

            # Basic validation - should contain /
            if '/' not in symbol:
                print("Error: Symbol should be in format ASSET/USD (e.g., BTC/USD)")
                continue

            return symbol

    else:  # sell mode
        print("SELECT ASSET TO SELL")
        print("=" * 60)

        sellable = get_sellable_assets()

        if not sellable:
            print("Error: No sellable assets found with balance > 0")
            print("Please ensure you have cryptocurrency in your account to sell.")
            sys.exit(1)

        print("Available assets:")
        for i, (currency, balance, _) in enumerate(sellable, 1):
            print(f"  {i}. {currency:8} {balance:,.4f} {currency}")
        print()

        # Create autocomplete with asset names
        asset_names = [curr for curr, _, _ in sellable]

        print("Enter number or start typing symbol name")

        while True:
            # Try to use autocomplete if terminal is available, otherwise use basic input
            try:
                if sys.stdin.isatty():
                    completer = WordCompleter(asset_names, ignore_case=True)
                    user_input = prompt("Choice: ", completer=completer).strip()
                else:
                    user_input = input("Choice: ").strip()
            except:
                # Fallback to basic input
                user_input = input("Choice: ").strip()

            # Check if it's a number (list selection)
            if user_input.isdigit():
                idx = int(user_input) - 1
                if 0 <= idx < len(sellable):
                    currency = sellable[idx][0]
                    return f"{currency}/USD"
                else:
                    print(f"Error: Invalid number. Please enter 1-{len(sellable)}")
                    continue

            # Check if it's a currency name
            user_input_upper = user_input.upper()
            if user_input_upper in asset_names:
                return f"{user_input_upper}/USD"

            print(f"Error: '{user_input}' not found. Choose from list or type valid asset name.")


def prompt_trade_type():
    """Interactive prompt for choosing buy or sell mode."""
    print("\n" + "=" * 60)
    print("TRADE TYPE")
    print("=" * 60)
    print("1. Buy  - Wait for dips, execute buy when price crosses stop")
    print("2. Sell - Wait for peaks, execute sell when price crosses stop")
    print()

    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == '1':
            return 'buy'
        elif choice == '2':
            return 'sell'
        else:
            print("Invalid choice. Please enter 1 or 2.")


def prompt_mode_selection():
    """Interactive prompt for choosing simple vs DCA mode."""
    print("\n" + "=" * 60)
    print("MODE SELECTION")
    print("=" * 60)
    print("1. Simple - Trade full balance with trailing stop only")
    print("2. DCA    - Use threshold ladder for partial exits at different prices")
    print()

    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == '1':
            return 'simple'
        elif choice == '2':
            return 'dca'
        else:
            print("Invalid choice. Please enter 1 or 2.")


def prompt_dca_type():
    """Interactive prompt for choosing default vs custom DCA."""
    print("\n" + "=" * 60)
    print("DCA CONFIGURATION")
    print("=" * 60)
    print("1. Default - Auto 4-tier ladder (+10%/+20%/+30%/+50%, 25% each)")
    print("2. Custom  - Define your own price thresholds")
    print()

    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == '1':
            return 'default'
        elif choice == '2':
            return 'custom'
        else:
            print("Invalid choice. Please enter 1 or 2.")


def prompt_dca_config():
    """Interactive prompt for custom DCA configuration."""
    print("\n" + "=" * 60)
    print("CUSTOM DCA THRESHOLDS")
    print("=" * 60)
    print("Enter thresholds as 'PRICE:AMOUNT,PRICE:AMOUNT,...'")
    print()
    print("Examples:")
    print("  Percentage: '+10%:5000,+20%:10000,+30%:15000'")
    print("  Absolute:   '0.30:5000,0.40:10000,0.50:15000'")
    print()

    while True:
        config = input("Enter configuration: ").strip()
        if not config:
            print("Error: Configuration cannot be empty.")
            continue

        # Basic validation - check format
        try:
            pairs = config.split(',')
            for pair in pairs:
                if ':' not in pair:
                    raise ValueError(f"Invalid format: '{pair}' - missing ':'")
                price_part, amount_part = pair.split(':', 1)
                if not price_part.strip() or not amount_part.strip():
                    raise ValueError(f"Invalid format: '{pair}' - empty price or amount")

            return config
        except ValueError as e:
            print(f"Error: {e}")
            print("Please use format: 'PRICE:AMOUNT,PRICE:AMOUNT'")


def prompt_stop_distance():
    """Interactive prompt for stop loss distance (percentage or absolute)."""
    print("\n" + "=" * 60)
    print("TRAILING STOP DISTANCE")
    print("=" * 60)
    print("1. Percentage - Distance as % of price (e.g., 5%)")
    print("2. Absolute   - Distance in dollar amount (e.g., $0.01 or $100)")
    print()

    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice not in ['1', '2']:
            print("Invalid choice. Please enter 1 or 2.")
            continue

        mode = 'percentage' if choice == '1' else 'absolute'

        # Prompt for value with mode-specific examples
        print()
        if mode == 'percentage':
            print("Enter percentage value:")
            print("  Examples: 0.05 for 5%, 0.10 for 10%, 0.02 for 2%")
            value_str = input("Value: ").strip()
        else:
            print("Enter absolute distance value:")
            print("  Examples: 0.01 for $0.01, 100 for $100, 0.005 for $0.005")
            value_str = input("Value: ").strip()

        # Validate value
        try:
            value = float(value_str)
            if value <= 0:
                print("Error: Value must be positive.")
                continue

            if mode == 'percentage' and value >= 1:
                print("Warning: Percentage should be decimal (e.g., 0.05 for 5%, not 5)")
                confirm = input("Continue with this value? (y/n): ").strip().lower()
                if confirm != 'y':
                    continue

            return (mode, value)
        except ValueError:
            print("Error: Invalid number format.")


def reset_instance_lock(symbol, trade_type):
    """Reset instance lock for a crashed or stuck instance."""
    import sqlite3 as sl
    import datetime

    print(f"Resetting instance lock for {symbol} {trade_type}...")

    try:
        con = sl.connect("exit_strategy.db")
        cursor = con.cursor()

        # Check if lock exists
        cursor.execute(
            "SELECT running, pid, started_at FROM instance_locks WHERE symbol = ? AND trade_type = ?",
            (symbol, trade_type)
        )
        result = cursor.fetchone()

        if result:
            running, pid, started_at = result
            if running == 1:
                print(f"Found active lock (PID: {pid}, started: {started_at})")
                print(f"Resetting lock...")
                cursor.execute(
                    """UPDATE instance_locks
                       SET running = 0, updated_at = ?
                       WHERE symbol = ? AND trade_type = ?""",
                    (datetime.datetime.now().isoformat(), symbol, trade_type)
                )
                con.commit()
                print(f"✓ Lock reset successfully for {symbol} {trade_type}")
            else:
                print(f"Lock already inactive for {symbol} {trade_type}")
        else:
            print(f"No lock found for {symbol} {trade_type}")

        cursor.close()
        con.close()

    except Exception as e:
        print(f"Error resetting lock: {e}")
        sys.exit(1)


def main(options):

    # Step 0: Determine trade type (buy/sell) - interactive if not provided
    if options.type:
        trade_type = options.type
        # Validate provided type
        if trade_type not in ['buy', 'sell']:
            print("Error: Please use valid trail type (Ex: 'buy' or 'sell')")
            return
    else:
        # No --type provided, ask interactively
        trade_type = prompt_trade_type()

    # Step 0.5: Determine symbol - interactive if not provided
    if options.symbol:
        symbol = options.symbol
    else:
        # No --symbol provided, ask interactively (different for buy vs sell)
        symbol = prompt_symbol(trade_type)

    # Step 1: Determine mode (simple vs DCA) - interactive if not provided
    dca_config = None
    simple_mode = options.simple

    if options.simple:
        # Simple mode explicitly requested via CLI
        dca_config = None
    elif options.DCA:
        # Custom DCA explicitly provided via CLI
        dca_config = options.DCA
    else:
        # Neither --simple nor --DCA provided - ask interactively
        mode = prompt_mode_selection()

        if mode == 'simple':
            simple_mode = True
            dca_config = None
        else:  # DCA mode
            # Ask if they want default or custom DCA
            dca_type = prompt_dca_type()

            if dca_type == 'default':
                dca_config = 'DEFAULT'
            else:  # custom
                dca_config = prompt_dca_config()

    # Step 2: Determine stop loss distance - interactive if not provided
    if options.distance is not None:
        # Absolute distance explicitly provided via CLI
        stop_mode = 'absolute'
        stop_value = options.distance
    elif options.size is not None:
        # Percentage size explicitly provided via CLI
        stop_mode = 'percentage'
        stop_value = options.size
    else:
        # Neither --size nor --distance provided - ask interactively
        stop_mode, stop_value = prompt_stop_distance()

    # Create and run the bot
    task = StopTrail(symbol, trade_type, stop_value, options.interval, options.split, simple_mode, dca_config, stop_mode)
    task.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Cryptocurrency trailing stop-loss bot for Coinbase Advanced Trade API',
        epilog='''
Examples:
  Simple mode with percentage-based stop (5%% trailing):
    python main.py --symbol DOGE/USD --type sell --size 0.05 --simple

  Simple mode with absolute distance stop ($0.01 trailing):
    python main.py --symbol DOGE/USD --type sell --distance 0.01 --simple

  Default DCA with percentage stop (4-tier: +10%%/+20%%/+30%%/+50%%, 25%% each):
    python main.py --symbol DOGE/USD --type sell --size 0.05

  Default DCA with absolute distance stop:
    python main.py --symbol BTC/USD --type sell --distance 100 --simple

  Custom DCA with absolute prices:
    python main.py --symbol DOGE/USD --type sell --size 0.05 --DCA '0.30:100,0.40:150,0.50:200'

  Custom DCA with percentages:
    python main.py --symbol BTC/USD --type sell --size 0.05 --DCA '+5%%:0.5,+10%%:0.5,+15%%:1.0'

  Reset stuck instance lock:
    python main.py --symbol DOGE/USD --type sell --reset-lock
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--symbol', type=str, help='Market Symbol (Ex: BTC/USD, DOGE/USD, ETH/USD)', required=False)

    # Mutually exclusive group for stop loss distance (optional - will prompt if not provided)
    stop_group = parser.add_mutually_exclusive_group(required=False)
    stop_group.add_argument('--size', type=float, help='Percentage-based stop loss distance (Ex: 0.05 = 5%%, 0.10 = 10%%)')
    stop_group.add_argument('--distance', type=float, help='Absolute/scalar stop loss distance in price units (Ex: 0.01 = $0.01, 100 = $100)')

    parser.add_argument('--type', type=str, help="Trading mode: 'buy' or 'sell'", required=False)
    parser.add_argument('--interval', type=float, help="How often to check for price changes in seconds (default: 5)", default=5)
    parser.add_argument('--split', type=int, help="How many trading pairs to split funds between (default: 1)", default=1)
    parser.add_argument('--simple', action='store_true', help="Simple mode: Use full balance with trailing stop (no threshold ladder)")
    parser.add_argument('--DCA', type=str, metavar='THRESHOLDS',
                       help="Comma-delimited DCA thresholds as PRICE:AMOUNT pairs. "
                            "Use absolute prices or +PERCENT%%. "
                            "Example: '0.30:100,0.40:150' or '+10%%:100,+20%%:150'")
    parser.add_argument('--reset-lock', action='store_true',
                       help="Reset instance lock for the specified symbol and type (use if previous instance crashed)")

    options = parser.parse_args()

    # Handle --reset-lock flag
    if options.reset_lock:
        if not options.symbol or not options.type:
            print("Error: --reset-lock requires both --symbol and --type")
            sys.exit(1)
        reset_instance_lock(options.symbol, options.type)
        sys.exit(0)

    main(options)

