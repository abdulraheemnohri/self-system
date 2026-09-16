#!/usr/bin/env python3
"""
Safety Governor for the Complete Self System

Provides:
- Tool permissions management
- Rate limiting
- Approval workflows
- Audit logging
- Security policies
"""

import sqlite3
import threading
import time
import json
import uuid
import hashlib
from typing import Dict, Any, Optional, Tuple, List


class SafetyGovernor:
    """
    Safety Governor ensures secure execution of tools and actions.
    
    Features:
    - Permission management for tools
    - Rate limiting
    - Approval workflows for sensitive operations
    - Comprehensive audit logging
    - Configurable security policies
    """
    
    def __init__(self, db_path: str = "storage/safety.db"):
        """
        Initialize the Safety Governor.
        
        Args:
            db_path: Path to the SQLite database for safety data
        """
        self.db_path = db_path
        self.lock = threading.RLock()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Default permissions (tool_name: enabled)
        self.default_permissions: Dict[str, bool] = {
            "get_current_time": True,
            "calculate": True,
            "search_memory": True,
            "save_note": True,
            "remember_fact": True,
            "fetch_url": True,
            "browser_navigate": True,
            "browser_text": True,
            "browser_fill": False,
            "browser_click": False,
            "run_plugin": False,
            "generate_skill": False,
            "install_skill": False,
            "file_write": False,
            "file_read": False,
            "shell": False,
            "execute_code": False,
        }
        
        self.default_approval_required: set = {
            "browser_fill",
            "browser_click", 
            "run_plugin",
            "generate_skill",
            "install_skill",
            "file_write",
            "shell",
            "execute_code",
        }
        
        self.default_rate_limits: Dict[str, int] = {
            "fetch_url": 60,
            "browser_navigate": 30,
            "generate_skill": 5,
            "run_plugin": 20,
            "search_memory": 100,
            "calculate": 1000,
        }
        
        self.create_tables()
    
    def execute(self, query: str, args: tuple = ()) -> sqlite3.Cursor:
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(query, args)
            self.conn.commit()
            return cur
    
    def query(self, query: str, args: tuple = ()) -> List[Dict[str, Any]]:
        with self.lock:
            cur = self.conn.cursor()
            cur.execute(query, args)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    
    def create_tables(self) -> None:
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS tool_permissions (
                name TEXT PRIMARY KEY,
                enabled INTEGER DEFAULT 0,
                requires_approval INTEGER DEFAULT 0,
                max_per_hour INTEGER DEFAULT 60,
                description TEXT
            )
            """
        )
        
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS audit (
                id TEXT PRIMARY KEY,
                ts REAL,
                tool TEXT,
                args TEXT,
                status TEXT,
                detail TEXT,
                user TEXT,
                session_id TEXT
            )
            """
        )
        
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS approvals (
                id TEXT PRIMARY KEY,
                tool TEXT,
                args_hash TEXT,
                status TEXT,
                created_at REAL,
                resolved_at REAL,
                resolved_by TEXT
            )
            """
        )
        
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS security_policies (
                id TEXT PRIMARY KEY,
                policy_name TEXT UNIQUE,
                policy_value TEXT,
                description TEXT
            )
            """
        )
        
        for tool, enabled in self.default_permissions.items():
            requires_approval = 1 if tool in self.default_approval_required else 0
            max_per_hour = self.default_rate_limits.get(tool, 60)
            self.execute(
                """
                INSERT OR IGNORE INTO tool_permissions 
                (name, enabled, requires_approval, max_per_hour, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (tool, 1 if enabled else 0, requires_approval, max_per_hour, f"Default permission for {tool}")
            )
    
    def args_hash(self, args: Dict[str, Any]) -> str:
        raw = json.dumps(args, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
    
    def audit(self, tool: str, args: Dict[str, Any], status: str, detail: str = "", 
              user: str = "system", session_id: str = "") -> None:
        self.execute(
            """
            INSERT INTO audit (id, ts, tool, args, status, detail, user, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                time.time(),
                tool,
                json.dumps(args, ensure_ascii=False),
                status,
                str(detail)[:2000],
                user,
                session_id
            )
        )
    
    def get_permission(self, tool: str) -> Dict[str, Any]:
        rows = self.query(
            "SELECT * FROM tool_permissions WHERE name = ?",
            (tool,)
        )
        if rows:
            return rows[0]
        return {
            "name": tool,
            "enabled": 0,
            "requires_approval": 1,
            "max_per_hour": 10,
            "description": f"Unknown tool: {tool}"
        }
    
    def can_execute(self, tool: str, args: Dict[str, Any], user: str = "system", 
                    session_id: str = "") -> Tuple[bool, str]:
        permission = self.get_permission(tool)
        
        if not permission["enabled"]:
            self.audit(tool, args, "blocked", "Tool disabled", user, session_id)
            return False, "Tool disabled"
        
        one_hour_ago = time.time() - 3600
        max_per_hour = permission["max_per_hour"]
        
        rows = self.query(
            """
            SELECT COUNT(*) AS count
            FROM audit
            WHERE tool = ?
              AND status = 'ok'
              AND ts > ?
            """,
            (tool, one_hour_ago)
        )
        
        count = rows[0]["count"] if rows else 0
        
        if count >= max_per_hour:
            self.audit(tool, args, "blocked", "Rate limit exceeded", user, session_id)
            return False, f"Rate limit exceeded ({count}/{max_per_hour} calls this hour)"
        
        if permission["requires_approval"]:
            if not self.has_recent_approval(tool, args):
                approval_id = self.request_approval(tool, args, user)
                self.audit(tool, args, "blocked", f"Approval required: {approval_id}", user, session_id)
                return False, f"Approval required: {approval_id}"
        
        return True, "ok"
    
    def has_recent_approval(self, tool: str, args: Dict[str, Any]) -> bool:
        h = self.args_hash(args)
        rows = self.query(
            """
            SELECT * FROM approvals
            WHERE tool = ?
              AND args_hash = ?
              AND status = 'approved'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (tool, h)
        )
        return bool(rows)
    
    def request_approval(self, tool: str, args: Dict[str, Any], user: str = "system") -> str:
        h = self.args_hash(args)
        approval_id = str(uuid.uuid4())
        self.execute(
            """
            INSERT INTO approvals (id, tool, args_hash, status, created_at, resolved_at, resolved_by)
            VALUES (?, ?, ?, 'pending', ?, 0, '')
            """,
            (approval_id, tool, h, time.time())
        )
        self.audit(tool, args, "approval_requested", f"Approval requested: {approval_id}", user)
        return approval_id
    
    def wrap_tool(self, tool_name: str, handler: callable) -> callable:
        def wrapped(args: Optional[Dict[str, Any]] = None, user: str = "system", 
                    session_id: str = "") -> Any:
            args = args or {}
            allowed, reason = self.can_execute(tool_name, args, user, session_id)
            
            if not allowed:
                self.audit(tool_name, args, "blocked", reason, user, session_id)
                return f"Safety blocked {tool_name}: {reason}"
            
            try:
                result = handler(args)
                self.audit(tool_name, args, "ok", str(result)[:1000], user, session_id)
                return result
            except Exception as exc:
                self.audit(tool_name, args, "error", str(exc), user, session_id)
                return f"Tool error in {tool_name}: {exc}"
        
        return wrapped
    
    def get_audit_logs(self, limit: int = 100, tool: Optional[str] = None, 
                       status: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM audit ORDER BY ts DESC LIMIT ?"
        params: list = [limit]
        
        if tool:
            query = "SELECT * FROM audit WHERE tool = ? ORDER BY ts DESC LIMIT ?"
            params = [tool, limit]
        
        if status:
            if tool:
                query = "SELECT * FROM audit WHERE tool = ? AND status = ? ORDER BY ts DESC LIMIT ?"
                params = [tool, status, limit]
            else:
                query = "SELECT * FROM audit WHERE status = ? ORDER BY ts DESC LIMIT ?"
                params = [status, limit]
        
        return self.query(query, tuple(params))
    
    def cleanup_old_logs(self, days: int = 90) -> int:
        cutoff = time.time() - (days * 86400)
        cur = self.execute("DELETE FROM audit WHERE ts < ?", (cutoff,))
        audit_deleted = cur.rowcount
        cur = self.execute("DELETE FROM approvals WHERE created_at < ?", (cutoff,))
        approvals_deleted = cur.rowcount
        return audit_deleted + approvals_deleted
    
    def close(self) -> None:
        self.conn.close()
