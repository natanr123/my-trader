from app.clients.my_alpaca_client import MyAlpacaClient, AlpacaOrder, AlpacaOrderStatus
from sqlmodel import Session
from app.models.order import Order, VirtualOrderStatus
from uuid import UUID
from app.models.user import UserCreate
from app.crud import crud
from app.models.order import OrderCreate

def test_buy_submitted(db: Session) -> None:
    user_in = UserCreate(email='test_buy_submitted@test.com', password='12345678')
    user = crud.create_user(session=db, user_create=user_in)
    db.add(user)
    db.commit()
    db.refresh(user)
    alpaca_order_id = UUID('cbe2c370-f613-41d0-9833-248f1ade5d6d')
    order_in = OrderCreate(symbol='AAPL', amount=55)
    order = Order.model_validate(order_in, update={"owner_id": user.id})
    assert order.status == VirtualOrderStatus.NEW
    order.buy_submitted(alpaca_order_id=alpaca_order_id)
    db.add(order)
    db.commit()
    db.refresh(order)
    assert order.status == VirtualOrderStatus.BUY_PENDING_NEW