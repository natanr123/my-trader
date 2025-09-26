from alpaca.trading.client import TradingClient
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.models import Order as AlpacaOrder, Position as AlpacaPosition
from app.utils.key_reader import get_alpaca_credentials
from typing import Annotated
from fastapi import Depends
from datetime import datetime, timezone
from decimal import Decimal


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
    
    def get_order_by_id(self, order_id: str) -> AlpacaOrder:
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








def get_alpaca_client_live():
    # credentials = get_alpaca_credentials('alpaca_key_live.json')
    credentials = get_alpaca_credentials('alpaca_key_paper.json')
    return MyAlpacaClient(credentials)

def get_alpaca_client_paper():
    # credentials = get_alpaca_credentials('alpaca_key_live.json')
    credentials = get_alpaca_credentials('alpaca_key_paper.json')
    return MyAlpacaClient(credentials)


AlpacaDep = Annotated[MyAlpacaClient, Depends(get_alpaca_client_live)]


# id = UUID('ee28ab4e-cbbd-4c9d-a699-4d080a235a77')
# client_order_id = '203fa50a-fbe1-4844-a5f5-2cb06949282e'
# created_at = datetime.datetime(2025, 8, 26, 19, 33, 44, 495718, tzinfo=TzInfo(UTC))
# updated_at = datetime.datetime(2025, 8, 26, 19, 33, 44, 497458, tzinfo=TzInfo(UTC))
# submitted_at = datetime.datetime(2025, 8, 26, 19, 33, 44, 495718, tzinfo=TzInfo(UTC))
# filled_at = None
# expired_at = None
# expires_at = datetime.datetime(2025, 8, 26, 20, 0, tzinfo=TzInfo(UTC))
# canceled_at = None
# failed_at = None
# replaced_at = None
# replaced_by = None
# replaces = None
# asset_id = UUID('b0b6dd9d-8b9b-48a9-ba46-b9d54906e415')
# symbol = 'AAPL'
# asset_class = < AssetClass.US_EQUITY: 'us_equity' > notional = '100'
# qty = None
# filled_qty = '0'
# filled_avg_price = None
# order_class = < OrderClass.SIMPLE: 'simple' > order_type = < OrderType.MARKET: 'market' > type = < OrderType.MARKET: 'market' > side = < OrderSide.BUY: 'buy' > time_in_force = < TimeInForce.DAY: 'day' > limit_price = None
# stop_price = None
# status = < OrderStatus.PENDING_NEW: 'pending_new' > extended_hours = False
# legs = None
# trail_percent = None
# trail_price = None
# hwm = None
# position_intent = < PositionIntent.BUY_TO_OPEN: 'buy_to_open' > ratio_qty = None


# alpaca_order:  id=UUID('9744ebb1-4520-494c-9c1f-82989c14a8f8')
# client_order_id='2cce8360-b220-4e37-8945-7e6d0132a67e' created_at=datetime.datetime(2025, 8, 27, 17, 13, 56, 80575, tzinfo=TzInfo(UTC)) updated_at=datetime.datetime(2025, 8, 27, 17, 13, 56, 81044, tzinfo=TzInfo(UTC)) submitted_at=datetime.datetime(2025, 8, 27, 17, 13, 56, 80575, tzinfo=TzInfo(UTC)) filled_at=None expired_at=None expires_at=datetime.datetime(2025, 8, 27, 20, 0, tzinfo=TzInfo(UTC)) canceled_at=None failed_at=None replaced_at=None replaced_by=None replaces=None asset_id=UUID('b6d1aa75-5c9c-4353-a305-9e2caa1925ab') symbol='MSFT' asset_class=<AssetClass.US_EQUITY: 'us_equity'> notional=None qty='0.159048942' filled_qty='0' filled_avg_price=None order_class=<OrderClass.SIMPLE: 'simple'> order_type=<OrderType.MARKET: 'market'> type=<OrderType.MARKET: 'market'> side=<OrderSide.SELL: 'sell'> time_in_force=<TimeInForce.DAY: 'day'> limit_price=None stop_price=None
# status=<OrderStatus.PENDING_NEW: 'pending_new'> extended_hours=False legs=None trail_percent=None trail_price=None hwm=None position_intent=<PositionIntent.SELL_TO_CLOSE: 'sell_to_close'> ratio_qty=None

