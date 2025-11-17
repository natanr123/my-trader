from typing import Annotated

from fastapi import Depends

from app.clients.my_alpaca_client import MyAlpacaClient
from app.core.config.alpaca_settings import AlpacaSettings, alpaca_settings


def get_my_alpaca_client():
    return MyAlpacaClient(alpaca_settings.credentials)


# We do not want any outside calls in test
def get_my_alpaca_client_test():
    test_settings = AlpacaSettings(
        ALPACA_API_KEY="NOTREAL6A5W029JXQH4D",
        ALPACA_SECRET_KEY="NOTREALt5wcgRbktip0fLx4vTneRoBoeOJCjBuLI",
        ALPACA_NAME="test",
        ALPACA_PAPER=True,
    )
    return MyAlpacaClient(test_settings.credentials)


AlpacaDep = Annotated[MyAlpacaClient, Depends(get_my_alpaca_client)]
