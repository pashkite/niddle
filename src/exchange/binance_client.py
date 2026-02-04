from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from binance.client import Client
from tenacity import retry, stop_after_attempt, wait_exponential


@dataclass
class MarketPrice:
    symbol: str
    price: float


class BinanceClient:
    def __init__(self, mode: str) -> None:
        self.mode = mode
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")

        if mode == "testnet":
            self.client = Client(api_key, api_secret, testnet=True)
        elif mode == "live":
            self.client = Client(api_key, api_secret)
        else:
            self.client = Client()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    def get_latest_price(self, symbol: str) -> MarketPrice:
        ticker = self.client.futures_symbol_ticker(symbol=symbol)
        return MarketPrice(symbol=symbol, price=float(ticker["price"]))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    def fetch_positions(self) -> List[Dict[str, str]]:
        if self.mode == "paper":
            return []
        return self.client.futures_position_information()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=5))
    def cancel_open_orders(self, symbol: Optional[str] = None) -> None:
        if self.mode == "paper":
            return
        if symbol:
            self.client.futures_cancel_all_open_orders(symbol=symbol)
        else:
            for order in self.client.futures_get_open_orders():
                self.client.futures_cancel_order(symbol=order["symbol"], orderId=order["orderId"])
