from alpaca.trading.client import TradingClient
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.models import Order as AlpacaOrder, Position as AlpacaPosition
from datetime import datetime, timezone
from uuid import UUID

from alpaca.trading.models import OrderStatus as AlpacaOrderStatus

class MyAlpacaClient:
    def __init__(self, credentials: dict[str, str | bool]):
        self.credentials = credentials

        self.trading_client = TradingClient(
            api_key=credentials['api-key'],
            secret_key=credentials['secret-key'],
            paper=credentials['paper'],
        )
        self.data_client = StockHistoricalDataClient(
            api_key=credentials['api-key'],
            secret_key=credentials['secret-key'],
        )

    def get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol"""
        request_params = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
        latest_quote = self.data_client.get_stock_latest_quote(request_params)
        return float(latest_quote[symbol].ask_price)

    def submit_buy_order(self, symbol: str , amount: float) -> AlpacaOrder:
        market_order = MarketOrderRequest(
            symbol=symbol,
            notional=amount,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )
        alpaca_order = self.trading_client.submit_order(market_order)
        return alpaca_order

    def submit_sell_order(self, symbol: str , amount: float) -> AlpacaOrder:
        market_order = MarketOrderRequest(
            symbol=symbol,
            notional=amount,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        alpaca_order = self.trading_client.submit_order(market_order)
        return alpaca_order

    def submit_liquidate_by_order(self, symbol: str, alpaca_order: AlpacaOrder) -> AlpacaOrder:
        market_order = MarketOrderRequest(
            symbol=symbol,
            qty=alpaca_order.filled_qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        alpaca_order = self.trading_client.submit_order(market_order)
        return alpaca_order

    def close_position(self, symbol: str) -> AlpacaOrder:
        alpaca_order = self.trading_client.close_position(symbol)
        return alpaca_order
    
    def get_order_by_id(self, order_id: UUID) -> AlpacaOrder:
        """Get order by ID with automatic type conversion for numeric fields"""
        alpaca_order = self.trading_client.get_order_by_id(order_id)
        
        # Convert string values to float and round to 4 decimal places
        if alpaca_order.filled_avg_price is not None:
            alpaca_order.filled_avg_price = round(float(alpaca_order.filled_avg_price), 4)
        
        if alpaca_order.filled_qty is not None:
            alpaca_order.filled_qty = round(float(alpaca_order.filled_qty), 4)
            
        return alpaca_order

    def get_position(self, symbol: str) -> AlpacaPosition:
        pos = self.trading_client.get_open_position(symbol)
        return pos
    
    def get_next_close(self) -> datetime:
        """Get the next market close time in UTC"""
        clock = self.trading_client.get_clock()
        return clock.next_close.astimezone(timezone.utc)

    def get_next_open(self) -> datetime:
        """Get the next market close time in UTC"""
        clock = self.trading_client.get_clock()
        return clock.next_open.astimezone(timezone.utc)

    def get_current_time(self) -> datetime:
        clock = self.trading_client.get_clock()
        return clock.timestamp.astimezone(timezone.utc)

    def is_time_passed(self, time: datetime) -> bool:
        clock = self.trading_client.get_clock()
        current_time_utc = clock.timestamp.astimezone(timezone.utc)
        # If the input time is naive (no timezone), assume it's UTC
        assert time.tzinfo is None, 'time to check is timezone-aware which is not good'
        time = time.replace(tzinfo=timezone.utc)
            
        return current_time_utc >= time

    def is_next_open_today(self) -> bool:
        clock = self.trading_client.get_clock()
        current_time_utc = clock.timestamp.astimezone(timezone.utc)
        next_open = clock.next_open.astimezone(timezone.utc)
        return next_open.date() == current_time_utc.date()

    def is_next_close_today(self) -> bool:
        clock = self.trading_client.get_clock()
        current_time_utc = clock.timestamp.astimezone(timezone.utc)
        next_close = clock.next_close.astimezone(timezone.utc)
        return next_close.date() == current_time_utc.date()




