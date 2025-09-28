from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep
from app.api.deps.alpaca_dep import AlpacaDep
from app.models.order import Order, OrderCreate, OrderPublic, VirtualOrderStatus
from app.api.deps import CurrentUser

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=OrderPublic)
def create_order(
    order_in: OrderCreate, current_user: CurrentUser,
    session: SessionDep,
    alpaca_client: AlpacaDep
):
    # my_file_log = MyFileLog('tmp/create_orders.log')

    # order =  Order(**order_in.model_dump())
    order = Order.model_validate(order_in, update={"owner_id": current_user.id})
    # my_file_log.append('Creating new order: ', payload)
    session.add(order)
    session.commit()
    session.refresh(order)
    ####################################################
    alpaca_order = alpaca_client.submit_buy_order(order.symbol, order.amount)
    order.buy_submitted(alpaca_order_id=alpaca_order.id)
    ######################################################
    session.commit()
    session.refresh(order)
    return order


@router.get("/")
def list_orders(
    session: SessionDep,
) -> list[OrderPublic]:
    statement = select(Order).where(getattr(Order, "deleted_at", None).is_(None))
    results = session.exec(statement)
    orders = results.all()
    return orders



@router.post(
    "/{id}/sync",
    responses={
        200: {"description": "Order synchronized successfully"},
        404: {"description": "Order not found"},
        500: {"description": "Internal server error during synchronization"}
    }
)
def sync_order(id: int, session: SessionDep, alpaca_client: AlpacaDep) -> OrderPublic:
    order = session.get(Order, id)
    order.sync(alpaca_client=alpaca_client)
    session.commit()
    session.refresh(order)
    return order

@router.get("/{id}")
def show_order(id: int, session: SessionDep) -> OrderPublic:
    order = session.get(Order, id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.delete("/{id}", status_code=204)
def delete_order(id: int, session: SessionDep):
    order = session.get(Order, id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    session.delete(order)
    session.commit()

@router.post("/sync")
def sync_orders(
    session: SessionDep,
    alpaca_client: AlpacaDep
):
    # my_file_log = MyFileLog('tmp/syncs.log')

    print('Syncing orders ......................................')
    statement = select(Order)
    results = session.exec(statement)
    orders = results.all()
    total_orders = len(orders)

    print('Total orders: ', total_orders)
    for order in orders:
        order.sync(alpaca_client=alpaca_client)
    return {"result": "success"}




