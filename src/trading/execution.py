from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional

from binance.exceptions import BinanceAPIException

from core.storage import OrderRecord, TradeRecord, Storage
from exchange.binance_client import BinanceClient


@dataclass
class OrderRequest:
    symbol: str
    side: str
    quantity: float
    price: float


class ExecutionEngine:
    def __init__(self, mode: str, slippage_pct: float, client: BinanceClient, storage: Storage) -> None:
        self.mode = mode
        self.slippage_pct = slippage_pct
        self.client = client
        self.storage = storage

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def submit_order(self, order: OrderRequest) -> Optional[TradeRecord]:
        order_id = str(uuid.uuid4())
        if self.mode == "paper":
            filled_price = order.price * (1 + self.slippage_pct if order.side == "BUY" else 1 - self.slippage_pct)
            self.storage.record_order(
                OrderRecord(
                    timestamp=self._utc_now(),
                    order_id=order_id,
                    symbol=order.symbol,
                    side=order.side,
                    status="FILLED",
                    price=filled_price,
                    quantity=order.quantity,
                    filled_qty=order.quantity,
                    mode=self.mode,
                    metadata={},
                )
            )
            trade = TradeRecord(
                timestamp=self._utc_now(),
                trade_id=str(uuid.uuid4()),
                order_id=order_id,
                symbol=order.symbol,
                side=order.side,
                price=filled_price,
                quantity=order.quantity,
                pnl=0.0,
                mode=self.mode,
                metadata={},
            )
            self.storage.record_trade(trade)
            return trade

        try:
            response = self.client.client.futures_create_order(
                symbol=order.symbol,
                side=order.side,
                type="MARKET",
                quantity=order.quantity,
            )
            self.storage.record_order(
                OrderRecord(
                    timestamp=self._utc_now(),
                    order_id=str(response.get("orderId")),
                    symbol=order.symbol,
                    side=order.side,
                    status=response.get("status", "UNKNOWN"),
                    price=float(response.get("avgPrice", order.price)),
                    quantity=float(response.get("origQty", order.quantity)),
                    filled_qty=float(response.get("executedQty", 0)),
                    mode=self.mode,
                    metadata=response,
                )
            )
        except BinanceAPIException as exc:
            self.storage.record_event("ERROR", "ORDER_FAIL", str(exc), {"symbol": order.symbol})
            return None

        return None
