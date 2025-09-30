import logging
from dataclasses import dataclass

from alpaca.common.exceptions import APIError
from sqlmodel import Session

from app.clients.my_alpaca_client import AlpacaOrder, AlpacaOrderStatus, MyAlpacaClient
from app.models.order import Order, OrderCreate, VirtualOrderStatus
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class OrderSyncData:
    buy_order: AlpacaOrder
    sell_order: AlpacaOrder | None

    def get_buy_order_filled_avg_price(self) -> float:
        assert isinstance(self.buy_order.filled_avg_price, float)
        return self.buy_order.filled_avg_price

    def get_buy_order_filled_qty(self) -> float:
        assert isinstance(self.buy_order.filled_qty, float)
        return self.buy_order.filled_qty

    def get_sell_order_filled_avg_price(self) -> float:
        assert self.sell_order is not None
        assert isinstance(self.sell_order.filled_avg_price, float)
        return self.sell_order.filled_avg_price

    def get_sell_order_filled_qty(self) -> float:
        assert self.sell_order is not None
        assert isinstance(self.sell_order.filled_qty, float)
        return self.sell_order.filled_qty

class OrderCrud:
    @classmethod
    def _fetch_order_data(cls, order: Order, alpaca_client: MyAlpacaClient) -> OrderSyncData:
        if not order.alpaca_buy_order_id:
            raise Exception('Order was created but no matching alpaca buy order')

        buy_order = alpaca_client.get_order_by_id(order.alpaca_buy_order_id)
        sell_order = None
        if order.alpaca_sell_order_id:
            sell_order = alpaca_client.get_order_by_id(order.alpaca_sell_order_id)

        return OrderSyncData(buy_order=buy_order, sell_order=sell_order)

    @classmethod
    def _handle_buy_pending_new(cls, order: Order, sync_data: OrderSyncData, alpaca_client: MyAlpacaClient):
        if sync_data.buy_order.status == AlpacaOrderStatus.ACCEPTED:
            order.buy_accepted()
        elif sync_data.buy_order.status == AlpacaOrderStatus.FILLED:
            logger.info('Order id=%s moving from buying to filled', order.id)
            market_close_at = alpaca_client.get_next_close()
            order.buy_filled(filled_avg_price=sync_data.get_buy_order_filled_avg_price(),
                           buy_filled_qty=sync_data.get_buy_order_filled_qty(), market_close_at=market_close_at)

    @classmethod
    def _handle_buy_accepted(cls, order: Order, sync_data: OrderSyncData, alpaca_client: MyAlpacaClient):
        if sync_data.buy_order.status == AlpacaOrderStatus.ACCEPTED:
            logger.info('Order id=%s waiting for it to be filled. Nothing to do for now', order.id)
        elif sync_data.buy_order.status == AlpacaOrderStatus.FILLED:
            logger.info('Order id=%s is moving from buying accepted buying to filled', order.id)
            market_close_at = alpaca_client.get_next_close()
            order.buy_filled(filled_avg_price=sync_data.get_buy_order_filled_avg_price(),
                           buy_filled_qty=sync_data.get_buy_order_filled_qty(), market_close_at=market_close_at)

    @classmethod
    def _handle_sell_pending_new(cls, order: Order, sync_data: OrderSyncData):
        if not sync_data.sell_order:
            raise Exception('Order in sell_pending_new but no matching alpaca sell order')

        if sync_data.sell_order.status == AlpacaOrderStatus.ACCEPTED:
            order.sell_accepted()
        elif sync_data.sell_order.status == AlpacaOrderStatus.FILLED:
            order.sell_filled(filled_avg_price=sync_data.get_sell_order_filled_avg_price(),
                            filled_qty=sync_data.get_sell_order_filled_qty())

    @classmethod
    def apply_sell_rules(cls, order: Order, alpaca_client: MyAlpacaClient):
        logger.info('apply_sell_rules order id=%s status=%s', order.id, order.status)
        if order.status == VirtualOrderStatus.BUY_FILLED:
            assert order.force_sell_at is not None
            sell_time_passed = alpaca_client.is_time_passed(order.force_sell_at)
            if sell_time_passed:
                try:
                    alpaca_sell_order = alpaca_client.close_position(order.symbol)
                    order.sell_submitted(alpaca_order_id=alpaca_sell_order.id)
                except APIError:
                    order.sell_failed()
            else:
                logger.info('Order id=%s was buy filled but it is not time-passed, doing nothing', order.id)

    @classmethod
    def sync_order_status(cls, order: Order, alpaca_client: MyAlpacaClient):
        sync_data = cls._fetch_order_data(order, alpaca_client)
        logger.info('Working on order id=%s status=%s alpaca_status=%s alpaca_sell_order=%s user_email=%s',
                    order.id, order.status, sync_data.buy_order.status, bool(sync_data.sell_order), order.owner.email)

        # NEW -> BUY_PENDING_NEW -> BUY_ACCEPTED -> BUY_FILLED -> SELL_PENDING_NEW -> SELL_ACCEPTED -> SELL_FILLED
        match order.status:
            case VirtualOrderStatus.BUY_PENDING_NEW:
                cls._handle_buy_pending_new(order, sync_data, alpaca_client)
            case VirtualOrderStatus.BUY_ACCEPTED:
                cls._handle_buy_accepted(order, sync_data, alpaca_client)
            case VirtualOrderStatus.SELL_PENDING_NEW:
                cls._handle_sell_pending_new(order, sync_data)

    @classmethod
    def create_order_with_alpaca_order(cls, user: User, order_in: OrderCreate, session: Session, alpaca_client: MyAlpacaClient) -> Order:
        alpaca_order = alpaca_client.submit_buy_order(order_in.symbol, order_in.amount)
        order = Order.model_validate(order_in, update={"owner_id": user.id})
        order.buy_submitted(alpaca_order_id=alpaca_order.id)
        session.add(order)
        session.commit()
        session.refresh(order)
        return order
