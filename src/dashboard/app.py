from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from core.config import load_config
from core.storage import Storage

CONTROL_DIR = Path("control")
KILL_SWITCH_FILE = CONTROL_DIR / "kill_switch.flag"
STOP_FILE = CONTROL_DIR / "stop.flag"


st.set_page_config(page_title="Trading Dashboard", layout="wide")
load_dotenv()

config_path = st.sidebar.text_input("Config path", "config.yaml")

try:
    config = load_config(config_path)
except Exception as exc:
    st.error(f"Failed to load config: {exc}")
    st.stop()

storage = Storage(config.storage.path)
CONTROL_DIR.mkdir(parents=True, exist_ok=True)

col1, col2, col3 = st.columns(3)

mode = config.mode
status = "STOPPED" if STOP_FILE.exists() else "RUNNING"
last_updated = datetime.now(timezone.utc).isoformat()

col1.metric("Mode", mode)
col2.metric("Status", status)
col3.metric("Last Update (UTC)", last_updated)

st.subheader("Controls")
control_col1, control_col2, control_col3 = st.columns(3)

with control_col1:
    if st.button("Start"):
        if STOP_FILE.exists():
            STOP_FILE.unlink()
        st.success("Start signal sent")

with control_col2:
    if st.button("Stop"):
        STOP_FILE.write_text("stop")
        st.warning("Stop signal sent")

with control_col3:
    if st.button("Kill Switch"):
        KILL_SWITCH_FILE.write_text("kill")
        st.error("Kill switch enabled")

if st.button("Disable Kill Switch"):
    if KILL_SWITCH_FILE.exists():
        KILL_SWITCH_FILE.unlink()
        st.success("Kill switch disabled")

st.subheader("Account Summary")
latest_equity = storage.fetch_latest_equity()
if latest_equity:
    equity = latest_equity["equity"]
    realized = latest_equity["realized_pnl"]
    unrealized = latest_equity["unrealized_pnl"]
    return_pct = (equity - config.initial_equity) / config.initial_equity * 100
    st.write(
        {
            "initial_equity": config.initial_equity,
            "equity": equity,
            "return_pct": round(return_pct, 2),
            "realized_pnl": realized,
            "unrealized_pnl": unrealized,
        }
    )
else:
    st.info("No equity data yet.")

st.subheader("Positions")
positions = storage.fetch_positions()
if positions:
    positions_df = pd.DataFrame(positions)
    st.dataframe(positions_df)
else:
    st.info("No positions found.")

st.subheader("Recent Events")
events = storage.fetch_recent_events(100)
if events:
    df = pd.DataFrame(events)
    st.dataframe(df)
else:
    st.info("No events found.")
