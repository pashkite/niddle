from __future__ import annotations

from dataclasses import dataclass
from typing import List, Protocol


@dataclass
class Signal:
    symbol: str
    side: str  # BUY or SELL
    reason: str


class Strategy(Protocol):
    def generate_signals(self, symbol: str, prices: List[float]) -> List[Signal]:
        ...
