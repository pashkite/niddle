from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .strategy_base import Signal


@dataclass
class EMAStrategy:
    fast_period: int
    slow_period: int

    def generate_signals(self, symbol: str, prices: List[float]) -> List[Signal]:
        if len(prices) < self.slow_period + 2:
            return []

        fast = self._ema_series(prices, self.fast_period)
        slow = self._ema_series(prices, self.slow_period)

        if len(fast) < 2 or len(slow) < 2:
            return []

        prev_fast, curr_fast = fast[-2], fast[-1]
        prev_slow, curr_slow = slow[-2], slow[-1]

        if prev_fast <= prev_slow and curr_fast > curr_slow:
            return [Signal(symbol=symbol, side="BUY", reason="EMA bullish crossover")]
        if prev_fast >= prev_slow and curr_fast < curr_slow:
            return [Signal(symbol=symbol, side="SELL", reason="EMA bearish crossover")]
        return []

    @staticmethod
    def _ema_series(prices: List[float], period: int) -> List[float]:
        multiplier = 2 / (period + 1)
        ema_values: List[float] = []
        for i, price in enumerate(prices):
            if i == 0:
                ema_values.append(price)
            else:
                ema_values.append((price - ema_values[-1]) * multiplier + ema_values[-1])
        return ema_values
