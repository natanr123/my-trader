import os
from alpaca.data.live.stock import StockDataStream
from alpaca.data.enums import DataFeed  # IEX (free) or SIP (paid)
from app.api.deps.alpaca_dep import get_my_alpaca_client

# This will always hold the latest completed 1-minute bar for AMD
# latest_amd_bar = None



# async def on_amd_bar(bar):
#     """
#     bar is an alpaca.data.models.bars.Bar instance:
#     bar.timestamp, bar.open, bar.high, bar.low, bar.close, bar.volume, ...
#     :contentReference[oaicite:0]{index=0}
#     """
#     global latest_amd_bar
#     latest_amd_bar = bar
#
#     print(
#         f"New AMD 1m bar: "
#         f"{bar.timestamp} "
#         f"o={bar.open} h={bar.high} l={bar.low} c={bar.close} v={bar.volume}"
#     )
#
#
# def main():
#     # feed=DataFeed.IEX is the free tier; use DataFeed.SIP if you have that subscription.
#     stream = StockDataStream(
#         api_key=API_KEY,
#         secret_key=SECRET_KEY,
#         feed=DataFeed.IEX,
#     )
#
#     # Subscribe to *minute bars* for AMD over WebSocket :contentReference[oaicite:1]{index=1}
#     stream.subscribe_bars(on_amd_bar, "AMD")
#
#     # Blocking call – starts the event loop and keeps the WS connection open
#     stream.run()
#
#
# if __name__ == "__main__":
#     main()

my_alpaca_client = get_my_alpaca_client()

