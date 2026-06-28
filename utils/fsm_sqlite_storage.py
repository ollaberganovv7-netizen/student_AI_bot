from __future__ import annotations
"""
SQLite-based FSM storage for aiogram 3.x
Persists states and data across bot restarts.
"""
import json
import sqlite3
import logging
from typing import Any, Dict, Optional

from aiogram.fsm.state import State
from aiogram.fsm.storage.base import BaseStorage, StorageKey, StateType

logger = logging.getLogger(__name__)


class SQLiteStorage(BaseStorage):
    """Persistent FSM storage using SQLite."""

    def __init__(self, db_path: str = "fsm_storage.db"):
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _init_db(self):
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fsm_states (
                key TEXT PRIMARY KEY,
                state TEXT,
                data TEXT DEFAULT '{}'
            )
            """
        )
        self._conn.commit()
        logger.info(f"FSM SQLite storage initialized: {self._db_path}")

    def _make_key(self, key: StorageKey) -> str:
        return f"{key.bot_id}:{key.chat_id}:{key.user_id}"

    async def set_state(self, key: StorageKey, state: StateType = None) -> None:
        k = self._make_key(key)
        state_str = state.state if isinstance(state, State) else state
        self._conn.execute(
            "INSERT INTO fsm_states (key, state) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET state = ?",
            (k, state_str, state_str),
        )
        self._conn.commit()

    async def get_state(self, key: StorageKey) -> Optional[str]:
        k = self._make_key(key)
        row = self._conn.execute(
            "SELECT state FROM fsm_states WHERE key = ?", (k,)
        ).fetchone()
        return row[0] if row else None

    async def set_data(self, key: StorageKey, data: Dict[str, Any]) -> None:
        k = self._make_key(key)
        data_str = json.dumps(data, ensure_ascii=False, default=str)
        self._conn.execute(
            "INSERT INTO fsm_states (key, data) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET data = ?",
            (k, data_str, data_str),
        )
        self._conn.commit()

    async def get_data(self, key: StorageKey) -> Dict[str, Any]:
        k = self._make_key(key)
        row = self._conn.execute(
            "SELECT data FROM fsm_states WHERE key = ?", (k,)
        ).fetchone()
        if row and row[0]:
            try:
                return json.loads(row[0])
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}

    async def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
