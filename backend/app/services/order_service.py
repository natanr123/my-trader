from sqlmodel import Session
from dataclasses import dataclass

from app.models.order import Order
from app.models.order import OrderCreate
from app.clients.my_alpaca_client import MyAlpacaClient, AlpacaOrder, AlpacaOrderStatus
from app.models.user import User
from app.models.order import VirtualOrderStatus
from alpaca.common.exceptions import APIError

@dataclass
class OrderSyncData:
    buy_order: AlpacaOrder
    sell_order: AlpacaOrder | None

def _log_order_status(order: Order, sync_data: OrderSyncData):
    print('working on order id=', order.id, 'status=', order.status, 'alpaca_status=', sync_data.buy_order.status, 'alpaca_sell_order=', bool(sync_data.sell_order))

class OrderService:
    def _fetch_order_data(self, order: Order, alpaca_client: MyAlpacaClient) -> OrderSyncData:
        if not order.alpaca_buy_order_id:
            raise Exception('Order was created but no matching alpaca buy order')

        buy_order = alpaca_client.get_order_by_id(order.alpaca_buy_order_id)
        sell_order = None
        if order.alpaca_sell_order_id:
            sell_order = alpaca_client.get_order_by_id(order.alpaca_sell_order_id)

        return OrderSyncData(buy_order=buy_order, sell_order=sell_order)

    def _handle_buy_pending_new(self, order: Order, sync_data: OrderSyncData, alpaca_client: MyAlpacaClient):
        if sync_data.buy_order.status == AlpacaOrderStatus.ACCEPTED:
            order.buy_accepted()
        elif sync_data.buy_order.status == AlpacaOrderStatus.FILLED:
            print('the order id=', order.id, 'moving from buying to filled')
            market_close_at = alpaca_client.get_next_close()
            order.buy_filled(filled_avg_price=sync_data.buy_order.filled_avg_price,
                           buy_filled_qty=sync_data.buy_order.filled_qty, market_close_at=market_close_at)

    def _handle_buy_accepted(self, order: Order, sync_data: OrderSyncData, alpaca_client: MyAlpacaClient):
        if sync_data.buy_order.status == AlpacaOrderStatus.ACCEPTED:
            print('the order id=', order.id, 'waiting for it to be filled. Nothing to do for now')
        elif sync_data.buy_order.status == AlpacaOrderStatus.FILLED:
            print('the order id=', order.id, 'is moving from buying accepted buying to filled')
            market_close_at = alpaca_client.get_next_close()
            order.buy_filled(filled_avg_price=sync_data.buy_order.filled_avg_price,
                           buy_filled_qty=sync_data.buy_order.filled_qty, market_close_at=market_close_at)

    def _handle_sell_pending_new(self, order: Order, sync_data: OrderSyncData):
        if sync_data.sell_order and sync_data.sell_order.status == AlpacaOrderStatus.ACCEPTED:
            order.sell_accepted()
        elif sync_data.sell_order and sync_data.sell_order.status == AlpacaOrderStatus.FILLED:
            order.sell_filled(filled_avg_price=sync_data.sell_order.filled_avg_price,
                            filled_qty=sync_data.sell_order.filled_qty)

    def apply_sell_rules(self, order: Order, alpaca_client: MyAlpacaClient):
        if order.status == VirtualOrderStatus.BUY_FILLED:
            sell_time_passed = alpaca_client.is_time_passed(order.force_sell_at)
            if sell_time_passed:
                try:
                    alpaca_sell_order = alpaca_client.close_position(order.symbol)
                    order.sell_submitted(alpaca_order_id=alpaca_sell_order.id)
                except APIError:
                    order.sell_failed()
            else:
                print('the order id=', order.id, 'was buy filled', 'but it is not time-passed', 'doing nothing')

    def sync_order_status(self, order: Order, alpaca_client: MyAlpacaClient):
        sync_data = self._fetch_order_data(order, alpaca_client)
        _log_order_status(order, sync_data)

        # NEW -> BUY_PENDING_NEW -> BUY_ACCEPTED -> BUY_FILLED -> SELL_PENDING_NEW -> SELL_ACCEPTED -> SELL_FILLED
        match order.status:
            case VirtualOrderStatus.BUY_PENDING_NEW:
                self._handle_buy_pending_new(order, sync_data, alpaca_client)
            case VirtualOrderStatus.BUY_ACCEPTED:
                self._handle_buy_accepted(order, sync_data, alpaca_client)
            case VirtualOrderStatus.SELL_PENDING_NEW:
                self._handle_sell_pending_new(order, sync_data)



    def create_order_with_alpaca_order(self, user: User, order_in: OrderCreate, session: Session, alpaca_client: MyAlpacaClient) -> Order:
        alpaca_order = alpaca_client.submit_buy_order(order_in.symbol, order_in.amount)
        order = Order.model_validate(order_in, update={"owner_id": user.id})
        order.buy_submitted(alpaca_order_id=alpaca_order.id)
        session.add(order)
        session.commit()
        session.refresh(order)
        return order
