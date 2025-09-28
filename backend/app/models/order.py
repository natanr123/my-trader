from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from transitions import Machine, EventData
from pydantic import PrivateAttr
from uuid import UUID
from app.models.soft_delete_mixin import SoftDeleteMixin
from app.utils.my_alpaca_client import AlpacaOrder, MyAlpacaClient, AlpacaOrderStatus
from alpaca.common.exceptions import APIError
from app.models.user import User

class VirtualOrderStatus(str, Enum):
    NEW = "new"
    BUY_PENDING_NEW = "buy_pending_new"
    BUY_ACCEPTED = "buy_accepted"
    BUY_FILLED = "buy_filled"
    SELL_PENDING_NEW = "sell_pending_new"
    SELL_ACCEPTED = "sell_accepted"
    SELL_FILLED = "sell_filled"

class OrderCore(SQLModel):
    symbol: str
    amount: float = Field(gt=0)

class OrderBase(SoftDeleteMixin, OrderCore):
    alpaca_buy_order_id: UUID | None = Field(
        default=None,
        index=True,
        sa_column_kwargs={"unique": True},  # make it globally unique
    )

    alpaca_sell_order_id: UUID | None = Field(
        default=None,
        index=True,
        sa_column_kwargs={"unique": True},  # make it globally unique
    )
    alpaca_client_order_id: Optional[str] = None
    symbol: str
    quantity: float = 0.0
    force_sell_at: Optional[datetime] = None
    buy_filled_avg_price: Optional[float] = None
    buy_filled_qty: Optional[float] = None
    sell_filled_avg_price: Optional[float] = None
    sell_filled_qty: Optional[float] = None
    target_profit_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    status: VirtualOrderStatus = Field(default=VirtualOrderStatus.NEW)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    filled_at: Optional[datetime] = None
    sold_at: Optional[datetime] = None
    error_message: Optional[str] = None

    _machine: Optional[Machine] = PrivateAttr(default=None)

class Order(OrderBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User = Relationship(back_populates="orders")

    def __init__(self, **data):
        super().__init__(**data)
        # Don't create machine here - delay until needed
        self._machine = None

    def buy_submitted(self, alpaca_order_id: UUID):
        self.alpaca_buy_order_id = alpaca_order_id
        self.machine.buy_submitted()

    def buy_accepted(self):
        self.machine.buy_accepted()

    def buy_filled(self, filled_avg_price: float, buy_filled_qty: float, market_close_at: datetime):
        self.buy_filled_avg_price = filled_avg_price
        self.buy_filled_qty = buy_filled_qty
        self.force_sell_at = market_close_at - timedelta(minutes=30)
        self.target_profit_price = filled_avg_price * 1.05
        self.stop_loss_price = filled_avg_price * 0.95
        self.machine.buy_filled()

    def sell_submitted(self, alpaca_order_id: UUID | None):
        self.alpaca_sell_order_id = alpaca_order_id
        self.machine.sell_submitted()

    def sell_accepted(self):
        self.machine.sell_accepted()

    def sell_filled(self, filled_avg_price: float, filled_qty: float):
        self.sell_filled_avg_price = filled_avg_price
        self.sell_filled_qty = filled_qty
        self.machine.sell_filled()

    def sync(self, alpaca_client: MyAlpacaClient):
        if self.alpaca_buy_order_id:
            alpaca_buy_order = alpaca_client.get_order_by_id(self.alpaca_buy_order_id)
        else:
            raise Exception('Order was created but no matching alpaca buy order')

        alpaca_sell_order: AlpacaOrder | None = None
        if self.alpaca_sell_order_id:
            alpaca_sell_order = alpaca_client.get_order_by_id(self.alpaca_sell_order_id)

        print('working on order id=', self.id, 'status=', self.status, 'alpaca_status=', alpaca_buy_order.status, 'alpaca_sell_order=', bool(alpaca_sell_order))

        # NEW -> BUY_PENDING_NEW -> BUY_ACCEPTED -> BUY_FILLED -> SELL_PENDING_NEW -> SELL_ACCEPTED -> SELL_FILLED
        match self.status:
            case VirtualOrderStatus.BUY_PENDING_NEW:
                if alpaca_buy_order.status == AlpacaOrderStatus.ACCEPTED:
                    self.buy_accepted()
                elif alpaca_buy_order.status == AlpacaOrderStatus.FILLED:
                    self.buy_accepted()
                    print('the order id=', self.id, 'moving from buying to filled')
                    market_close_at = alpaca_client.get_next_close()
                    self.buy_filled(filled_avg_price=alpaca_buy_order.filled_avg_price,
                                     buy_filled_qty=alpaca_buy_order.filled_qty, market_close_at=market_close_at)
            case VirtualOrderStatus.BUY_ACCEPTED:
                if alpaca_buy_order.status == AlpacaOrderStatus.ACCEPTED:
                    print('the order id=', self.id, 'waiting for it to be filled. Nothing to do for now')
                elif alpaca_buy_order.status == AlpacaOrderStatus.FILLED:
                    print('the order id=', self.id, 'is moving from buying accepted buying to filled')
                    market_close_at = alpaca_client.get_next_close()
                    self.buy_filled(filled_avg_price=alpaca_buy_order.filled_avg_price,
                                     buy_filled_qty=alpaca_buy_order.filled_qty, market_close_at=market_close_at)
            case VirtualOrderStatus.BUY_FILLED:
                sell_time_passed = alpaca_client.is_time_passed(self.force_sell_at)
                if sell_time_passed:
                    try:
                        alpaca_sell_order = alpaca_client.close_position(self.symbol)
                        # my_file_log.append('the order id=', order.id, 'buy was filled', 'sell position not found', 'sending sell order -> buy_pending_new')
                        self.sell_submitted(alpaca_order_id=alpaca_sell_order.id)
                    except APIError as e:
                        # my_file_log.append('the order id=', order.id, 'buy was filled', 'sell position arelady FOUND', 'skipping to sell filled')
                        self.sell_submitted(alpaca_order_id=None)
                        self.sell_accepted()
                        self.sell_filled(filled_avg_price=0, filled_qty=0)
                else:
                    print('the order id=', self.id, 'was buy filled', 'but it is not time-passed', 'doing nothing')
            case VirtualOrderStatus.SELL_PENDING_NEW:
                if alpaca_sell_order.status == AlpacaOrderStatus.ACCEPTED:
                    # my_file_log.append('the order id=', order.id, 'sell order was accepted')
                    self.sell_accepted()
                elif alpaca_sell_order.status == AlpacaOrderStatus.FILLED:
                    # my_file_log.append('the order id=', order.id, 'sell order was filled')
                    self.sell_accepted()
                    self.sell_filled(filled_avg_price=alpaca_buy_order.filled_avg_price,
                                      filled_qty=alpaca_buy_order.filled_qty)


    @staticmethod
    def create_machine(model) -> Machine:

        class MyMachine(Machine):
            def after_state_changed(self, event: EventData):
                self._model.status = event.state.value
                print('model status was updated to ',event.state.name)

            def set_model(self, model):
                self._model = model

        transitions_def = [
            {"trigger": "buy_submitted", "source": VirtualOrderStatus.NEW, "dest": VirtualOrderStatus.BUY_PENDING_NEW},
            {"trigger": "buy_accepted", "source": VirtualOrderStatus.BUY_PENDING_NEW, "dest": VirtualOrderStatus.BUY_ACCEPTED},
            {"trigger": "buy_filled", "source": VirtualOrderStatus.BUY_ACCEPTED, "dest": VirtualOrderStatus.BUY_FILLED},
            {"trigger": "sell_submitted", "source": VirtualOrderStatus.BUY_FILLED, "dest": VirtualOrderStatus.SELL_PENDING_NEW},
            {"trigger": "sell_accepted", "source": VirtualOrderStatus.SELL_PENDING_NEW, "dest": VirtualOrderStatus.SELL_ACCEPTED},
            {"trigger": "sell_filled", "source": VirtualOrderStatus.SELL_ACCEPTED, "dest": VirtualOrderStatus.SELL_FILLED},
        ]
        m = MyMachine(states=VirtualOrderStatus, transitions=transitions_def, initial=model.status, send_event=True, after_state_change='after_state_changed')
        m.set_model(model)
        return m

    @property
    def machine(self) -> Machine:
        if self._machine is None:
            self._machine = Order.create_machine(self)
        return self._machine

class OrderCreate(OrderCore):
    model_config = {"extra": "forbid"}

class OrderPublic(OrderBase):
    id: int





