from sqlmodel import Session

from app.models.order import Order
from app.models.order import OrderCreate
from app.clients.my_alpaca_client import MyAlpacaClient, AlpacaOrder, AlpacaOrderStatus
from app.models.user import User
from app.models.order import VirtualOrderStatus
from alpaca.common.exceptions import APIError

class OrderService:
    def create_order_with_alpaca_order(self, user: User, order_in: OrderCreate, session: Session, alpaca_client: MyAlpacaClient) -> Order:
        alpaca_order = alpaca_client.submit_buy_order(order_in.symbol, order_in.amount)
        order = Order.model_validate(order_in, update={"owner_id": user.id})
        order.buy_submitted(alpaca_order_id=alpaca_order.id)
        session.add(order)
        session.commit()
        session.refresh(order)
        return order

    def sync_order(self, order: Order, alpaca_client: MyAlpacaClient):
        if order.alpaca_buy_order_id:
            alpaca_buy_order = alpaca_client.get_order_by_id(order.alpaca_buy_order_id)
        else:
            raise Exception('Order was created but no matching alpaca buy order')

        alpaca_sell_order: AlpacaOrder | None = None
        if order.alpaca_sell_order_id:
            alpaca_sell_order = alpaca_client.get_order_by_id(order.alpaca_sell_order_id)

        print('working on order id=', order.id, 'status=', order.status, 'alpaca_status=', alpaca_buy_order.status, 'alpaca_sell_order=', bool(alpaca_sell_order))

        # NEW -> BUY_PENDING_NEW -> BUY_ACCEPTED -> BUY_FILLED -> SELL_PENDING_NEW -> SELL_ACCEPTED -> SELL_FILLED
        match order.status:
            case VirtualOrderStatus.BUY_PENDING_NEW:
                if alpaca_buy_order.status == AlpacaOrderStatus.ACCEPTED:
                    order.buy_accepted()
                elif alpaca_buy_order.status == AlpacaOrderStatus.FILLED:
                    order.buy_accepted()
                    print('the order id=', order.id, 'moving from buying to filled')
                    market_close_at = alpaca_client.get_next_close()
                    order.buy_filled(filled_avg_price=alpaca_buy_order.filled_avg_price,
                                     buy_filled_qty=alpaca_buy_order.filled_qty, market_close_at=market_close_at)
            case VirtualOrderStatus.BUY_ACCEPTED:
                if alpaca_buy_order.status == AlpacaOrderStatus.ACCEPTED:
                    print('the order id=', order.id, 'waiting for it to be filled. Nothing to do for now')
                elif alpaca_buy_order.status == AlpacaOrderStatus.FILLED:
                    print('the order id=', order.id, 'is moving from buying accepted buying to filled')
                    market_close_at = alpaca_client.get_next_close()
                    order.buy_filled(filled_avg_price=alpaca_buy_order.filled_avg_price,
                                     buy_filled_qty=alpaca_buy_order.filled_qty, market_close_at=market_close_at)
            case VirtualOrderStatus.BUY_FILLED:
                sell_time_passed = alpaca_client.is_time_passed(order.force_sell_at)
                if sell_time_passed:
                    try:
                        alpaca_sell_order = alpaca_client.close_position(order.symbol)
                        # my_file_log.append('the order id=', order.id, 'buy was filled', 'sell position not found', 'sending sell order -> buy_pending_new')
                        order.sell_submitted(alpaca_order_id=alpaca_sell_order.id)
                    except APIError as e:
                        # my_file_log.append('the order id=', order.id, 'buy was filled', 'sell position arelady FOUND', 'skipping to sell filled')
                        order.sell_submitted(alpaca_order_id=None)
                        order.sell_accepted()
                        order.sell_filled(filled_avg_price=0, filled_qty=0)
                else:
                    print('the order id=', order.id, 'was buy filled', 'but it is not time-passed', 'doing nothing')
            case VirtualOrderStatus.SELL_PENDING_NEW:
                if alpaca_sell_order.status == AlpacaOrderStatus.ACCEPTED:
                    # my_file_log.append('the order id=', order.id, 'sell order was accepted')
                    order.sell_accepted()
                elif alpaca_sell_order.status == AlpacaOrderStatus.FILLED:
                    # my_file_log.append('the order id=', order.id, 'sell order was filled')
                    order.sell_accepted()
                    order.sell_filled(filled_avg_price=alpaca_buy_order.filled_avg_price,
                                      filled_qty=alpaca_buy_order.filled_qty)
