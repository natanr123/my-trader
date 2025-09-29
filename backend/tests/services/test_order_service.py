from app.clients.my_alpaca_client import MyAlpacaClient
from sqlmodel import Session
from app.services.order_service import OrderService


def test_handle_buy_pending_new(alpaca_client: MyAlpacaClient, order_service: OrderService) -> None:
    print('alpaca_clientalpaca_clientalpaca_client: ', alpaca_client)
    print('order_serviceorder_serviceorder_service: ', order_service)

    print('aaaaaaaaaaaaaaaaaa')
