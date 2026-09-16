"""Database Module for SQLite persistence."""

import atexit
import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
from app.config import get_setting


class Database:
    def __init__(self, path: str = None):
        self.path = path or get_setting("system.db_path", "storage/allostatic_self.db")
        self._connection = None
        self._ensure_directory()
        
    def _ensure_directory(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        
    def connect(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(self.path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection
    
    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None
    
    @contextmanager
    def get_cursor(self):
        conn = self.connect()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
    
    def execute(self, sql: str, params: Tuple = ()):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor
    
    def execute_many(self, sql: str, params_list: List[Tuple]):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.executemany(sql, params_list)
        conn.commit()
        cursor.close()
    
    def query(self, sql: str, params: Tuple = (), one: bool = False) -> List[Dict[str, Any]]:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        
        if one:
            row = cursor.fetchone()
            return dict(row) if row else None
        
        results = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return results
    
    def query_one(self, sql: str, params: Tuple = ()):
        return self.query(sql, params, one=True)
    
    def table_exists(self, table_name: str) -> bool:
        result = self.query_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return result is not None
    
    def create_tables(self):
        tables = {
            "memories": """
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "history": """
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    session_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "knowledge": """
                CREATE TABLE IF NOT EXISTS knowledge (
                    id TEXT PRIMARY KEY,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "self_events": """
                CREATE TABLE IF NOT EXISTS self_events (
                    id TEXT PRIMARY KEY,
                    ts TEXT DEFAULT CURRENT_TIMESTAMP,
                    kind TEXT NOT NULL,
                    payload TEXT
                )
            """,
            "brain_state": """
                CREATE TABLE IF NOT EXISTS brain_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "brain_chemicals": """
                CREATE TABLE IF NOT EXISTS brain_chemicals (
                    id TEXT PRIMARY KEY,
                    ts TEXT DEFAULT CURRENT_TIMESTAMP,
                    chemical TEXT NOT NULL,
                    value REAL NOT NULL
                )
            """,
            "brain_drives": """
                CREATE TABLE IF NOT EXISTS brain_drives (
                    id TEXT PRIMARY KEY,
                    ts TEXT DEFAULT CURRENT_TIMESTAMP,
                    drive TEXT NOT NULL,
                    value REAL NOT NULL
                )
            """,
            "sleep_cycles": """
                CREATE TABLE IF NOT EXISTS sleep_cycles (
                    id TEXT PRIMARY KEY,
                    started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    ended_at TEXT,
                    phase TEXT NOT NULL,
                    energy_before REAL,
                    energy_after REAL
                )
            """
        }
        
        for table_name, sql in tables.items():
            if not self.table_exists(table_name):
                self.execute(sql)
    
    def initialize(self):
        self.create_tables()


database = Database()


def get_database():
    return database


def init_db():
    global database
    database.initialize()
    return database


atexit.register(lambda: database.close())