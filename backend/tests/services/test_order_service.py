from app.clients.my_alpaca_client import MyAlpacaClient, AlpacaOrder, AlpacaOrderStatus
from sqlmodel import Session
from app.services.order_service import OrderService, OrderSyncData
from app.models.order import OrderCreate, OrderPublic, Order, VirtualOrderStatus
from app.models.user import UserCreate, User
from app.crud import create_user
from uuid import UUID
from datetime import datetime
def test_handle_buy_pending_new(alpaca_client: MyAlpacaClient, order_service: OrderService, db: Session) -> None:
    print('alpaca_clientalpaca_clientalpaca_client: ', alpaca_client)
    print('order_serviceorder_serviceorder_service: ', order_service)

    print('aaaaaaaaaaaaaaaaaa')
    user_create = UserCreate(email='aaaa@aaa.com', password='12345678')
    user = create_user(session=db, user_create=user_create)
    order_in = OrderCreate(symbol='AAPL', amount=100)
    # order_service.create_order_with_alpaca_order(user=user, order_in=order_in, session=db, alpaca_client=alpaca_client)
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

    order_service._handle_buy_pending_new(order=order, sync_data=sync_data, alpaca_client=alpaca_client)


    # db_obj = User.model_validate(
    #     user_create, update={"hashed_password": get_password_hash(user_create.password)}
    # )
    # session.add(db_obj)
    # session.commit()
    # session.refresh(db_obj)

    # user_create = UserCreate(email='aaaaaaa@aaaa.com', password='12345678')
    # user = User.model_validate(user_create, update = {"hashed_password": get_password_hash(user_create.password)})
    # db.add(user)
    # db.commit()
    # db.refresh(user)
    # print(user)

    # order = order_service.create_order_with_alpaca_order()


    # order_service._handle_buy_pending_new()
