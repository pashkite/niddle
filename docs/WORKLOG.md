# WORKLOG

## Implemented
- Binance USDT-M futures trading engine with paper/testnet/live modes (live disabled by default).
- EMA crossover strategy with configurable periods.
- Risk controls: kill switch, daily loss limit, consecutive loss cooldown.
- SQLite storage for events, orders, trades, equity curve.
- Streamlit dashboard reading from SQLite (equity, events, positions) and control flags.
- Basic tests for risk, strategy, storage layers.

## TODO
- Add liquidation price calculations and leverage-aware metrics.
- Implement trailing stop logic and SL/TP order management.
- Add robust order status sync for testnet/live.
- Add background scheduler for periodic reconciliation of open orders.

## How to Run
1. Copy config and env examples:
   - `cp config.example.yaml config.yaml`
   - `cp .env.example .env`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Run the engine:
   - `python -m src.main --config config.yaml`
4. Run the dashboard:
   - `streamlit run src/dashboard/app.py`

## Config Notes
- `mode`: paper/testnet/live (live is blocked by default).
- `symbols`: list of Binance symbols (e.g., BTCUSDT).
- `daily_loss_limit_pct`, `max_consecutive_losses`, `cooldown_minutes` control risk.

## Issues / Incidents
- None recorded yet.
