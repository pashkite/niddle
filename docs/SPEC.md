# System Specification

## Architecture (Text Diagram)
```
+------------------+        +------------------+
| Trading Engine   |        | Streamlit UI     |
| (src/main.py)    |        | (dashboard/app)  |
+--------+---------+        +--------+---------+
         |                           |
         | writes/reads              | reads
         v                           v
     SQLite DB (data/trading.db)  Control Flags (control/*.flag)
```

## Module Responsibilities (RACI-style)
- core/config.py: Load/validate config, enforce safe mode.
- core/logger.py: UTC logging to console + file.
- core/storage.py: SQLite persistence for events/orders/trades/equity.
- exchange/binance_client.py: Binance API wrapper for prices, positions, cancels.
- trading/strategy_ema.py: Signal generation.
- trading/risk.py: Kill switch, daily loss, consecutive loss cooldown.
- trading/execution.py: Order submission + paper fill simulation.
- trading/portfolio.py: Position/PnL tracking.
- dashboard/app.py: UI for status, controls, events.

## Risk & Safety Controls
- Default mode is paper/testnet; live blocked unless explicitly enabled.
- Kill switch flag stops new orders and can cancel open orders (manual intervention).
- Daily loss limit stops new trades when exceeded.
- Consecutive loss cooldown prevents rapid re-entry.
- Startup sync: detect existing positions and halt for safety.

## Recovery
- On restart, engine checks open positions for testnet/live and halts if any.
- Persistent SQLite logs for replay and audit.
