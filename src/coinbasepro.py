from coinbase.rest import RESTClient
import uuid
import time

class CoinbasePro():
    """
    Wrapper for Coinbase Advanced Trade API using official coinbase-advanced-py SDK.
    Migrated from legacy Coinbase Pro API (CCXT) to Advanced Trade API v3.
    """

    def __init__(self, api_key, api_secret, password=None):
        """
        Initialize Coinbase Advanced Trade client.

        Args:
            api_key: CDP API key name in format: organizations/{org_id}/apiKeys/{key_id}
            api_secret: EC private key in PEM format
            password: Deprecated, not used in Advanced Trade API (kept for compatibility)
        """
        self.client = RESTClient(
            api_key=api_key,
            api_secret=api_secret
        )

    def _convert_symbol(self, symbol):
        """
        Convert CCXT-style symbol (BTC/USD) to Coinbase format (BTC-USD).

        Args:
            symbol: Trading pair in CCXT format (e.g., 'BTC/USD')

        Returns:
            Trading pair in Coinbase format (e.g., 'BTC-USD')
        """
        return symbol.replace('/', '-')

    def buy(self, market, funds):
        """
        Execute a market buy order using specified funds amount.

        Args:
            market: Trading pair (e.g., 'BTC/USD')
            funds: USD amount to spend

        Returns:
            Order response from Coinbase API
        """
        product_id = self._convert_symbol(market)
        client_order_id = str(uuid.uuid4())

        order = self.client.market_order_buy(
            client_order_id=client_order_id,
            product_id=product_id,
            quote_size=str(funds)  # USD amount to spend
        )

        # Transform response to match CCXT-like structure for compatibility
        return {
            'id': order.get('order_id') or order.get('success_response', {}).get('order_id'),
            'info': order,
            'status': 'pending'
        }

    def sell(self, market, amount):
        """
        Execute a market sell order for specified amount of base currency.

        Args:
            market: Trading pair (e.g., 'BTC/USD')
            amount: Amount of base currency to sell (e.g., BTC amount)

        Returns:
            Order response from Coinbase API
        """
        product_id = self._convert_symbol(market)
        client_order_id = str(uuid.uuid4())

        order = self.client.market_order_sell(
            client_order_id=client_order_id,
            product_id=product_id,
            base_size=str(amount)  # Amount of crypto to sell
        )

        # Transform response to match CCXT-like structure for compatibility
        return {
            'id': order.get('order_id') or order.get('success_response', {}).get('order_id'),
            'info': order,
            'status': 'pending'
        }

    def get_price(self, market):
        """
        Get current market price for a trading pair.

        Args:
            market: Trading pair (e.g., 'BTC/USD')

        Returns:
            Current price as float
        """
        product_id = self._convert_symbol(market)
        product = self.client.get_product(product_id)

        # SDK returns GetProductResponse object, convert to dict
        if hasattr(product, '__dict__'):
            product_dict = product.__dict__
        else:
            product_dict = dict(product)

        # Extract price from product data
        price = float(product_dict.get('price', 0))

        return price

    def get_balance(self, coin):
        """
        Get available balance for a specific currency.

        Args:
            coin: Currency code (e.g., 'USD', 'BTC')

        Returns:
            Available balance as float
        """
        accounts_response = self.client.get_accounts()

        # SDK returns object, convert to dict
        if hasattr(accounts_response, '__dict__'):
            accounts_dict = accounts_response.__dict__
        else:
            accounts_dict = dict(accounts_response)

        # Find account matching the currency
        for account in accounts_dict.get('accounts', []):
            account_dict = account.__dict__ if hasattr(account, '__dict__') else dict(account)
            if account_dict.get('currency') == coin:
                available_balance = account_dict.get('available_balance', {})
                balance_dict = available_balance.__dict__ if hasattr(available_balance, '__dict__') else dict(available_balance)
                return float(balance_dict.get('value', 0))

        return 0.0

    def get_order(self, id):
        """
        Get order details by order ID.

        Args:
            id: Order ID

        Returns:
            Order details in CCXT-compatible format
        """
        order = self.client.get_order(id)

        # Transform to CCXT-like structure
        order_data = order.get('order', {})

        # Calculate filled amount and cost
        filled_size = float(order_data.get('filled_size', 0))
        filled_value = float(order_data.get('filled_value', 0))

        # Get fee information
        total_fees = float(order_data.get('total_fees', 0))

        # Determine fill price
        avg_price = filled_value / filled_size if filled_size > 0 else 0

        return {
            'id': order_data.get('order_id'),
            'status': order_data.get('status'),
            'amount': filled_size,
            'filled': filled_size,
            'cost': filled_value,
            'price': avg_price,
            'fee': {
                'cost': total_fees,
                'currency': order_data.get('product_id', '').split('-')[-1]
            },
            'info': order_data
        }

    def get_payment_methods(self):
        """
        Get list of payment methods.
        Note: This functionality may require different permissions or API endpoints.

        Returns:
            List of payment methods
        """
        # Advanced Trade API v3 has payment methods endpoints
        try:
            payment_methods = self.client.get_payment_methods()
            return payment_methods
        except Exception as e:
            # If not available, return empty list
            print(f"Payment methods not available: {e}")
            return {'payment_methods': []}

    def deposit_funds(self, payment_method_id, deposit_amount, currency):
        """
        Deposit funds from a payment method.
        Note: This may require Wallet API or different endpoint in v3.

        Args:
            payment_method_id: ID of payment method
            deposit_amount: Amount to deposit
            currency: Currency code

        Returns:
            Deposit response
        """
        # This functionality may not be directly available in Advanced Trade API
        # May need to use Wallet API or other endpoints
        raise NotImplementedError(
            "Deposit functionality requires Wallet API or additional configuration. "
            "Please use Coinbase web interface for deposits or implement Wallet API separately."
        )

    def fetch_deposits(self):
        """
        Fetch deposit history.
        Note: This may require Wallet API or different endpoint in v3.

        Returns:
            List of deposits
        """
        # This functionality may not be directly available in Advanced Trade API
        raise NotImplementedError(
            "Fetch deposits functionality requires Wallet API or additional configuration. "
            "Please use Coinbase web interface to view deposit history."
        )
