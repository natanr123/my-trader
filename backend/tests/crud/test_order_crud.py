from app.clients.my_alpaca_client import MyAlpacaClient, AlpacaOrder, AlpacaOrderStatus
from sqlmodel import Session
from app.crud.order_crud import OrderCrud, OrderSyncData
from app.models.order import Order, VirtualOrderStatus
from uuid import UUID
from datetime import datetime

def test_handle_buy_pending_new(alpaca_client: MyAlpacaClient, db: Session) -> None:
    order = Order(status=VirtualOrderStatus.BUY_PENDING_NEW)
    buy_order = AlpacaOrder(id=UUID('cbe2c370-f613-41d0-9833-248f1ade5d6d'),
                            client_order_id="",
                            created_at=datetime.now(),
                            updated_at=datetime.now(),
                            submitted_at=datetime.now(),
                            time_in_force='day',
                            status = AlpacaOrderStatus.ACCEPTED,
                            extended_hours=False,
                            )
    sync_data = OrderSyncData(buy_order=buy_order, sell_order=None)

    OrderCrud._handle_buy_pending_new(order=order, sync_data=sync_data, alpaca_client=alpaca_client)
    assert order.status == VirtualOrderStatus.BUY_ACCEPTED

