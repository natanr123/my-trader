from sqlmodel import Session

from app.models.order import Order
from app.models.order import OrderCreate
from app.utils.my_alpaca_client import MyAlpacaClient
from app.models.user import User


class OrderService:
    def create_order_with_alpaca_order(self, user: User, order_in: OrderCreate, session: Session, alpaca_client: MyAlpacaClient) -> Order:
        alpaca_order = alpaca_client.submit_buy_order(order_in.symbol, order_in.amount)
        order = Order.model_validate(order_in, update={"owner_id": user.id})
        order.buy_submitted(alpaca_order_id=alpaca_order.id)
        session.add(order)
        session.commit()
        session.refresh(order)
        return order