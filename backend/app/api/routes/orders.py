from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep
from app.api.deps.alpaca_dep import AlpacaDep
from app.models.order import Order, OrderCreate, OrderPublic, VirtualOrderStatus
from app.api.deps import CurrentUser
from app.api.deps.order_service_dep import OrderServiceDep

router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=OrderPublic)
def create_order(
    order_in: OrderCreate, current_user: CurrentUser,
    session: SessionDep,
    alpaca_client: AlpacaDep,
    order_service: OrderServiceDep
):
    order = order_service.create_order_with_alpaca_order(user=current_user, order_in=order_in, session=session, alpaca_client=alpaca_client)
    return order

@router.post("/by_admin", response_model=OrderPublic)
def create_order_by_admin(
    order_in: OrderCreate,
    session: SessionDep,
    alpaca_client: AlpacaDep,
    order_service: OrderServiceDep
):
    from app.models.user import User
    admin = session.exec(select(User).where(User.is_superuser == True)).first()
    if not admin:
        raise HTTPException(status_code=404, detail="No admin user found")
    order = order_service.create_order_with_alpaca_order(user=admin, order_in=order_in, session=session, alpaca_client=alpaca_client)
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
        403: {"description": "Not authorized to sync this order"},
        404: {"description": "Order not found"},
        500: {"description": "Internal server error during synchronization"}
    }
)
def sync_order(id: int, session: SessionDep, alpaca_client: AlpacaDep, current_user: CurrentUser) -> OrderPublic:
    order = session.get(Order, id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to sync this order")
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
def delete_order(id: int, session: SessionDep, current_user: CurrentUser):
    order = session.get(Order, id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this order")

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




