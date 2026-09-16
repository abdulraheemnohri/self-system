#!/usr/bin/env python3
"""
Database Manager for Complete Self System

SQLite backend for:
- Facts (user information)
- Notes (general notes)
- Knowledge (Q&A pairs)
- History (conversation history)
- Memories (vector embeddings)
- Skills (generated plugins)
- Schedules (autonomous tasks)

Provides thread-safe database operations with comprehensive CRUD methods.
"""

import sqlite3
import json
import threading
import time
import uuid
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class Database:
    """
    SQLite database manager for the Complete Self System.
    
    Features:
    - Thread-safe operations
    - Automatic table creation
    - CRUD operations for all data types
    - Cleanup and maintenance methods
    - Statistics and analytics
    """
    
    def __init__(self, db_path: str = "storage/self_system.db"):
        """
        Initialize the database.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.lock = threading.RLock()
        self._ensure_directory()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _ensure_directory(self) -> None:
        """Ensure the database directory exists."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _execute(self, query: str, args: Tuple = ()) -> sqlite3.Cursor:
        """Execute a SQL query with thread safety."""
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(query, args)
            self.conn.commit()
            return cur
    
    def _query(self, query: str, args: Tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results as dictionaries."""
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(query, args)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    
    def _create_tables(self) -> None:
        """Create all database tables if they don't exist."""
        # Facts table (key-value pairs for user information)
        self._execute("""
            CREATE TABLE IF NOT EXISTS facts (
                id TEXT PRIMARY KEY,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at REAL DEFAULT (strftime('%s', 'now')),
                updated_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)
        self._execute("CREATE INDEX IF NOT EXISTS idx_facts_key ON facts(key)")
        
        # Notes table (general notes with tags)
        self._execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                tags TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}',
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)
        self._execute("CREATE INDEX IF NOT EXISTS idx_notes_tags ON notes(tags)")
        
        # Knowledge table (Q&A pairs for direct answers)
        self._execute("""
            CREATE TABLE IF NOT EXISTS knowledge (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                metadata TEXT DEFAULT '{}',
                created_at REAL DEFAULT (strftime('%s', 'now')),
                updated_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)
        self._execute("CREATE INDEX IF NOT EXISTS idx_knowledge_question ON knowledge(question)")
        self._execute("CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge(category)")
        
        # History table (conversation history)
        self._execute("""
            CREATE TABLE IF NOT EXISTS history (
                id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                session_id TEXT DEFAULT '',
                metadata TEXT DEFAULT '{}',
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)
        self._execute("CREATE INDEX IF NOT EXISTS idx_history_session ON history(session_id)")
        self._execute("CREATE INDEX IF NOT EXISTS idx_history_created ON history(created_at)")
        
        # Memories table (vector embeddings for semantic search)
        self._execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                kind TEXT DEFAULT 'note',
                metadata TEXT DEFAULT '{}',
                embedding TEXT NOT NULL,
                dim INTEGER NOT NULL,
                created_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)
        self._execute("CREATE INDEX IF NOT EXISTS idx_memories_dim ON memories(dim)")
        self._execute("CREATE INDEX IF NOT EXISTS idx_memories_kind ON memories(kind)")
        
        # Skills table (generated plugins)
        self._execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                code TEXT NOT NULL,
                status TEXT DEFAULT 'generated',
                metadata TEXT DEFAULT '{}',
                created_at REAL DEFAULT (strftime('%s', 'now')),
                updated_at REAL DEFAULT (strftime('%s', 'now'))
            )
        """)
        self._execute("CREATE INDEX IF NOT EXISTS idx_skills_name ON skills(name)")
        self._execute("CREATE INDEX IF NOT EXISTS idx_skills_status ON skills(status)")
        
        # Schedules table (autonomous tasks)
        self._execute("""
            CREATE TABLE IF NOT EXISTS schedules (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                action TEXT NOT NULL,
                interval_seconds INTEGER NOT NULL DEFAULT 3600,
                last_run REAL DEFAULT 0,
                next_run REAL DEFAULT 0,
                enabled INTEGER DEFAULT 1,
                metadata TEXT DEFAULT '{}'
            )
        """)
        self._execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_schedules_name ON schedules(name)")
    
    # ============================================================
    # Facts Methods
    # ============================================================
    
    def set_fact(self, key: str, value: str, metadata: Optional[Dict] = None) -> None:
        """
        Set a fact (key-value pair).
        
        Args:
            key: The key for the fact
            value: The value for the fact
            metadata: Optional metadata
        """
        key = str(key).strip().lower()
        value = str(value)
        metadata = metadata or {}
        
        existing = self.get_fact(key)
        if existing:
            self._execute(
                "UPDATE facts SET value = ?, metadata = ?, updated_at = ? WHERE id = ?",
                (value, json.dumps(metadata), time.time(), existing['id'])
            )
        else:
            self._execute(
                "INSERT INTO facts (id, key, value, metadata, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), key, value, json.dumps(metadata), time.time(), time.time())
            )
    
    def get_fact(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a fact by key.
        
        Args:
            key: The key to look up
            
        Returns:
            Fact dictionary or None
        """
        results = self._query("SELECT * FROM facts WHERE key = ?", (str(key).strip().lower(),))
        return results[0] if results else None
    
    def get_facts(self) -> Dict[str, str]:
        """
        Get all facts as a dictionary.
        
        Returns:
            Dictionary of {key: value}
        """
        rows = self._query("SELECT key, value FROM facts ORDER BY key")
        return {row['key']: row['value'] for row in rows}
    
    def delete_fact(self, key: str) -> bool:
        """
        Delete a fact by key.
        
        Args:
            key: The key to delete
            
        Returns:
            True if deleted, False otherwise
        """
        cursor = self._execute("DELETE FROM facts WHERE key = ?", (str(key).strip().lower(),))
        return cursor.rowcount > 0
    
    # ============================================================
    # Notes Methods
    # ============================================================
    
    def add_note(self, text: str, tags: str = "", metadata: Optional[Dict] = None) -> str:
        """
        Add a note.
        
        Args:
            text: The note text
            tags: Comma-separated tags
            metadata: Optional metadata
            
        Returns:
            Note ID
        """
        note_id = str(uuid.uuid4())
        self._execute(
            "INSERT INTO notes (id, text, tags, metadata, created_at) VALUES (?, ?, ?, ?, ?)",
            (note_id, str(text), str(tags), json.dumps(metadata or {}), time.time())
        )
        return note_id
    
    def list_notes(self, limit: int = 20, tags: str = "") -> List[Dict[str, Any]]:
        """
        List notes, optionally filtered by tags.
        
        Args:
            limit: Maximum number of notes to return
            tags: Filter by tags (comma-separated)
            
        Returns:
            List of note dictionaries
        """
        if tags:
            # Search for any of the tags
            tag_conditions = " OR ".join([f"tags LIKE '%{tag.strip()}%'" for tag in tags.split(",")])
            return self._query(f"SELECT * FROM notes WHERE {tag_conditions} ORDER BY created_at DESC LIMIT ?", (limit,))
        return self._query("SELECT * FROM notes ORDER BY created_at DESC LIMIT ?", (limit,))
    
    def delete_note(self, note_id: str) -> bool:
        """
        Delete a note by ID.
        
        Args:
            note_id: The note ID to delete
            
        Returns:
            True if deleted, False otherwise
        """
        cursor = self._execute("DELETE FROM notes WHERE id = ?", (note_id,))
        return cursor.rowcount > 0
    
    # ============================================================
    # Knowledge Methods
    # ============================================================
    
    def add_knowledge(self, question: str, answer: str, category: str = "general", 
                      metadata: Optional[Dict] = None) -> str:
        """
        Add a knowledge Q&A pair.
        
        Args:
            question: The question
            answer: The answer
            category: Category for organization
            metadata: Optional metadata
            
        Returns:
            Knowledge ID
        """
        knowledge_id = str(uuid.uuid4())
        self._execute(
            """INSERT INTO knowledge (id, question, answer, category, metadata, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (knowledge_id, str(question), str(answer), str(category), 
             json.dumps(metadata or {}), time.time(), time.time())
        )
        return knowledge_id
    
    def list_knowledge(self, limit: int = 50, category: str = "") -> List[Dict[str, Any]]:
        """
        List knowledge items, optionally filtered by category.
        
        Args:
            limit: Maximum number of items to return
            category: Filter by category
            
        Returns:
            List of knowledge dictionaries
        """
        if category:
            return self._query(
                "SELECT * FROM knowledge WHERE category = ? ORDER BY updated_at DESC LIMIT ?",
                (category, limit)
            )
        return self._query(
            "SELECT * FROM knowledge ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        )
    
    def find_best_knowledge(self, query: str, threshold: float = 0.0) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Find the best matching knowledge for a query.
        
        Args:
            query: The query to match
            threshold: Minimum score to return a match
            
        Returns:
            Tuple of (best_match, score)
        """
        from app.vector_store import relevance
        
        query = str(query).strip().lower()
        if not query:
            return None, 0.0
        
        best = None
        best_score = 0.0
        
        for item in self.list_knowledge(limit=100):
            question = str(item.get('question', '')).lower()
            answer = str(item.get('answer', '')).lower()
            
            question_score = relevance(query, question)
            answer_score = relevance(query, answer) * 0.70
            score = max(question_score, answer_score)
            
            if score > best_score:
                best = item
                best_score = score
        
        if best_score >= threshold:
            return best, best_score
        return None, best_score
    
    def delete_knowledge(self, knowledge_id: str) -> bool:
        """
        Delete a knowledge item by ID.
        
        Args:
            knowledge_id: The knowledge ID to delete
            
        Returns:
            True if deleted, False otherwise
        """
        cursor = self._execute("DELETE FROM knowledge WHERE id = ?", (knowledge_id,))
        return cursor.rowcount > 0
    
    def search_knowledge(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search knowledge by question or answer.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching knowledge items
        """
        query = f"%{str(query).strip().lower()}%"
        return self._query(
            """SELECT * FROM knowledge 
               WHERE LOWER(question) LIKE ? OR LOWER(answer) LIKE ? 
               ORDER BY updated_at DESC LIMIT ?""",
            (query, query, limit)
        )
    
    # ============================================================
    # History Methods
    # ============================================================
    
    def add_history(self, role: str, content: str, session_id: str = "", 
                    metadata: Optional[Dict] = None) -> str:
        """
        Add a conversation history entry.
        
        Args:
            role: Role (user, assistant, system, tool)
            content: The content
            session_id: Optional session ID
            metadata: Optional metadata
            
        Returns:
            History ID
        """
        history_id = str(uuid.uuid4())
        self._execute(
            """INSERT INTO history (id, role, content, session_id, metadata, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (history_id, str(role), str(content), str(session_id), 
             json.dumps(metadata or {}), time.time())
        )
        return history_id
    
    def get_history(self, limit: int = 12, session_id: str = "") -> List[Dict[str, Any]]:
        """
        Get conversation history.
        
        Args:
            limit: Maximum number of entries to return
            session_id: Filter by session ID
            
        Returns:
            List of history entries
        """
        if session_id:
            return self._query(
                """SELECT * FROM history 
                   WHERE session_id = ? 
                   ORDER BY created_at ASC LIMIT ?""",
                (session_id, limit)
            )
        return self._query(
            "SELECT * FROM history ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
    
    def clear_history(self) -> None:
        """Clear all conversation history."""
        self._execute("DELETE FROM history")
    
    def cleanup_history(self, days: int = 30) -> int:
        """
        Clean up old history entries.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of entries deleted
        """
        cutoff = time.time() - (days * 86400)
        cursor = self._execute("DELETE FROM history WHERE created_at < ?", (cutoff,))
        return cursor.rowcount
    
    # ============================================================
    # Memories Methods (Vector Embeddings)
    # ============================================================
    
    def add_memory(self, text: str, kind: str = "note", embedding: List[float] = None, 
                   dim: int = 0, metadata: Optional[Dict] = None) -> str:
        """
        Add a memory with vector embedding.
        
        Args:
            text: The text to store
            kind: Type of memory (note, fact, knowledge, conversation, etc.)
            embedding: Vector embedding
            dim: Dimension of the embedding
            metadata: Optional metadata
            
        Returns:
            Memory ID
        """
        memory_id = str(uuid.uuid4())
        embedding_json = json.dumps(embedding or [])
        metadata_json = json.dumps(metadata or {})
        
        self._execute(
            """INSERT INTO memories (id, text, kind, metadata, embedding, dim, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (memory_id, str(text), str(kind), metadata_json, embedding_json, int(dim), time.time())
        )
        return memory_id
    
    def get_memories_by_dim(self, dim: int, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get memories by embedding dimension.
        
        Args:
            dim: Embedding dimension
            limit: Maximum number to return
            
        Returns:
            List of memory dictionaries
        """
        return self._query(
            "SELECT * FROM memories WHERE dim = ? LIMIT ?",
            (int(dim), int(limit))
        )
    
    def cleanup_memories(self) -> int:
        """
        Clean up duplicate memories (keep only the most recent for each text/kind).
        
        Returns:
            Number of duplicates removed
        """
        # Delete all but the most recent for each text/kind combination
        cursor = self._execute("""
            DELETE FROM memories
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM memories
                GROUP BY text, kind
            )
        """)
        return cursor.rowcount
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a memory by ID.
        
        Args:
            memory_id: The memory ID to delete
            
        Returns:
            True if deleted, False otherwise
        """
        cursor = self._execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        return cursor.rowcount > 0
    
    # ============================================================
    # Skills Methods
    # ============================================================
    
    def add_skill(self, name: str, description: str = "", code: str = "", 
                  status: str = "generated", metadata: Optional[Dict] = None) -> str:
        """
        Add a generated skill.
        
        Args:
            name: Skill name
            description: Skill description
            code: Skill code
            status: Skill status (generated, installed, active, etc.)
            metadata: Optional metadata
            
        Returns:
            Skill ID
        """
        skill_id = str(uuid.uuid4())
        self._execute(
            """INSERT INTO skills (id, name, description, code, status, metadata, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (skill_id, str(name), str(description), str(code), 
             str(status), json.dumps(metadata or {}), time.time(), time.time())
        )
        return skill_id
    
    def list_skills(self, limit: int = 100, status: str = "") -> List[Dict[str, Any]]:
        """
        List skills, optionally filtered by status.
        
        Args:
            limit: Maximum number to return
            status: Filter by status
            
        Returns:
            List of skill dictionaries
        """
        if status:
            return self._query(
                "SELECT * FROM skills WHERE status = ? ORDER BY updated_at DESC LIMIT ?",
                (status, limit)
            )
        return self._query(
            "SELECT * FROM skills ORDER BY updated_at DESC LIMIT ?",
            (limit,)
        )
    
    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a skill by ID.
        
        Args:
            skill_id: The skill ID
            
        Returns:
            Skill dictionary or None
        """
        results = self._query("SELECT * FROM skills WHERE id = ?", (skill_id,))
        return results[0] if results else None
    
    def delete_skill(self, skill_id: str) -> bool:
        """
        Delete a skill by ID.
        
        Args:
            skill_id: The skill ID to delete
            
        Returns:
            True if deleted, False otherwise
        """
        cursor = self._execute("DELETE FROM skills WHERE id = ?", (skill_id,))
        return cursor.rowcount > 0
    
    # ============================================================
    # Schedules Methods
    # ============================================================
    
    def add_schedule(self, name: str, action: str, interval_seconds: int = 3600, 
                     enabled: bool = True, metadata: Optional[Dict] = None) -> str:
        """
        Add a scheduled task.
        
        Args:
            name: Unique name for the schedule
            action: Action to execute
            interval_seconds: Seconds between executions
            enabled: Whether the task is enabled
            metadata: Optional metadata
            
        Returns:
            Schedule ID
        """
        schedule_id = str(uuid.uuid4())
        now = time.time()
        next_run = now + interval_seconds
        
        self._execute(
            """INSERT OR REPLACE INTO schedules 
               (id, name, action, interval_seconds, last_run, next_run, enabled, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (schedule_id, str(name), str(action), int(interval_seconds), 
             0, next_run, 1 if enabled else 0, json.dumps(metadata or {}))
        )
        return schedule_id
    
    def get_schedule_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a schedule by name.
        
        Args:
            name: The schedule name
            
        Returns:
            Schedule dictionary or None
        """
        results = self._query("SELECT * FROM schedules WHERE name = ?", (str(name),))
        return results[0] if results else None
    
    def get_due_schedules(self, now_ts: float) -> List[Dict[str, Any]]:
        """
        Get schedules that are due to run.
        
        Args:
            now_ts: Current timestamp
            
        Returns:
            List of due schedule dictionaries
        """
        return self._query(
            "SELECT * FROM schedules WHERE enabled = 1 AND next_run <= ?",
            (float(now_ts),)
        )
    
    def update_schedule_last_run(self, schedule_id: str, now_ts: float) -> None:
        """
        Update the last run time for a schedule.
        
        Args:
            schedule_id: The schedule ID
            now_ts: Current timestamp
        """
        interval = self._query(
            "SELECT interval_seconds FROM schedules WHERE id = ?",
            (schedule_id,)
        )
        
        interval_seconds = interval[0]['interval_seconds'] if interval else 3600
        next_run = now_ts + interval_seconds
        
        self._execute(
            "UPDATE schedules SET last_run = ?, next_run = ? WHERE id = ?",
            (float(now_ts), float(next_run), schedule_id)
        )
    
    def list_schedules(self) -> List[Dict[str, Any]]:
        """
        List all schedules.
        
        Returns:
            List of schedule dictionaries
        """
        return self._query("SELECT * FROM schedules ORDER BY next_run ASC")
    
    def enable_schedule(self, name: str) -> bool:
        """
        Enable a schedule.
        
        Args:
            name: The schedule name
            
        Returns:
            True if updated, False otherwise
        """
        cursor = self._execute(
            "UPDATE schedules SET enabled = 1 WHERE name = ?",
            (str(name),)
        )
        return cursor.rowcount > 0
    
    def disable_schedule(self, name: str) -> bool:
        """
        Disable a schedule.
        
        Args:
            name: The schedule name
            
        Returns:
            True if updated, False otherwise
        """
        cursor = self._execute(
            "UPDATE schedules SET enabled = 0 WHERE name = ?",
            (str(name),)
        )
        return cursor.rowcount > 0
    
    def remove_schedule(self, name: str) -> bool:
        """
        Remove a schedule.
        
        Args:
            name: The schedule name
            
        Returns:
            True if removed, False otherwise
        """
        cursor = self._execute("DELETE FROM schedules WHERE name = ?", (str(name),))
        return cursor.rowcount > 0
    
    # ============================================================
    # Statistics & Utility Methods
    # ============================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with counts for each table
        """
        stats = {}
        tables = ['facts', 'notes', 'knowledge', 'history', 'memories', 'skills', 'schedules']
        
        for table in tables:
            results = self._query(f"SELECT COUNT(*) as count FROM {table}")
            stats[table] = results[0]['count'] if results else 0
        
        return stats
    
    def cleanup_all(self, days: int = 30) -> Dict[str, int]:
        """
        Clean up all old data.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Dictionary with counts of deleted items
        """
        cutoff = time.time() - (days * 86400)
        
        # Clean up history
        history_cursor = self._execute("DELETE FROM history WHERE created_at < ?", (cutoff,))
        history_deleted = history_cursor.rowcount
        
        # Clean up memories (duplicates)
        memories_deleted = self.cleanup_memories()
        
        return {
            "history": history_deleted,
            "memories": memories_deleted
        }
    
    def close(self) -> None:
        """Close the database connection."""
        with self.lock:
            if self.conn:
                self.conn.close()
                self.conn = None


# Singleton instance
db = Database()
