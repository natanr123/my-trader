import logging

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.api.deps.alpaca_dep import AlpacaDep
from app.crud.order_crud import OrderCrud
from app.models.order import Order, OrderCreate, OrderPublic

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderPublic)
def create_order(
    order_in: OrderCreate,
    current_user: CurrentUser,
    session: SessionDep,
    alpaca_client: AlpacaDep,
):
    order = OrderCrud.create_order_with_alpaca_order(
        user=current_user,
        order_in=order_in,
        session=session,
        alpaca_client=alpaca_client,
    )
    return order


@router.get("/")
def list_orders(session: SessionDep, current_user: CurrentUser) -> list[OrderPublic]:
    statement = select(Order).where(Order.owner_id == current_user.id)
    results = session.exec(statement)
    orders = results.all()
    # Pydantic automatically converts Order to OrderPublic at runtime, but mypy can't infer this
    return orders  # type: ignore[return-value]


@router.post(
    "/{id}/sync",
    responses={
        200: {"description": "Order synchronized successfully"},
        403: {"description": "Not authorized to sync this order"},
        404: {"description": "Order not found"},
        500: {"description": "Internal server error during synchronization"},
    },
)
def sync_order(
    id: int, session: SessionDep, alpaca_client: AlpacaDep, current_user: CurrentUser
) -> OrderPublic:
    order = session.get(Order, id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to sync this order")
    OrderCrud.sync_order_status(order=order, alpaca_client=alpaca_client)
    session.commit()
    session.refresh(order)
    OrderCrud.apply_sell_rules(order=order, alpaca_client=alpaca_client)
    session.commit()
    session.refresh(order)

    # Pydantic automatically converts Order to OrderPublic at runtime, but mypy can't infer this
    return order  # type: ignore[return-value]


@router.get("/{id}")
def show_order(id: int, session: SessionDep) -> OrderPublic:
    order = session.get(Order, id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Pydantic automatically converts Order to OrderPublic at runtime, but mypy can't infer this
    return order  # type: ignore[return-value]


@router.delete("/{id}", status_code=204)
def delete_order(id: int, session: SessionDep, current_user: CurrentUser):
    order = session.get(Order, id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.owner_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this order"
        )

    session.delete(order)
    session.commit()


@router.post("/sync")
def sync_orders(session: SessionDep, alpaca_client: AlpacaDep):
    # my_file_log = MyFileLog('tmp/syncs.log')

    logger.info("Syncing orders")
    statement = select(Order)
    results = session.exec(statement)
    orders = results.all()
    total_orders = len(orders)

    logger.info("Total orders: %d", total_orders)
    for order in orders:
        OrderCrud.sync_order_status(order=order, alpaca_client=alpaca_client)
        session.commit()
        session.refresh(order)
        OrderCrud.apply_sell_rules(order=order, alpaca_client=alpaca_client)
        session.commit()
        session.refresh(order)
    return {"result": "success"}
