from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Position:
    symbol: str
    side: str
    entry_price: float
    quantity: float
    leverage: int

    def unrealized_pnl(self, mark_price: float) -> float:
        if self.side == "LONG":
            return (mark_price - self.entry_price) * self.quantity * self.leverage
        return (self.entry_price - mark_price) * self.quantity * self.leverage


class Portfolio:
    def __init__(self, initial_equity: float) -> None:
        self.initial_equity = initial_equity
        self.realized_pnl = 0.0
        self.positions: Dict[str, Position] = {}

    def update_with_trade(self, symbol: str, side: str, price: float, quantity: float, leverage: int) -> float:
        pnl = 0.0
        if symbol in self.positions:
            position = self.positions[symbol]
            if position.side != side:
                pnl = position.unrealized_pnl(price)
                self.realized_pnl += pnl
                del self.positions[symbol]
            else:
                position.entry_price = (position.entry_price + price) / 2
                position.quantity += quantity
        else:
            self.positions[symbol] = Position(
                symbol=symbol,
                side=side,
                entry_price=price,
                quantity=quantity,
                leverage=leverage,
            )
        return pnl

    def total_equity(self, mark_prices: Dict[str, float]) -> float:
        unrealized = sum(
            position.unrealized_pnl(mark_prices.get(symbol, position.entry_price))
            for symbol, position in self.positions.items()
        )
        return self.initial_equity + self.realized_pnl + unrealized

    def unrealized_pnl(self, mark_prices: Dict[str, float]) -> float:
        return sum(
            position.unrealized_pnl(mark_prices.get(symbol, position.entry_price))
            for symbol, position in self.positions.items()
        )
