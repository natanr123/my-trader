from typing import Annotated
from fastapi import Depends
from app.clients.my_alpaca_client import MyAlpacaClient
from app.core.config.alpaca_settings import alpaca_settings

def get_alpaca_client():
    return MyAlpacaClient(alpaca_settings.credentials)

AlpacaDep = Annotated[MyAlpacaClient, Depends(get_alpaca_client)]