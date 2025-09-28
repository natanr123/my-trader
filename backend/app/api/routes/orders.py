from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import SessionDep
from app.api.deps.my_alpaca_client import AlpacaDep, AlpacaOrderStatus, AlpacaOrder

from app.models.order import Order, OrderCreate, OrderPublic, VirtualOrderStatus
from alpaca.common.exceptions import APIError


router = APIRouter(prefix="/orders", tags=["orders"])

@router.post("/", response_model=OrderPublic)
def create_order(
    payload: OrderCreate,
    session: SessionDep,
    alpaca_client: AlpacaDep
):
    # my_file_log = MyFileLog('tmp/create_orders.log')

    order = Order(**payload.model_dump())
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
    statement = select(Order)
    results = session.exec(statement)
    orders = results.all()
    return orders

@router.post("/{id}/sync")
def sync_order(id: int, session: SessionDep, alpaca_client: AlpacaDep) -> OrderPublic:
    order = session.get(Order, id)
    if order.alpaca_buy_order_id:
        alpaca_buy_order = alpaca_client.get_order_by_id(order.alpaca_buy_order_id)
    else:
        raise Exception('Order was created but no matching alpaca buy order')

    alpaca_sell_order: AlpacaOrder | None = None
    if order.alpaca_sell_order_id:
        alpaca_sell_order = alpaca_client.get_order_by_id(order.alpaca_sell_order_id)

    # my_file_log.append('working on order id=', order.id, 'status=', order.status, 'alpaca_status=', alpaca_buy_order.status, 'alpaca_sell_order=', bool(alpaca_sell_order))

    # NEW -> BUY_PENDING_NEW -> BUY_ACCEPTED -> BUY_FILLED -> SELL_PENDING_NEW -> SELL_ACCEPTED -> SELL_FILLED
    if order.status == VirtualOrderStatus.BUY_PENDING_NEW:
        print('the order id=', order.id, 'waiting for it to be filled. Nothing to do for now')
        if alpaca_buy_order.status == AlpacaOrderStatus.ACCEPTED:
            # my_file_log.append('the order id=', order.id, 'moving from buying to accepted')
            order.buy_accepted()
            session.commit()
        elif alpaca_buy_order.status == AlpacaOrderStatus.FILLED:
            # my_file_log.append('the order id=', order.id, 'moving from buying to filled')
            order.buy_accepted()
            session.commit()
            session.refresh(order)
            market_close_at = alpaca_client.get_next_close()
            order.buy_filled(filled_avg_price=alpaca_buy_order.filled_avg_price,
                             buy_filled_qty=alpaca_buy_order.filled_qty, market_close_at=market_close_at)
            session.commit()
    elif order.status == VirtualOrderStatus.BUY_ACCEPTED:
        if alpaca_buy_order.status == AlpacaOrderStatus.ACCEPTED:
            print('the order id=', order.id, 'waiting for it to be filled. Nothing to do for now')
        elif alpaca_buy_order.status == AlpacaOrderStatus.FILLED:
            # my_file_log.append('the order id=', order.id, 'is moving from buying accepted buying to filled')
            market_close_at = alpaca_client.get_next_close()
            order.buy_filled(filled_avg_price=alpaca_buy_order.filled_avg_price,
                             buy_filled_qty=alpaca_buy_order.filled_qty, market_close_at=market_close_at)
            session.commit()
    elif order.status == VirtualOrderStatus.BUY_FILLED:
        still_have_time = not alpaca_client.is_time_passed(order.force_sell_at)
        if still_have_time:
            # my_file_log.append('the order id=', order.id, 'was buy filled','but it is not time-passed', 'doing nothing')
            continue
        ######################################################
        try:
            alpaca_sell_order = alpaca_client.close_position(order.symbol)
            # my_file_log.append('the order id=', order.id, 'buy was filled', 'sell position not found', 'sending sell order -> buy_pending_new')
            order.sell_submitted(alpaca_order_id=alpaca_sell_order.id)
        except APIError as e:
            # my_file_log.append('the order id=', order.id, 'buy was filled', 'sell position arelady FOUND', 'skipping to sell filled')
            order.sell_submitted(alpaca_order_id=None)
            order.sell_accepted()
            order.sell_filled(filled_avg_price=0, filled_qty=0)

        session.commit()
        ############################################
    elif order.status == VirtualOrderStatus.SELL_PENDING_NEW:
        if alpaca_sell_order.status == AlpacaOrderStatus.ACCEPTED:
            # my_file_log.append('the order id=', order.id, 'sell order was accepted')
            order.sell_accepted()
            session.commit()
        elif alpaca_sell_order.status == AlpacaOrderStatus.FILLED:
            # my_file_log.append('the order id=', order.id, 'sell order was filled')
            order.sell_accepted()
            order.sell_filled(filled_avg_price=alpaca_buy_order.filled_avg_price,
                              filled_qty=alpaca_buy_order.filled_qty)
            session.commit()
    return order

@router.get("/{id}")
def show_order(id: int, session: SessionDep) -> OrderPublic:
    order = session.get(Order, id)
    return order

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
    # my_file_log.append('syncing orders... total_orders=', total_orders)

    print('Total orders: ', total_orders)
    for order in orders:
        if order.alpaca_buy_order_id:
            alpaca_buy_order = alpaca_client.get_order_by_id(order.alpaca_buy_order_id)
        else:
            raise Exception('Order was created but no matching alpaca buy order')

        alpaca_sell_order: AlpacaOrder | None = None
        if order.alpaca_sell_order_id:
            alpaca_sell_order = alpaca_client.get_order_by_id(order.alpaca_sell_order_id)

        # my_file_log.append('working on order id=', order.id, 'status=', order.status, 'alpaca_status=', alpaca_buy_order.status, 'alpaca_sell_order=', bool(alpaca_sell_order))

        #NEW -> BUY_PENDING_NEW -> BUY_ACCEPTED -> BUY_FILLED -> SELL_PENDING_NEW -> SELL_ACCEPTED -> SELL_FILLED
        if order.status == VirtualOrderStatus.BUY_PENDING_NEW:
            print('the order id=', order.id, 'waiting for it to be filled. Nothing to do for now')
            if alpaca_buy_order.status == AlpacaOrderStatus.ACCEPTED:
                # my_file_log.append('the order id=', order.id, 'moving from buying to accepted')
                order.buy_accepted()
                session.commit()
            elif alpaca_buy_order.status == AlpacaOrderStatus.FILLED:
                # my_file_log.append('the order id=', order.id, 'moving from buying to filled')
                order.buy_accepted()
                session.commit()
                session.refresh(order)
                market_close_at = alpaca_client.get_next_close()
                order.buy_filled(filled_avg_price=alpaca_buy_order.filled_avg_price, buy_filled_qty=alpaca_buy_order.filled_qty, market_close_at=market_close_at)
                session.commit()
        elif order.status == VirtualOrderStatus.BUY_ACCEPTED:
            if alpaca_buy_order.status == AlpacaOrderStatus.ACCEPTED:
                print('the order id=', order.id, 'waiting for it to be filled. Nothing to do for now')
            elif alpaca_buy_order.status == AlpacaOrderStatus.FILLED:
                # my_file_log.append('the order id=', order.id, 'is moving from buying accepted buying to filled')
                market_close_at = alpaca_client.get_next_close()
                order.buy_filled(filled_avg_price=alpaca_buy_order.filled_avg_price, buy_filled_qty=alpaca_buy_order.filled_qty, market_close_at=market_close_at)
                session.commit()
        elif order.status == VirtualOrderStatus.BUY_FILLED:
            still_have_time = not alpaca_client.is_time_passed(order.force_sell_at)
            if still_have_time:
                # my_file_log.append('the order id=', order.id, 'was buy filled','but it is not time-passed', 'doing nothing')
                continue
            ######################################################
            try:
                alpaca_sell_order = alpaca_client.close_position(order.symbol)
                # my_file_log.append('the order id=', order.id, 'buy was filled', 'sell position not found', 'sending sell order -> buy_pending_new')
                order.sell_submitted(alpaca_order_id=alpaca_sell_order.id)
            except APIError as e:
                # my_file_log.append('the order id=', order.id, 'buy was filled', 'sell position arelady FOUND', 'skipping to sell filled')
                order.sell_submitted(alpaca_order_id=None)
                order.sell_accepted()
                order.sell_filled(filled_avg_price=0, filled_qty=0)

            session.commit()
            ############################################
        elif order.status == VirtualOrderStatus.SELL_PENDING_NEW:
            if alpaca_sell_order.status == AlpacaOrderStatus.ACCEPTED:
                # my_file_log.append('the order id=', order.id, 'sell order was accepted')
                order.sell_accepted()
                session.commit()
            elif alpaca_sell_order.status == AlpacaOrderStatus.FILLED:
                # my_file_log.append('the order id=', order.id, 'sell order was filled')
                order.sell_accepted()
                order.sell_filled(filled_avg_price=alpaca_buy_order.filled_avg_price, filled_qty=alpaca_buy_order.filled_qty)
                session.commit()




    return {"result": "success"}


@router.get("/hello")
def hello():
    return "Hello World"





