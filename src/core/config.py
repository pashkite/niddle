from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass
class StrategyConfig:
    name: str
    fast_period: int
    slow_period: int


@dataclass
class LoggingConfig:
    level: str
    dir: str


@dataclass
class StorageConfig:
    path: str


@dataclass
class RiskConfig:
    kill_switch_close_positions: bool


@dataclass
class AppConfig:
    mode: str
    allow_live: bool
    symbols: List[str]
    leverage: int
    position_size_pct: float
    max_symbol_exposure_pct: float
    sl_pct: float
    tp_pct: float
    trailing_stop_pct: float
    slippage_pct: float
    daily_loss_limit_pct: float
    max_consecutive_losses: int
    cooldown_minutes: int
    poll_interval_seconds: int
    initial_equity: float
    strategy: StrategyConfig
    logging: LoggingConfig
    storage: StorageConfig
    risk: RiskConfig

    def ensure_safe_mode(self) -> None:
        if self.mode not in {"paper", "testnet", "live"}:
            raise ValueError(f"Unsupported mode: {self.mode}")
        if self.mode == "live" and not self.allow_live:
            raise ValueError("Live mode is disabled by default. Set allow_live=true to proceed.")


DEFAULT_CONFIG_PATH = Path("config.yaml")


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    raw: Dict[str, Any] = yaml.safe_load(config_path.read_text())
    strategy = StrategyConfig(**raw.get("strategy", {}))
    logging_cfg = LoggingConfig(**raw.get("logging", {}))
    storage_cfg = StorageConfig(**raw.get("storage", {}))
    risk_cfg = RiskConfig(**raw.get("risk", {}))

    cfg = AppConfig(
        mode=raw.get("mode", "paper"),
        allow_live=bool(raw.get("allow_live", False)),
        symbols=raw.get("symbols", []),
        leverage=int(raw.get("leverage", 1)),
        position_size_pct=float(raw.get("position_size_pct", 0.1)),
        max_symbol_exposure_pct=float(raw.get("max_symbol_exposure_pct", 0.2)),
        sl_pct=float(raw.get("sl_pct", 0.01)),
        tp_pct=float(raw.get("tp_pct", 0.02)),
        trailing_stop_pct=float(raw.get("trailing_stop_pct", 0.0)),
        slippage_pct=float(raw.get("slippage_pct", 0.0)),
        daily_loss_limit_pct=float(raw.get("daily_loss_limit_pct", 0.05)),
        max_consecutive_losses=int(raw.get("max_consecutive_losses", 3)),
        cooldown_minutes=int(raw.get("cooldown_minutes", 30)),
        poll_interval_seconds=int(raw.get("poll_interval_seconds", 5)),
        initial_equity=float(raw.get("initial_equity", 10000)),
        strategy=strategy,
        logging=logging_cfg,
        storage=storage_cfg,
        risk=risk_cfg,
    )
    return cfg
