from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from alpaca.data import StockHistoricalDataClient
from alpaca.data.enums import DataFeed
from alpaca.data.live.crypto import CryptoDataStream
from alpaca.data.live.stock import StockDataStream
from alpaca.data.models.bars import Bar as AlpacaBar
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, OrderStatus, TimeInForce
from alpaca.trading.models import Clock as AlpacaClock
from alpaca.trading.models import Order as AlpacaOrder
from alpaca.trading.models import Position as AlpacaPosition
from alpaca.trading.requests import MarketOrderRequest

class MyAlpacaClient:
    def __init__(self, credentials: dict[str, Any]):
        self.credentials = credentials

        self.trading_client = TradingClient(
            api_key=credentials["api-key"],
            secret_key=credentials["secret-key"],
            paper=credentials["paper"],
        )
        self.data_client = StockHistoricalDataClient(
            api_key=credentials["api-key"],
            secret_key=credentials["secret-key"],
        )

        self.stocks_stream = StockDataStream(
            api_key=credentials["api-key"],
            secret_key=credentials["secret-key"],
            feed=DataFeed.IEX,
        )

        self.crypto_stream = CryptoDataStream(
            api_key=credentials["api-key"],
            secret_key=credentials["secret-key"],
        )

    def get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol"""
        request_params = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
        latest_quote = self.data_client.get_stock_latest_quote(request_params)
        return float(latest_quote[symbol].ask_price)

    def submit_buy_order(self, symbol: str, amount: float) -> AlpacaOrder:
        market_order = MarketOrderRequest(
            symbol=symbol,
            notional=amount,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )
        alpaca_order = self.trading_client.submit_order(market_order)
        assert isinstance(alpaca_order, AlpacaOrder)
        return alpaca_order

    def submit_sell_order(self, symbol: str, amount: float) -> AlpacaOrder:
        market_order = MarketOrderRequest(
            symbol=symbol,
            notional=amount,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        alpaca_order = self.trading_client.submit_order(market_order)
        assert isinstance(alpaca_order, AlpacaOrder)
        return alpaca_order

    def submit_liquidate_by_order(
        self, symbol: str, alpaca_order: AlpacaOrder
    ) -> AlpacaOrder:
        market_order = MarketOrderRequest(
            symbol=symbol,
            qty=alpaca_order.filled_qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        liquidate_order = self.trading_client.submit_order(market_order)
        assert isinstance(liquidate_order, AlpacaOrder)
        return liquidate_order

    def close_position(self, symbol: str) -> AlpacaOrder:
        alpaca_order = self.trading_client.close_position(symbol)
        assert isinstance(alpaca_order, AlpacaOrder)
        return alpaca_order

    def get_order_by_id(self, order_id: UUID) -> AlpacaOrder:
        """Get order by ID with automatic type conversion for numeric fields"""
        alpaca_order = self.trading_client.get_order_by_id(order_id)
        assert isinstance(alpaca_order, AlpacaOrder)

        # Convert string values to float and round to 4 decimal places
        if alpaca_order.filled_avg_price is not None:
            alpaca_order.filled_avg_price = round(
                float(alpaca_order.filled_avg_price), 4
            )

        if alpaca_order.filled_qty is not None:
            alpaca_order.filled_qty = round(float(alpaca_order.filled_qty), 4)

        return alpaca_order

    def get_position(self, symbol: str) -> AlpacaPosition:
        pos = self.trading_client.get_open_position(symbol)
        assert isinstance(pos, AlpacaPosition)
        return pos

    def get_next_close(self) -> datetime:
        """Get the next market close time in UTC"""
        clock = self.trading_client.get_clock()
        assert isinstance(clock, AlpacaClock)
        return clock.next_close.astimezone(timezone.utc)

    def get_next_open(self) -> datetime:
        """Get the next market close time in UTC"""
        clock = self.trading_client.get_clock()
        assert isinstance(clock, AlpacaClock)
        return clock.next_open.astimezone(timezone.utc)

    def get_current_time(self) -> datetime:
        clock = self.trading_client.get_clock()
        assert isinstance(clock, AlpacaClock)
        return clock.timestamp.astimezone(timezone.utc)

    def is_time_passed(self, time: datetime) -> bool:
        clock = self.trading_client.get_clock()
        assert isinstance(clock, AlpacaClock)
        current_time_utc = clock.timestamp.astimezone(timezone.utc)
        # If the input time is naive (no timezone), assume it's UTC
        assert time.tzinfo is None, "time to check is timezone-aware which is not good"
        time = time.replace(tzinfo=timezone.utc)

        return current_time_utc >= time

    def is_next_open_today(self) -> bool:
        clock = self.trading_client.get_clock()
        assert isinstance(clock, AlpacaClock)
        current_time_utc = clock.timestamp.astimezone(timezone.utc)
        next_open = clock.next_open.astimezone(timezone.utc)
        return next_open.date() == current_time_utc.date()

    def is_next_close_today(self) -> bool:
        clock = self.trading_client.get_clock()
        assert isinstance(clock, AlpacaClock)
        current_time_utc = clock.timestamp.astimezone(timezone.utc)
        next_close = clock.next_close.astimezone(timezone.utc)
        return next_close.date() == current_time_utc.date()

    def subscribe_bar_stocks(self, symbol: str, on_bar):
        stream = self.stocks_stream
        stream.subscribe_bars(on_bar, symbol)
        stream.run()

    def subscribe_bar_crypto(self, pair: str, on_bar):
        stream = self.crypto_stream
        stream.subscribe_bars(on_bar, pair)
        stream.run()



# AlpacaOrderStatus Is imported in other files. And it is more friendly to be imported from here and confused with the regular "order" status
AlpacaOrderStatus = OrderStatus
__all__ = ["MyAlpacaClient", "AlpacaOrderStatus", "AlpacaBar"]