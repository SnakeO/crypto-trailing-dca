# crypto-trailing-dca
Implements dynamic, trailing stop loss functionality for Coinbase Pro. Designed to be utilized in either 1) “buy-mode” to create a dollar cost average (DCA) strategy that capitalizes on short-term down swings or 2) “sell-mode” to maximize profits by executing a hybrid-DCA exit strategy based on predefined take-profit thresholds and trailing stop losses.


## Installation

**Clone the repository**
```
git clone https://github.com/SnakeO/crypto-trailing-dca
```

**Install required libraries**
```
apt-get install python-pip -y
pip install -r src/requirements.txt
```

Or install manually:
```
pip install coinbase-advanced-py boto3 pandas
```


## Configure API keys

**IMPORTANT: Coinbase Pro API has been deprecated. This project now uses Coinbase Advanced Trade API (Feb 2025).**

### Generate Coinbase CDP API Keys

1. Visit the Coinbase Developer Platform: https://portal.cdp.coinbase.com/projects
2. Sign in with your Coinbase account
3. Create a new project or select an existing one
4. Navigate to "API Keys" section
5. Click "Create API Key"
6. Select permissions: Enable **View** and **Trade** permissions
7. Choose key type: **ES256** (ECDSA with P-256 curve) - EdDSA is NOT supported
8. Click "Generate Key"
9. **IMPORTANT**: Save the following information immediately (you won't be able to see the private key again):
   - API Key Name (format: `organizations/{org_id}/apiKeys/{key_id}`)
   - Private Key (PEM format, starts with `-----BEGIN EC PRIVATE KEY-----`)

### Configure settings.ini

Modify `/conf/settings.ini` and insert your CDP API credentials:

```ini
[api]
api_key_name=organizations/YOUR_ORG_ID/apiKeys/YOUR_KEY_ID
api_private_key=-----BEGIN EC PRIVATE KEY-----
YOUR_PRIVATE_KEY_HERE
-----END EC PRIVATE KEY-----
```

**Note**: Legacy Coinbase Pro credentials (`api_key`, `api_secret`, `password`) are no longer supported as of February 5, 2025.



## Initialize Database

**Before first run**, you must initialize the exit strategy database:

```bash
cd src
python create-db.py
```

**For Sell Mode**: Edit `src/create-db.py` (lines 48-53) to customize your exit thresholds before running:

```python
data1 = [
    (1, 14200, 0.05, 'N', None),  # At $14,200, release 0.05 coins to sell
    (2, 14900, 0.05, 'N', None),  # At $14,900, release 0.05 coins to sell
    (3, 15500, 0.05, 'N', None),  # At $15,500, release 0.05 coins to sell
    (4, 16500, 0.05, 'N', None),  # At $16,500, release 0.05 coins to sell
]
```

This creates `exit_strategy.db` which persists your:
- Exit price thresholds and amounts (sell mode)
- Current stop loss value (both modes)
- Trading performance statistics (buy mode)
- Balance tracking (buy mode)

## Running

**Usage**

```
$ python main.py --help
usage: main.py [-h] --symbol SYMBOL --size SIZE --type TYPE [--interval INTERVAL] [--split SPLIT]

optional arguments:
  -h, --help           show this help message and exit
  --symbol SYMBOL      Market Symbol (e.g., BTC/USD, ETH/USD)
  --size SIZE          The decimal value of the percentage that the stop loss should be placed above or below current price (e.g., 0.05, 0.10)
  --type TYPE          Specify whether the trailing stop loss should be in buying or selling mode. (e.g., 'buy' or 'sell')
  --interval INTERVAL  How often the bot should check for price changes (default: 5 seconds)
  --split SPLIT        How many trading pairs should we allocate our funds between? (e.g., if ETH/USD and BTC/USD simultaneously: 2, if ETH/USD only: 1)
```

**Examples**

```bash
# Sell mode: Trail stop loss upward as price rises
python3 src/main.py --symbol BTC/USD --size 0.05 --type sell --interval 5

# Buy mode: Wait for dips, trail stop loss downward
python3 src/main.py --symbol ETH/USD --size 0.10 --type buy --interval 5 --split 1
```

**Important notes**

- **Sell mode**: Assumes you already own the coins to sell
- **Buy mode**: Uses total available balance in base currency (USD, etc.)
- **Database persistence**: Bot state survives restarts via `exit_strategy.db`
- **Reset state**: Delete `exit_strategy.db` and re-run `create-db.py` for fresh start


## Parameters

**--type buy**

If the **buy** option is set, the bot will initially place a stop-loss (100 * `size`)% **above** the current market price (e.g., (100 * 0.05 = 5%)). As the price goes lower, the stop-loss will get dragged with it, staying no higher than the size specified. Once the price crosses the stop-loss price, a buy order is executed.

**--type sell**

If the **sell** option is set, the bot will initially place a stop-loss (100 * `size`)% **below** the current market price (e.g., (100 * 0.05 = 5%)). As the price goes higher, the stop-loss will get dragged with it, staying no lower than the size specified. Once the price crosses the stop-loss price, a sell order is executed.

**--size**

This is the percentage difference you would like the stop-loss to be retained at. The difference between the current price and stop-loss will never be larger than this amount.

## Overview

### Sell Mode
Allows user to create an exit strategy including:
1. Exit price (e.g., $600)
2. Amount of coins to release at exit price (e.g., 0.5 ETH)

| Exit Price | Amount (ETH) |
|-----|------|
| 600 | 0.25 |
| 775 | 0.25 |
| 925 | 0.50 |
| 1080 | 1.0 |
| 1250 | 1.5 |

The bot will track the current price against the defined thresholds and release coins to be sold as thresholds are met. As new thresholds are hit, the bot will automatically increment a "hopper" to track the appropriate amount of coins to sell based on the defined exit strategy. When the market price drops below an established stop loss value, the bot will sell only the amount of coins that have been released into the hopper (i.e., those marked "available to sell"). 

![image](https://user-images.githubusercontent.com/13890717/113211258-1c89b280-922a-11eb-866d-2a9d3c10a292.png)


### Buy Mode

In 'buy-mode', the bot will actively monitor the market price around a defined range that is initialized upon the deposit of USD funds to the account. The bot will execute a strategy around this "range" that consists of three modes: 

1. If the market price rises X% above the deposit price it will execute a market buy order. 
2. If the market price ranges between the higher and lower bound (X% above and X% below deposit price), no action is taken.
3. If the market price drops X% below the deposit price, it will initialize a stoploss at the deposit price and continue to lower the stoploss upon each new price low observed. Once a stoploss has been initialized the bot will execute a market buy order if the current market price exceeds the stoploss. 

![image](https://user-images.githubusercontent.com/13890717/113211108-e1877f00-9229-11eb-971b-35af02e8d68f.png)


## Migration from Legacy Coinbase Pro API

If you're upgrading from an older version of this project that used Coinbase Pro API:

1. **Generate new CDP API keys** following the instructions above
2. **Update conf/settings.ini** with the new key format:
   - Replace `api_key` with `api_key_name` (organizations format)
   - Replace `api_secret` with `api_private_key` (EC PEM format)
   - Remove `password` field (no longer used)
3. **Apply the same changes to `[live_api]` and `[deposit]` sections**
4. **Reinstall dependencies**: `pip install -r src/requirements.txt`
5. **Test with small amounts first** to verify the migration was successful

**Breaking Changes**:
- Deposit functionality may have limited support - use Coinbase web interface for deposits
- Symbol format is auto-converted (BTC/USD → BTC-USD) but behavior should remain the same
- Error handling updated to work with new SDK exceptions

## License
Released under GPLv3.
