from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

from core.clock import Clock
from core.config import AppConfig, load_config
from core.logger import setup_logger
from core.storage import EquityRecord, Storage
from exchange.binance_client import BinanceClient
from trading.execution import ExecutionEngine, OrderRequest
from trading.portfolio import Portfolio
from trading.risk import RiskLimits, RiskManager
from trading.strategy_ema import EMAStrategy

CONTROL_DIR = Path("control")
KILL_SWITCH_FILE = CONTROL_DIR / "kill_switch.flag"
STOP_FILE = CONTROL_DIR / "stop.flag"


def load_prices(client: BinanceClient, symbols: List[str]) -> Dict[str, float]:
    prices: Dict[str, float] = {}
    for symbol in symbols:
        prices[symbol] = client.get_latest_price(symbol).price
    return prices


def sync_positions_or_halt(config: AppConfig, client: BinanceClient, storage: Storage, logger) -> bool:
    if config.mode == "paper":
        return True
    positions = client.fetch_positions()
    open_positions = [p for p in positions if float(p.get("positionAmt", 0)) != 0]
    if open_positions:
        storage.record_event(
            "WARN",
            "SYNC",
            "Open positions detected on startup. Halting for safety.",
            {"positions": open_positions},
        )
        logger.warning("Open positions detected on startup. Halting for safety.")
        return False
    return True


def update_kill_switch(risk: RiskManager) -> None:
    if KILL_SWITCH_FILE.exists():
        risk.enable_kill_switch()
    else:
        risk.disable_kill_switch()


def should_stop() -> bool:
    return STOP_FILE.exists()


def run_engine(config_path: str) -> None:
    load_dotenv()
    config = load_config(config_path)
    config.ensure_safe_mode()

    logger = setup_logger("engine", config.logging.level, config.logging.dir)
    storage = Storage(config.storage.path)
    client = BinanceClient(config.mode)

    if not sync_positions_or_halt(config, client, storage, logger):
        return

    risk = RiskManager(
        RiskLimits(
            daily_loss_limit_pct=config.daily_loss_limit_pct,
            max_consecutive_losses=config.max_consecutive_losses,
            cooldown_minutes=config.cooldown_minutes,
        ),
        initial_equity=config.initial_equity,
    )
    strategy = EMAStrategy(config.strategy.fast_period, config.strategy.slow_period)
    execution = ExecutionEngine(config.mode, config.slippage_pct, client, storage)
    portfolio = Portfolio(config.initial_equity)

    price_history: Dict[str, List[float]] = {symbol: [] for symbol in config.symbols}
    clock = Clock()
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Engine started in %s mode", config.mode)
    storage.record_event("INFO", "ENGINE_START", f"Engine started ({config.mode})", {})

    while True:
        if should_stop():
            logger.warning("Stop flag detected. Shutting down.")
            storage.record_event("WARN", "ENGINE_STOP", "Stop flag detected", {})
            break

        update_kill_switch(risk)

        can_trade, reason = risk.can_trade()
        if not can_trade:
            storage.record_event("WARN", "RISK_BLOCK", reason, {})

        try:
            prices = load_prices(client, config.symbols)
        except Exception as exc:
            logger.error("Price fetch failed: %s", exc)
            storage.record_event("ERROR", "PRICE_FETCH", str(exc), {})
            time.sleep(config.poll_interval_seconds)
            continue

        if risk.state.kill_switch:
            if config.mode != "paper":
                for symbol in config.symbols:
                    client.cancel_open_orders(symbol)
            if config.risk.kill_switch_close_positions and portfolio.positions:
                for symbol, position in list(portfolio.positions.items()):
                    close_side = "SELL" if position.side == "LONG" else "BUY"
                    close_order = OrderRequest(
                        symbol=symbol,
                        side=close_side,
                        quantity=position.quantity,
                        price=prices.get(symbol, position.entry_price),
                    )
                    trade = execution.submit_order(close_order)
                    if trade:
                        pnl = portfolio.update_with_trade(
                            symbol,
                            "LONG" if close_side == "BUY" else "SHORT",
                            trade.price,
                            trade.quantity,
                            config.leverage,
                        )
                        risk.record_trade_pnl(pnl)
                        storage.record_event(
                            "WARN",
                            "KILL_SWITCH_CLOSE",
                            f"Closed position {symbol}",
                            {"price": trade.price, "qty": trade.quantity, "pnl": pnl},
                        )

        for symbol in config.symbols:
            price_history[symbol].append(prices[symbol])
            signals = strategy.generate_signals(symbol, price_history[symbol])
            for signal in signals:
                storage.record_event(
                    "INFO",
                    "SIGNAL",
                    signal.reason,
                    {"symbol": symbol, "side": signal.side, "price": prices[symbol]},
                )
                if not can_trade:
                    storage.record_event(
                        "INFO",
                        "SIGNAL_SKIPPED",
                        f"Signal skipped: {reason}",
                        {"symbol": symbol, "side": signal.side},
                    )
                    continue

                side = signal.side
                notional = config.initial_equity * config.position_size_pct
                quantity = round(notional / prices[symbol], 6)
                order = OrderRequest(symbol=symbol, side=side, quantity=quantity, price=prices[symbol])
                trade = execution.submit_order(order)
                if trade:
                    pnl = portfolio.update_with_trade(
                        symbol,
                        "LONG" if side == "BUY" else "SHORT",
                        trade.price,
                        trade.quantity,
                        config.leverage,
                    )
                    risk.record_trade_pnl(pnl)
                    storage.record_event(
                        "INFO",
                        "TRADE",
                        f"Trade executed {side} {symbol}",
                        {"price": trade.price, "qty": trade.quantity, "pnl": pnl},
                    )

        equity = portfolio.total_equity(prices)
        positions_snapshot = [
            {
                "symbol": position.symbol,
                "side": position.side,
                "entry_price": position.entry_price,
                "quantity": position.quantity,
                "leverage": position.leverage,
                "mark_price": prices.get(symbol, position.entry_price),
                "unrealized_pnl": position.unrealized_pnl(prices.get(symbol, position.entry_price)),
            }
            for symbol, position in portfolio.positions.items()
        ]
        storage.record_equity(
            EquityRecord(
                timestamp=clock.now().isoformat(),
                equity=equity,
                realized_pnl=portfolio.realized_pnl,
                unrealized_pnl=portfolio.unrealized_pnl(prices),
            )
        )
        storage.replace_positions(clock.now().isoformat(), positions_snapshot)
        time.sleep(config.poll_interval_seconds)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Binance USDT-M Futures trading engine")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    args = parser.parse_args()

    run_engine(args.config)
