from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta


@dataclass
class RiskLimits:
    daily_loss_limit_pct: float
    max_consecutive_losses: int
    cooldown_minutes: int


@dataclass
class RiskState:
    kill_switch: bool = False
    consecutive_losses: int = 0
    last_loss_time: datetime | None = None
    daily_pnl: float = 0.0
    day_start: datetime = datetime.now(timezone.utc)

    def reset_if_new_day(self) -> None:
        now = datetime.now(timezone.utc)
        if now.date() != self.day_start.date():
            self.daily_pnl = 0.0
            self.consecutive_losses = 0
            self.last_loss_time = None
            self.day_start = now


class RiskManager:
    def __init__(self, limits: RiskLimits, initial_equity: float) -> None:
        self.limits = limits
        self.initial_equity = initial_equity
        self.state = RiskState()

    def enable_kill_switch(self) -> None:
        self.state.kill_switch = True

    def disable_kill_switch(self) -> None:
        self.state.kill_switch = False

    def record_trade_pnl(self, pnl: float) -> None:
        self.state.reset_if_new_day()
        self.state.daily_pnl += pnl
        if pnl < 0:
            self.state.consecutive_losses += 1
            self.state.last_loss_time = datetime.now(timezone.utc)
        else:
            self.state.consecutive_losses = 0

    def is_in_cooldown(self) -> bool:
        if not self.state.last_loss_time:
            return False
        cooldown = timedelta(minutes=self.limits.cooldown_minutes)
        return datetime.now(timezone.utc) < self.state.last_loss_time + cooldown

    def daily_loss_limit_hit(self) -> bool:
        return self.state.daily_pnl <= -(self.initial_equity * self.limits.daily_loss_limit_pct)

    def can_trade(self) -> tuple[bool, str]:
        self.state.reset_if_new_day()
        if self.state.kill_switch:
            return False, "Kill switch enabled"
        if self.daily_loss_limit_hit():
            return False, "Daily loss limit reached"
        if self.state.consecutive_losses >= self.limits.max_consecutive_losses:
            if self.is_in_cooldown():
                return False, "Cooldown active after consecutive losses"
            return False, "Max consecutive losses reached"
        return True, "OK"
