# Binance USDT-M Futures Auto-Trading System (MVP+)

## Overview
This project provides a minimal, safety-first automated trading system for Binance USDT-M Futures. It supports paper trading, testnet, and explicitly enabled live trading. The engine logs all decisions, orders, and events to SQLite and exposes a Streamlit dashboard for monitoring.

## Safety Defaults
- **Default mode is `paper`**.
- **Live trading is blocked** unless explicitly enabled in the config (and you acknowledge the risk).
- API keys are loaded from environment variables or `.env`.
- Kill switch, daily loss limit, and consecutive loss cooldown are built-in.

## Install
```bash
pip install -r requirements.txt
```

## Configuration
```bash
cp config.example.yaml config.yaml
cp .env.example .env
```
Edit `config.yaml` to set symbols, risk limits, and strategy parameters.

## Run Engine (Paper)
```bash
python -m src.main --config config.yaml
```

## Switch to Testnet
Update in `config.yaml`:
```yaml
mode: testnet
```
Set testnet API keys in `.env` or environment variables.

## Enable Live (Explicit)
Update in `config.yaml` (use extreme caution):
```yaml
mode: live
allow_live: true
```

## Run Dashboard
```bash
streamlit run src/dashboard/app.py
```

## GitHub Actions Dashboard Preview
- The workflow `.github/workflows/dashboard-preview.yml` renders a static dashboard snapshot and publishes it to GitHub Pages.
- Trigger on push to `work` or via **Actions > Dashboard Preview**.

## Controls
- **Start/Stop**: create/remove `control/stop.flag`.
- **Kill Switch**: create `control/kill_switch.flag`.

## Notes
- The engine writes logs to `logs/engine.log` and SQLite to `data/trading.db`.
- Use testnet before any live deployment.
