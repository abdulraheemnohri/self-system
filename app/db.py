"""
Database Manager for Complete Self System
ڈاٹا بیس مینیجر برائے خود کار نظام

SQLite backend for facts, notes, knowledge, history, and vector memory
"""

import sqlite3
import json
import threading
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class Database:
    def __init__(self, db_path: str = "storage/self_system.db"):
        self.db_path = db_path
        self.lock = threading.RLock()
        self._ensure_directory()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _ensure_directory(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _execute(self, query: str, args: Tuple = ()) -> sqlite3.Cursor:
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(query, args)
            self.conn.commit()
            return cur
    
    def _query(self, query: str, args: Tuple = ()) -> List[Dict[str, Any]]:
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(query, args)
            return [dict(row) for row in cur.fetchall()]
    
    def _create_tables(self) -> None:
        self._execute("CREATE TABLE IF NOT EXISTS facts (id TEXT PRIMARY KEY, key TEXT NOT NULL, value TEXT NOT NULL, metadata TEXT DEFAULT '{}', created_at REAL DEFAULT (strftime('%s', 'now')), updated_at REAL DEFAULT (strftime('%s', 'now')))")
        self._execute("CREATE INDEX IF NOT EXISTS idx_facts_key ON facts(key)")
        self._execute("CREATE TABLE IF NOT EXISTS notes (id TEXT PRIMARY KEY, text TEXT NOT NULL, tags TEXT DEFAULT '', metadata TEXT DEFAULT '{}', created_at REAL DEFAULT (strftime('%s', 'now')))")
        self._execute("CREATE INDEX IF NOT EXISTS idx_notes_tags ON notes(tags)")
        self._execute("CREATE TABLE IF NOT EXISTS knowledge (id TEXT PRIMARY KEY, title TEXT NOT NULL, content TEXT NOT NULL, category TEXT DEFAULT 'general', metadata TEXT DEFAULT '{}', created_at REAL DEFAULT (strftime('%s', 'now')), updated_at REAL DEFAULT (strftime('%s', 'now')))")
        self._execute("CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge(category)")
        self._execute("CREATE TABLE IF NOT EXISTS history (id TEXT PRIMARY KEY, role TEXT NOT NULL, content TEXT NOT NULL, session_id TEXT DEFAULT '', metadata TEXT DEFAULT '{}', created_at REAL DEFAULT (strftime('%s', 'now')))")
        self._execute("CREATE INDEX IF NOT EXISTS idx_history_session ON history(session_id)")
        self._execute("CREATE TABLE IF NOT EXISTS memories (id TEXT PRIMARY KEY, text TEXT NOT NULL, kind TEXT DEFAULT 'note', metadata TEXT DEFAULT '{}', embedding TEXT NOT NULL, dim INTEGER NOT NULL, created_at REAL DEFAULT (strftime('%s', 'now')))")
        self._execute("CREATE INDEX IF NOT EXISTS idx_memories_dim ON memories(dim)")
        self._execute("CREATE TABLE IF NOT EXISTS skills (id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT DEFAULT '', code TEXT NOT NULL, status TEXT DEFAULT 'pending', metadata TEXT DEFAULT '{}', created_at REAL DEFAULT (strftime('%s', 'now')), updated_at REAL DEFAULT (strftime('%s', 'now')))")
        self._execute("CREATE TABLE IF NOT EXISTS schedules (id TEXT PRIMARY KEY, name TEXT NOT NULL, action TEXT NOT NULL, interval_seconds INTEGER NOT NULL DEFAULT 3600, last_run REAL DEFAULT 0, next_run REAL DEFAULT 0, enabled INTEGER DEFAULT 1, metadata TEXT DEFAULT '{}')")
    
    def add_fact(self, key: str, value: str, metadata: Optional[Dict] = None) -> str:
        fact_id = str(uuid.uuid4())
        existing = self.get_fact(key)
        if existing:
            fact_id = existing['id']
            self._execute("UPDATE facts SET value = ?, metadata = ?, updated_at = ? WHERE id = ?", (value, json.dumps(metadata or {}), time.time(), fact_id))
        else:
            self._execute("INSERT INTO facts VALUES (?, ?, ?, ?, ?, ?)", (fact_id, key, value, json.dumps(metadata or {}), time.time(), time.time()))
        return fact_id
    
    def get_fact(self, key: str) -> Optional[Dict[str, Any]]:
        results = self._query("SELECT * FROM facts WHERE key = ?", (key,))
        return results[0] if results else None
    
    def get_facts(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._query("SELECT * FROM facts ORDER BY updated_at DESC LIMIT ?", (limit,))
    
    def add_note(self, text: str, tags: str = "", metadata: Optional[Dict] = None) -> str:
        note_id = str(uuid.uuid4())
        self._execute("INSERT INTO notes VALUES (?, ?, ?, ?, ?)", (note_id, text, tags, json.dumps(metadata or {}), time.time()))
        return note_id
    
    def list_notes(self, limit: int = 100, tags: str = "") -> List[Dict[str, Any]]:
        if tags:
            return self._query("SELECT * FROM notes WHERE tags LIKE ? ORDER BY created_at DESC LIMIT ?", (f"%{tags.split(',')[0].strip()}%", limit))
        return self._query("SELECT * FROM notes ORDER BY created_at DESC LIMIT ?", (limit,))
    
    def add_knowledge(self, title: str, content: str, category: str = "general", metadata: Optional[Dict] = None) -> str:
        knowledge_id = str(uuid.uuid4())
        self._execute("INSERT INTO knowledge VALUES (?, ?, ?, ?, ?, ?, ?)", (knowledge_id, title, content, category, json.dumps(metadata or {}), time.time(), time.time()))
        return knowledge_id
    
    def list_knowledge(self, limit: int = 100, category: str = "") -> List[Dict[str, Any]]:
        if category:
            return self._query("SELECT * FROM knowledge WHERE category = ? ORDER BY updated_at DESC LIMIT ?", (category, limit))
        return self._query("SELECT * FROM knowledge ORDER BY updated_at DESC LIMIT ?", (limit,))
    
    def search_knowledge(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        return self._query("SELECT * FROM knowledge WHERE content LIKE ? OR title LIKE ? ORDER BY updated_at DESC LIMIT ?", (f"%{query}%", f"%{query}%", limit))
    
    def add_history(self, role: str, content: str, session_id: str = "", metadata: Optional[Dict] = None) -> str:
        history_id = str(uuid.uuid4())
        self._execute("INSERT INTO history VALUES (?, ?, ?, ?, ?, ?)", (history_id, role, content, session_id, json.dumps(metadata or {}), time.time()))
        return history_id
    
    def get_history(self, limit: int = 100, session_id: str = "") -> List[Dict[str, Any]]:
        if session_id:
            return self._query("SELECT * FROM history WHERE session_id = ? ORDER BY created_at ASC LIMIT ?", (session_id, limit))
        return self._query("SELECT * FROM history ORDER BY created_at DESC LIMIT ?", (limit,))
    
    def cleanup_history(self, days: int = 30) -> int:
        cutoff = time.time() - (days * 86400)
        cursor = self._execute("DELETE FROM history WHERE created_at < ?", (cutoff,))
        return cursor.rowcount
    
    def add_memory(self, text: str, kind: str = "note", embedding: List[float] = None, dim: int = 0, metadata: Optional[Dict] = None) -> str:
        memory_id = str(uuid.uuid4())
        self._execute("INSERT INTO memories VALUES (?, ?, ?, ?, ?, ?, ?)", (memory_id, text, kind, json.dumps(metadata or {}), json.dumps(embedding or []), dim, time.time()))
        return memory_id
    
    def get_memories_by_dim(self, dim: int, limit: int = 1000) -> List[Dict[str, Any]]:
        return self._query("SELECT * FROM memories WHERE dim = ? LIMIT ?", (dim, limit))
    
    def add_skill(self, name: str, description: str, code: str, status: str = "pending", metadata: Optional[Dict] = None) -> str:
        skill_id = str(uuid.uuid4())
        self._execute("INSERT INTO skills VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (skill_id, name, description, code, status, json.dumps(metadata or {}), time.time(), time.time()))
        return skill_id
    
    def list_skills(self, limit: int = 100, status: str = "") -> List[Dict[str, Any]]:
        if status:
            return self._query("SELECT * FROM skills WHERE status = ? ORDER BY updated_at DESC LIMIT ?", (status, limit))
        return self._query("SELECT * FROM skills ORDER BY updated_at DESC LIMIT ?", (limit,))
    
    def add_schedule(self, name: str, action: str, interval_seconds: int = 3600, enabled: bool = True, metadata: Optional[Dict] = None) -> str:
        schedule_id = str(uuid.uuid4())
        now = time.time()
        self._execute("INSERT INTO schedules VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (schedule_id, name, action, interval_seconds, 0, now + interval_seconds, 1 if enabled else 0, json.dumps(metadata or {})))
        return schedule_id
    
    def list_schedules(self) -> List[Dict[str, Any]]:
        return self._query("SELECT * FROM schedules ORDER BY next_run ASC")
    
    def get_stats(self) -> Dict[str, Any]:
        stats = {}
        tables = ['facts', 'notes', 'knowledge', 'history', 'memories', 'skills', 'schedules']
        for table in tables:
            results = self._query(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = results[0]['count'] if results else 0
        return stats
    
    def close(self) -> None:
        with self.lock:
            if self.conn:
                self.conn.close()
                self.conn = None


db = Database()