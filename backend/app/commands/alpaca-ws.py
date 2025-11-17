from app.api.deps.alpaca_dep import get_my_alpaca_client
from app.clients.my_alpaca_client import AlpacaBar
import logging
logger = logging.getLogger(__name__)


async def on_amd_bar(bar: AlpacaBar) -> None:
    logger.info(
        f"New AMD 1m bar: "
        f"{bar.timestamp} "
        f"o={bar.open} h={bar.high} l={bar.low} c={bar.close} v={bar.volume}"
    )


my_alpaca_client = get_my_alpaca_client()
logger.info("Subscribing to AMD 1m bars...")
my_alpaca_client.subscribe_bar_crypto(pair="BTC/USD", on_bar=on_amd_bar)

