from trail import StopTrail
import argparse
import sys

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


def main(options):

    if options.type not in ['buy', 'sell']:
        print("Error: Please use valid trail type (Ex: 'buy' or 'sell')")
        return

    # Determine DCA configuration based on mode
    dca_config = None

    if options.simple:
        # Simple mode: no DCA configuration needed
        dca_config = None
    elif options.DCA:
        # Custom DCA provided - parse it (need current price first)
        # Will be parsed inside StopTrail after getting current price
        dca_config = options.DCA
    else:
        # No --simple, no --DCA: use default DCA strategy
        # Will be generated inside StopTrail after getting current price and balance
        dca_config = 'DEFAULT'

    task = StopTrail(options.symbol, options.type, options.size, options.interval, options.split, options.simple, dca_config)
    task.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Cryptocurrency trailing stop-loss bot for Coinbase Advanced Trade API',
        epilog='''
Examples:
  Simple mode (full balance, no DCA):
    python main.py --symbol DOGE/USD --type sell --size 0.05 --simple

  Default DCA (4-tier: +10%%/+20%%/+30%%/+50%%, 25%% each):
    python main.py --symbol DOGE/USD --type sell --size 0.05

  Custom DCA with absolute prices:
    python main.py --symbol DOGE/USD --type sell --size 0.05 --DCA '0.30:100,0.40:150,0.50:200'

  Custom DCA with percentages:
    python main.py --symbol BTC/USD --type sell --size 0.05 --DCA '+5%%:0.5,+10%%:0.5,+15%%:1.0'
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--symbol', type=str, help='Market Symbol (Ex: BTC/USD, DOGE/USD, ETH/USD)', required=True)
    parser.add_argument('--size', type=float, help='Decimal percentage for stop loss distance (Ex: 0.05 = 5%%, 0.10 = 10%%)', required=True)
    parser.add_argument('--type', type=str, help="Trading mode: 'buy' or 'sell'", required=True)
    parser.add_argument('--interval', type=float, help="How often to check for price changes in seconds (default: 5)", default=5)
    parser.add_argument('--split', type=int, help="How many trading pairs to split funds between (default: 1)", default=1)
    parser.add_argument('--simple', action='store_true', help="Simple mode: Use full balance with trailing stop (no threshold ladder)")
    parser.add_argument('--DCA', type=str, metavar='THRESHOLDS',
                       help="Comma-delimited DCA thresholds as PRICE:AMOUNT pairs. "
                            "Use absolute prices or +PERCENT%%. "
                            "Example: '0.30:100,0.40:150' or '+10%%:100,+20%%:150'")

    options = parser.parse_args()
    main(options)

