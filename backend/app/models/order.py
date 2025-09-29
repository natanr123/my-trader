from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from transitions import Machine, EventData
from pydantic import PrivateAttr
from uuid import UUID
from app.models.soft_delete_mixin import SoftDeleteMixin
from app.models.user import User

class VirtualOrderStatus(str, Enum):
    NEW = "new"
    BUY_PENDING_NEW = "buy_pending_new"
    BUY_ACCEPTED = "buy_accepted"
    BUY_FILLED = "buy_filled"
    SELL_PENDING_NEW = "sell_pending_new"
    SELL_ACCEPTED = "sell_accepted"
    SELL_FILLED = "sell_filled"
    SELL_FAILED = "sell_failed"

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
        if self.status == VirtualOrderStatus.BUY_PENDING_NEW:
            self.buy_accepted()
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
        if self.status == VirtualOrderStatus.SELL_PENDING_NEW:
            self.sell_accepted()
        self.sell_filled_avg_price = filled_avg_price
        self.sell_filled_qty = filled_qty
        self.machine.sell_filled()

    def sell_failed(self):
        self.machine.sell_failed()



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
            {"trigger": "sell_failed", "source": VirtualOrderStatus.BUY_FILLED, "dest": VirtualOrderStatus.SELL_FAILED},
            {"trigger": "sell_accepted", "source": VirtualOrderStatus.SELL_PENDING_NEW, "dest": VirtualOrderStatus.SELL_ACCEPTED},
            {"trigger": "sell_filled", "source": VirtualOrderStatus.SELL_ACCEPTED, "dest": VirtualOrderStatus.SELL_FILLED},
        ]
        m = MyMachine(states=VirtualOrderStatus, transitions=transitions_def, initial=model.status, send_event=True, after_state_change='after_state_changed')
        m.set_model(model)
        return m

    @property
    def machine(self) -> Machine:
        # Ensure __pydantic_private__ exists for instances loaded from DB
        if not hasattr(self, '__pydantic_private__') or self.__pydantic_private__ is None:
            self.__pydantic_private__ = {}

        # Handle case where _machine doesn't exist (loaded from DB) or is None (new instance)
        if getattr(self, '_machine', None) is None:
            self._machine = Order.create_machine(self)
        return self._machine

class OrderCreate(OrderCore):
    model_config = {"extra": "forbid"}

class OrderPublic(OrderBase):
    id: int





