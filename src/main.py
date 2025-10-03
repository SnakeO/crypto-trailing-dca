from trail import StopTrail
import argparse

def main(options):

    if options.type not in ['buy', 'sell']:
        print("Error: Please use valid trail type (Ex: 'buy' or 'sell')")
        return

    task = StopTrail(options.symbol, options.type, options.size, options.interval, options.split, options.simple)
    task.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Cryptocurrency trailing stop-loss bot for Coinbase Advanced Trade API',
        epilog='Example: python main.py --symbol DOGE/USD --type sell --size 0.05 --simple'
    )
    parser.add_argument('--symbol', type=str, help='Market Symbol (Ex: BTC/USD, DOGE/USD, ETH/USD)', required=True)
    parser.add_argument('--size', type=float, help='Decimal percentage for stop loss distance (Ex: 0.05 = 5%%, 0.10 = 10%%)', required=True)
    parser.add_argument('--type', type=str, help="Trading mode: 'buy' or 'sell'", required=True)
    parser.add_argument('--interval', type=float, help="How often to check for price changes in seconds (default: 5)", default=5)
    parser.add_argument('--split', type=int, help="How many trading pairs to split funds between (default: 1)", default=1)
    parser.add_argument('--simple', action='store_true', help="Simple mode: Use full balance with trailing stop (no threshold ladder configuration needed)")

    options = parser.parse_args()
    main(options)

