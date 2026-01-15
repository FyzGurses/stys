import sqlite3
import os
from typing import Optional, Any, List, Dict
from contextlib import contextmanager
from datetime import datetime

from app.config.settings import settings


class Database:
    _instance: Optional['Database'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._connection: Optional[sqlite3.Connection] = None
        self._db_path = settings.database.path
        self._ensure_directory()
        self._initialized = True

    def _ensure_directory(self):
        db_dir = os.path.dirname(self._db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

    @property
    def connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(
                self._db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.connection.execute(query, params)

    def executemany(self, query: str, params_list: List[tuple]) -> sqlite3.Cursor:
        return self.connection.executemany(query, params_list)

    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def commit(self):
        if self._connection:
            self._connection.commit()

    def rollback(self):
        if self._connection:
            self._connection.rollback()

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    @contextmanager
    def transaction(self):
        try:
            yield self
            self.commit()
        except Exception as e:
            self.rollback()
            raise e

    def table_exists(self, table_name: str) -> bool:
        result = self.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return result is not None

    def get_last_insert_id(self) -> int:
        result = self.fetchone("SELECT last_insert_rowid()")
        return result[0] if result else 0


_db: Optional[Database] = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db
