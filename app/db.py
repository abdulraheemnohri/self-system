"""
Database Backend for Complete Self System
ڈاٹا بیس بیک اینڈ
"""

import os
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path


class Database:
    """SQLite database backend for persistent storage"""
    
    def __init__(self, path="storage/self_system.db"):
        self.path = path
        self.lock = threading.RLock()
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
    
    def execute(self, query, args=()):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(query, args)
            self.conn.commit()
            return cur
    
    def query(self, query, args=()):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(query, args)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    
    def create_tables(self):
        self.execute("CREATE TABLE IF NOT EXISTS facts (key TEXT PRIMARY KEY, value TEXT)")
        self.execute("CREATE TABLE IF NOT EXISTS notes (id TEXT PRIMARY KEY, text TEXT, tags TEXT, created_at TEXT)")
        self.execute("CREATE TABLE IF NOT EXISTS knowledge (id TEXT PRIMARY KEY, question TEXT, answer TEXT, created_at TEXT)")
        self.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT, created_at TEXT)")
        self.execute("CREATE TABLE IF NOT EXISTS memories (id TEXT PRIMARY KEY, text TEXT, kind TEXT, metadata TEXT, embedding TEXT, dim INTEGER, created_at TEXT)")
        self.execute("CREATE TABLE IF NOT EXISTS schedules (id TEXT PRIMARY KEY, name TEXT UNIQUE, action TEXT, interval_seconds INTEGER, last_run REAL DEFAULT 0)")
        self.execute("CREATE TABLE IF NOT EXISTS skills (id TEXT PRIMARY KEY, name TEXT, description TEXT, code TEXT, status TEXT DEFAULT "generated", created_at TEXT)")
        self.execute("CREATE TABLE IF NOT EXISTS audit (id TEXT PRIMARY KEY, ts REAL, tool TEXT, args TEXT, status TEXT, detail TEXT, created_at TEXT)")
    
    def set_fact(self, key, value):
        key = str(key).lower()
        now = datetime.now().isoformat(timespec="seconds")
        self.execute("INSERT OR REPLACE INTO facts (key, value) VALUES (?, ?)", (key, str(value)))
    
    def get_fact(self, key):
        key = str(key).lower()
        rows = self.query("SELECT value FROM facts WHERE key = ?", (key,))
        return rows[0]["value"] if rows else None
    
    def get_facts(self):
        rows = self.query("SELECT key, value FROM facts ORDER BY key")
        return {row["key"]: row["value"] for row in rows}
    
    def delete_fact(self, key):
        key = str(key).lower()
        self.execute("DELETE FROM facts WHERE key = ?", (key,))
    
    def add_note(self, text, tags=""):
        note_id = str(uuid.uuid4())
        now = datetime.now().isoformat(timespec="seconds")
        self.execute("INSERT INTO notes (id, text, tags, created_at) VALUES (?, ?, ?, ?)", (note_id, str(text), str(tags), now))
        return note_id
    
    def list_notes(self, limit=20):
        return self.query("SELECT text, tags, created_at FROM notes ORDER BY created_at DESC LIMIT ?", (int(limit),))
    
    def add_knowledge(self, question, answer):
        kid = str(uuid.uuid4())
        now = datetime.now().isoformat(timespec="seconds")
        self.execute("INSERT INTO knowledge (id, question, answer, created_at) VALUES (?, ?, ?, ?)", (kid, str(question), str(answer), now))
        return kid
    
    def list_knowledge(self, limit=50):
        return self.query("SELECT question, answer, created_at FROM knowledge ORDER BY created_at DESC LIMIT ?", (int(limit),))
    
    def add_history(self, role, content):
        now = datetime.now().isoformat(timespec="seconds")
        self.execute("INSERT INTO history (role, content, created_at) VALUES (?, ?, ?)", (role, content, now))
    
    def get_history(self, limit=12):
        rows = self.query("SELECT role, content FROM history ORDER BY id DESC LIMIT ?", (int(limit),))
        return list(reversed(rows))
    
    def clear_history(self):
        self.execute("DELETE FROM history")
    
    def cleanup_history(self, days=30):
        cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
        self.execute("DELETE FROM history WHERE created_at < ?", (cutoff,))
    
    def add_memory(self, text, kind, metadata, embedding, dim):
        memory_id = str(uuid.uuid4())
        now = datetime.now().isoformat(timespec="seconds")
        self.execute("INSERT INTO memories (id, text, kind, metadata, embedding, dim, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (memory_id, str(text), str(kind), json.dumps(metadata or {}, ensure_ascii=False), json.dumps(embedding, ensure_ascii=False), int(dim), now))
        return memory_id
    
    def get_memories_by_dim(self, dim):
        return self.query("SELECT id, text, kind, metadata, embedding FROM memories WHERE dim = ?", (int(dim),))
    
    def cleanup_memories(self):
        self.execute("DELETE FROM memories WHERE id NOT IN (SELECT MIN(id) FROM memories GROUP BY text, kind)")
    
    def add_schedule(self, name, action, interval_seconds):
        sid = str(uuid.uuid4())
        self.execute("INSERT OR IGNORE INTO schedules (id, name, action, interval_seconds, last_run) VALUES (?, ?, ?, ?, 0)",
            (sid, name, action, int(interval_seconds)))
    
    def get_schedule_by_name(self, name):
        rows = self.query("SELECT * FROM schedules WHERE name = ?", (name,))
        return rows[0] if rows else None
    
    def get_due_schedules(self, now_ts):
        return self.query("SELECT * FROM schedules WHERE (last_run + interval_seconds) <= ?", (float(now_ts),))
    
    def update_schedule_last_run(self, sid, now_ts):
        self.execute("UPDATE schedules SET last_run = ? WHERE id = ?", (float(now_ts), sid))
    
    def list_schedules(self):
        return self.query("SELECT name, action, interval_seconds, last_run FROM schedules")
    
    def add_skill(self, name, description, code, status="generated"):
        skill_id = str(uuid.uuid4())
        now = datetime.now().isoformat(timespec="seconds")
        self.execute("INSERT INTO skills (id, name, description, code, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (skill_id, name, description, code, status, now))
        return skill_id
    
    def list_skills(self, limit=50):
        return self.query("SELECT name, description, status, created_at FROM skills ORDER BY created_at DESC LIMIT ?", (int(limit),))
    
    def add_audit(self, tool, args, status, detail=""):
        audit_id = str(uuid.uuid4())
        now = datetime.now().isoformat(timespec="seconds")
        self.execute("INSERT INTO audit (id, ts, tool, args, status, detail, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (audit_id, time.time(), tool, json.dumps(args, ensure_ascii=False), status, str(detail)[:2000], now))