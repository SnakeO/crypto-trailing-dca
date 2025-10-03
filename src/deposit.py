import time
from datetime import datetime, timedelta
from coinbasepro import CoinbasePro
from helper import get_logger, send_sns, Config

logger = get_logger('deposit')

coinbasepro = CoinbasePro(
    api_key = Config.get_value('deposit', 'deposit_api_key_name'),
    api_secret = Config.get_value('deposit', 'deposit_api_private_key')
)

payment_method_id = Config.get_value('deposit', 'payment_method_id')
deposit_amount = Config.get_value('deposit', 'deposit_amount')
currency = Config.get_value('deposit', 'currency')

try:
    deposit = coinbasepro.deposit_funds(payment_method_id, deposit_amount, currency)
    message = 'Deposit successful: $%s' % deposit_amount
    logger.warning(message)
    send_sns(message)

except NotImplementedError as e:
    # Deposit functionality not yet implemented for Advanced Trade API
    message = 'Deposit functionality not available: %s' % e
    logger.warning(message)
    send_sns(message)

except ConnectionError as e:
    # Network error - attempt to verify deposit via fetch_deposits
    time.sleep(5)
    try:
        deposit_lookup = coinbasepro.fetch_deposits()
        timestamp = deposit_lookup[-1]['info']['created_at'][:-3]
        timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
        difference = datetime.now() - timestamp
        if difference < timedelta(minutes=5):
            message = 'Deposit successful: $%s' % deposit_lookup['info']['amount']
            logger.warning(message)
            send_sns(message)
        else:
            message = 'Deposit failed: %s' % e
            logger.exception(message)
            send_sns(message)
    except Exception as inner_e:
        message = 'Deposit verification failed: %s' % inner_e
        logger.exception(message)
        send_sns(message)

except Exception as e:
    message = 'Deposit failed: %s' % e
    logger.exception(message)
    send_sns(message)