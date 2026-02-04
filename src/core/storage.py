from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class EventRecord:
    timestamp: str
    level: str
    event_type: str
    message: str
    metadata: Dict[str, Any]


@dataclass
class OrderRecord:
    timestamp: str
    order_id: str
    symbol: str
    side: str
    status: str
    price: float
    quantity: float
    filled_qty: float
    mode: str
    metadata: Dict[str, Any]


@dataclass
class TradeRecord:
    timestamp: str
    trade_id: str
    order_id: str
    symbol: str
    side: str
    price: float
    quantity: float
    pnl: float
    mode: str
    metadata: Dict[str, Any]


@dataclass
class EquityRecord:
    timestamp: str
    equity: float
    realized_pnl: float
    unrealized_pnl: float


class Storage:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                level TEXT,
                event_type TEXT,
                message TEXT,
                metadata TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                order_id TEXT,
                symbol TEXT,
                side TEXT,
                status TEXT,
                price REAL,
                quantity REAL,
                filled_qty REAL,
                mode TEXT,
                metadata TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                trade_id TEXT,
                order_id TEXT,
                symbol TEXT,
                side TEXT,
                price REAL,
                quantity REAL,
                pnl REAL,
                mode TEXT,
                metadata TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS equity_curve (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                equity REAL,
                realized_pnl REAL,
                unrealized_pnl REAL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                symbol TEXT,
                side TEXT,
                entry_price REAL,
                quantity REAL,
                leverage INTEGER,
                mark_price REAL,
                unrealized_pnl REAL
            )
            """
        )
        self.conn.commit()

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def record_event(self, level: str, event_type: str, message: str, metadata: Dict[str, Any]) -> None:
        record = EventRecord(self._utc_now(), level, event_type, message, metadata)
        self.conn.execute(
            "INSERT INTO events (timestamp, level, event_type, message, metadata) VALUES (?, ?, ?, ?, ?)",
            (
                record.timestamp,
                record.level,
                record.event_type,
                record.message,
                str(record.metadata),
            ),
        )
        self.conn.commit()

    def record_order(self, record: OrderRecord) -> None:
        self.conn.execute(
            """
            INSERT INTO orders (timestamp, order_id, symbol, side, status, price, quantity, filled_qty, mode, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.timestamp,
                record.order_id,
                record.symbol,
                record.side,
                record.status,
                record.price,
                record.quantity,
                record.filled_qty,
                record.mode,
                str(record.metadata),
            ),
        )
        self.conn.commit()

    def record_trade(self, record: TradeRecord) -> None:
        self.conn.execute(
            """
            INSERT INTO trades (timestamp, trade_id, order_id, symbol, side, price, quantity, pnl, mode, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.timestamp,
                record.trade_id,
                record.order_id,
                record.symbol,
                record.side,
                record.price,
                record.quantity,
                record.pnl,
                record.mode,
                str(record.metadata),
            ),
        )
        self.conn.commit()

    def record_equity(self, record: EquityRecord) -> None:
        self.conn.execute(
            "INSERT INTO equity_curve (timestamp, equity, realized_pnl, unrealized_pnl) VALUES (?, ?, ?, ?)",
            (record.timestamp, record.equity, record.realized_pnl, record.unrealized_pnl),
        )
        self.conn.commit()

    def fetch_recent_events(self, limit: int = 50) -> List[sqlite3.Row]:
        cursor = self.conn.execute(
            "SELECT timestamp, level, event_type, message, metadata FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return cursor.fetchall()

    def fetch_latest_equity(self) -> Optional[sqlite3.Row]:
        cursor = self.conn.execute(
            "SELECT timestamp, equity, realized_pnl, unrealized_pnl FROM equity_curve ORDER BY id DESC LIMIT 1"
        )
        return cursor.fetchone()

    def replace_positions(self, timestamp: str, positions: Iterable[Dict[str, Any]]) -> None:
        self.conn.execute("DELETE FROM positions")
        self.conn.executemany(
            """
            INSERT INTO positions (timestamp, symbol, side, entry_price, quantity, leverage, mark_price, unrealized_pnl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    timestamp,
                    position["symbol"],
                    position["side"],
                    position["entry_price"],
                    position["quantity"],
                    position["leverage"],
                    position["mark_price"],
                    position["unrealized_pnl"],
                )
                for position in positions
            ],
        )
        self.conn.commit()

    def fetch_positions(self) -> List[sqlite3.Row]:
        cursor = self.conn.execute(
            "SELECT symbol, side, entry_price, quantity, leverage, mark_price, unrealized_pnl FROM positions"
        )
        return cursor.fetchall()

    def close(self) -> None:
        self.conn.close()
