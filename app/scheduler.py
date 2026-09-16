#!/usr/bin/env python3
"""
Autonomous Scheduler for the Complete Self System

Provides:
- Periodic task execution
- Memory cleanup
- Self-review and learning
- Skill generation proposals
- Scheduled maintenance
"""

import os
import time
import json
import uuid
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable


class AutonomousScheduler:
    """
    Scheduler for autonomous tasks.
    
    Features:
    - Periodic task execution
    - Thread-based scheduling
    - Task persistence
    - Graceful shutdown
    """
    
    def __init__(self, db_path: str = "storage/scheduler.db",
                 action_runner: Optional[Callable[[str, Dict[str, Any]], Any]] = None):
        """
        Initialize the AutonomousScheduler.
        
        Args:
            db_path: Path to the SQLite database
            action_runner: Function to run scheduled actions
        """
        self.db_path = db_path
        self.action_runner = action_runner
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self.lock = threading.RLock()
        
        # Initialize database
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize the scheduler database."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        with self.lock:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS schedules (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE,
                    action TEXT,
                    interval_seconds INTEGER,
                    last_run REAL,
                    next_run REAL,
                    enabled INTEGER DEFAULT 1,
                    description TEXT,
                    created_at REAL
                )
                """
            )
            
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS task_logs (
                    id TEXT PRIMARY KEY,
                    schedule_id TEXT,
                    action TEXT,
                    status TEXT,
                    result TEXT,
                    duration REAL,
                    created_at REAL,
                    FOREIGN KEY (schedule_id) REFERENCES schedules(id)
                )
                """
            )
        
        conn.commit()
        conn.close()
    
    def _get_conn(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def add_schedule(self, name: str, action: str, interval_seconds: int,
                     description: str = "", enabled: bool = True) -> Dict[str, Any]:
        """
        Add a new scheduled task.
        
        Args:
            name: Unique name for the schedule
            action: Action to execute
            interval_seconds: Seconds between executions
            description: Description of the task
            enabled: Whether the task is enabled
            
        Returns:
            Dictionary with schedule info
        """
        schedule_id = str(uuid.uuid4())
        now = time.time()
        next_run = now + interval_seconds
        
        conn = self._get_conn()
        try:
            with self.lock:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO schedules 
                    (id, name, action, interval_seconds, last_run, next_run, enabled, description, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (schedule_id, name, action, interval_seconds, 0, next_run, 
                     1 if enabled else 0, description, now)
                )
            conn.commit()
            
            return {
                "success": True,
                "id": schedule_id,
                "name": name,
                "action": action,
                "interval_seconds": interval_seconds,
                "next_run": next_run
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def remove_schedule(self, name: str) -> Dict[str, Any]:
        """
        Remove a scheduled task.
        
        Args:
            name: Name of the schedule to remove
            
        Returns:
            Dictionary with removal result
        """
        conn = self._get_conn()
        try:
            with self.lock:
                conn.execute("DELETE FROM schedules WHERE name = ?", (name,))
            conn.commit()
            
            if conn.total_changes > 0:
                return {"success": True, "message": f"Schedule '{name}' removed"}
            else:
                return {"success": False, "error": f"Schedule '{name}' not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def list_schedules(self) -> List[Dict[str, Any]]:
        """List all scheduled tasks."""
        conn = self._get_conn()
        try:
            with self.lock:
                rows = conn.execute(
                    "SELECT * FROM schedules ORDER BY next_run ASC"
                ).fetchall()
            
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def get_schedule(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a schedule by name.
        
        Args:
            name: Name of the schedule
            
        Returns:
            Schedule dictionary or None
        """
        conn = self._get_conn()
        try:
            with self.lock:
                row = conn.execute(
                    "SELECT * FROM schedules WHERE name = ?", (name,)
                ).fetchone()
            
            return dict(row) if row else None
        finally:
            conn.close()
    
    def enable_schedule(self, name: str) -> Dict[str, Any]:
        """Enable a schedule."""
        conn = self._get_conn()
        try:
            with self.lock:
                conn.execute(
                    "UPDATE schedules SET enabled = 1 WHERE name = ?", (name,)
                )
            conn.commit()
            
            if conn.total_changes > 0:
                return {"success": True, "message": f"Schedule '{name}' enabled"}
            else:
                return {"success": False, "error": f"Schedule '{name}' not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def disable_schedule(self, name: str) -> Dict[str, Any]:
        """Disable a schedule."""
        conn = self._get_conn()
        try:
            with self.lock:
                conn.execute(
                    "UPDATE schedules SET enabled = 0 WHERE name = ?", (name,)
                )
            conn.commit()
            
            if conn.total_changes > 0:
                return {"success": True, "message": f"Schedule '{name}' disabled"}
            else:
                return {"success": False, "error": f"Schedule '{name}' not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def log_task(self, schedule_id: str, action: str, status: str, 
                 result: str = "", duration: float = 0.0) -> None:
        """
        Log a task execution.
        
        Args:
            schedule_id: ID of the schedule
            action: Action that was executed
            status: Status of execution
            result: Result of execution
            duration: Duration in seconds
        """
        conn = self._get_conn()
        try:
            with self.lock:
                conn.execute(
                    """
                    INSERT INTO task_logs 
                    (id, schedule_id, action, status, result, duration, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (str(uuid.uuid4()), schedule_id, action, status, result[:2000], duration, time.time())
                )
            conn.commit()
        finally:
            conn.close()
    
    def get_task_logs(self, limit: int = 100, action: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get task execution logs.
        
        Args:
            limit: Maximum number of logs to return
            action: Filter by action name
            
        Returns:
            List of task log dictionaries
        """
        conn = self._get_conn()
        try:
            with self.lock:
                if action:
                    rows = conn.execute(
                        "SELECT * FROM task_logs WHERE action = ? ORDER BY created_at DESC LIMIT ?",
                        (action, limit)
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM task_logs ORDER BY created_at DESC LIMIT ?",
                        (limit,)
                    ).fetchall()
            
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def add_default_tasks(self) -> None:
        """Add default scheduled tasks."""
        defaults = [
            {
                "name": "memory_cleanup",
                "action": "memory_cleanup",
                "interval_seconds": 60 * 60,  # 1 hour
                "description": "Clean up old history and duplicate memories"
            },
            {
                "name": "self_review",
                "action": "self_review",
                "interval_seconds": 60 * 60 * 4,  # 4 hours
                "description": "Review recent conversations and suggest improvements"
            },
            {
                "name": "periodic_learning",
                "action": "periodic_learning",
                "interval_seconds": 60 * 60 * 12,  # 12 hours
                "description": "Summarize recent notes into long-term memory"
            },
            {
                "name": "skill_proposal",
                "action": "skill_proposal",
                "interval_seconds": 60 * 60 * 24,  # 24 hours
                "description": "Propose new skills based on recent usage"
            },
            {
                "name": "health_check",
                "action": "health_check",
                "interval_seconds": 60 * 60 * 6,  # 6 hours
                "description": "Check system health and dependencies"
            }
        ]
        
        for task in defaults:
            existing = self.get_schedule(task["name"])
            if not existing:
                self.add_schedule(**task)
    
    def start(self) -> None:
        """Start the scheduler thread."""
        if self.thread:
            return
        
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
    
    def stop(self) -> None:
        """Stop the scheduler."""
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None
    
    def _loop(self) -> None:
        """Main scheduler loop."""
        while not self.stop_event.is_set():
            try:
                self._check_due_tasks()
            except Exception as e:
                print(f"[Scheduler] Error: {e}")
            
            # Sleep for a short interval
            self.stop_event.wait(10)
    
    def _check_due_tasks(self) -> None:
        """Check and execute due tasks."""
        conn = self._get_conn()
        try:
            now = time.time()
            
            with self.lock:
                # Get all enabled schedules that are due
                rows = conn.execute(
                    """
                    SELECT * FROM schedules 
                    WHERE enabled = 1 AND next_run <= ?
                    ORDER BY next_run ASC
                    """,
                    (now,)
                ).fetchall()
            
            for row in rows:
                schedule = dict(row)
                schedule_id = schedule["id"]
                name = schedule["name"]
                action = schedule["action"]
                interval = schedule["interval_seconds"]
                
                try:
                    # Execute the action
                    start_time = time.time()
                    
                    if self.action_runner:
                        result = self.action_runner(action, {"schedule": name})
                    else:
                        result = f"No action runner configured for: {action}"
                    
                    duration = time.time() - start_time
                    
                    # Log the task
                    self.log_task(
                        schedule_id=schedule_id,
                        action=action,
                        status="success",
                        result=str(result)[:1000],
                        duration=duration
                    )
                    
                    print(f"[Scheduler] Executed: {name} ({action}) - {result}")
                    
                    # Update next run time
                    next_run = now + interval
                    with self.lock:
                        conn.execute(
                            "UPDATE schedules SET last_run = ?, next_run = ? WHERE id = ?",
                            (now, next_run, schedule_id)
                        )
                    conn.commit()
                    
                except Exception as e:
                    duration = time.time() - start_time
                    self.log_task(
                        schedule_id=schedule_id,
                        action=action,
                        status="error",
                        result=str(e)[:1000],
                        duration=duration
                    )
                    print(f"[Scheduler] Error in {name}: {e}")
                    
                    # Still update next run to prevent repeated failures
                    next_run = now + interval
                    with self.lock:
                        conn.execute(
                            "UPDATE schedules SET last_run = ?, next_run = ? WHERE id = ?",
                            (now, next_run, schedule_id)
                        )
                    conn.commit()
        
        finally:
            conn.close()


# ============================================================
# Default Autonomous Actions
# ============================================================

def memory_cleanup(ctx: Dict[str, Any]) -> str:
    """
    Clean up old history and duplicate memories.
    
    Args:
        ctx: Context dictionary with db, cfg, etc.
        
    Returns:
        Result message
    """
    db = ctx.get("db")
    if db:
        # Clean up old history
        if hasattr(db, "cleanup_history"):
            db.cleanup_history(days=30)
        
        # Clean up duplicate memories
        if hasattr(db, "cleanup_memories"):
            db.cleanup_memories()
        
        return "Memory cleanup completed"
    return "Memory cleanup skipped (no db)"


def self_review(ctx: Dict[str, Any]) -> str:
    """
    Review recent conversations and suggest improvements.
    
    Args:
        ctx: Context dictionary with db, cfg, etc.
        
    Returns:
        Result message
    """
    db = ctx.get("db")
    cfg = ctx.get("cfg")
    simple_llm = ctx.get("simple_llm")
    embedder = ctx.get("embedder")
    
    if not db or not simple_llm:
        return "Self-review skipped (missing dependencies)"
    
    try:
        # Get recent history
        history = db.get_history(30) if hasattr(db, "get_history") else []
        
        if not history:
            return "No history available for self-review"
        
        # Format conversation
        conversation = "\n".join(
            f"{item.get('role', 'unknown')}: {item.get('content', '')}"
            for item in history
        )
        
        # Ask LLM to review
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI reliability reviewer. "
                    "Review this conversation and suggest ONE concrete improvement. "
                    "Be concise and practical."
                )
            },
            {
                "role": "user",
                "content": conversation[:7000]
            }
        ]
        
        reply = simple_llm(messages)
        
        # Save review
        if hasattr(db, "add_note"):
            db.add_note(reply, tags=["self_review", "autonomous"])
        
        # Add to vector memory
        if embedder and hasattr(db, "add_memory"):
            from app.vector_store import remember_text
            remember_text(db, embedder, reply, kind="self_review")
        
        return f"Self-review completed: {reply[:100]}..."
    
    except Exception as e:
        return f"Self-review error: {e}"


def periodic_learning(ctx: Dict[str, Any]) -> str:
    """
    Summarize recent notes into long-term memory.
    
    Args:
        ctx: Context dictionary with db, cfg, etc.
        
    Returns:
        Result message
    """
    db = ctx.get("db")
    simple_llm = ctx.get("simple_llm")
    embedder = ctx.get("embedder")
    
    if not db or not simple_llm:
        return "Periodic learning skipped (missing dependencies)"
    
    try:
        # Get recent notes
        notes = db.list_notes(limit=20) if hasattr(db, "list_notes") else []
        
        if not notes:
            return "No notes available for periodic learning"
        
        # Combine note texts
        text = "\n\n".join(row.get("text", "") for row in notes)
        
        # Ask LLM to summarize
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a knowledge distiller. "
                    "Summarize the most useful information from these notes "
                    "into concise, durable knowledge statements."
                )
            },
            {
                "role": "user",
                "content": text[:7000]
            }
        ]
        
        reply = simple_llm(messages)
        
        if reply and not reply.startswith("[API"):
            # Save summary
            if hasattr(db, "add_note"):
                db.add_note(reply, tags=["periodic_learning", "autonomous"])
            
            # Add to vector memory
            if embedder and hasattr(db, "add_memory"):
                from app.vector_store import remember_text
                remember_text(db, embedder, reply, kind="periodic_learning")
            
            return f"Periodic learning: {reply[:100]}..."
        
        return "Periodic learning skipped (API unavailable)"
    
    except Exception as e:
        return f"Periodic learning error: {e}"


def skill_proposal(ctx: Dict[str, Any]) -> str:
    """
    Propose new skills based on recent usage.
    
    Args:
        ctx: Context dictionary with db, cfg, etc.
        
    Returns:
        Result message
    """
    db = ctx.get("db")
    simple_llm = ctx.get("simple_llm")
    
    if not db or not simple_llm:
        return "Skill proposal skipped (missing dependencies)"
    
    try:
        # Get recent history
        history = db.get_history(50) if hasattr(db, "get_history") else []
        
        # Get recent notes
        notes = db.list_notes(limit=10) if hasattr(db, "list_notes") else []
        
        # Combine for context
        context = "\n\n".join(
            [f"{item.get('role', 'unknown')}: {item.get('content', '')}" for item in history[:20]] +
            [f"Note: {row.get('text', '')}" for row in notes]
        )
        
        # Ask LLM to propose a skill
        messages = [
            {
                "role": "system",
                "content": (
                    "Based on recent AI assistant usage, propose ONE new plugin skill. "
                    "Return JSON only with: "
                    '{"name": "skill_name", "description": "what it does", "risk_level": "low|medium|high"}'
                )
            },
            {
                "role": "user",
                "content": context[:7000]
            }
        ]
        
        reply = simple_llm(messages)
        
        # Save proposal
        if hasattr(db, "add_note"):
            db.add_note(reply, tags=["skill_proposal", "autonomous"])
        
        return f"Skill proposal: {reply[:100]}..."
    
    except Exception as e:
        return f"Skill proposal error: {e}"


def health_check(ctx: Dict[str, Any]) -> str:
    """
    Check system health and dependencies.
    
    Args:
        ctx: Context dictionary with db, cfg, etc.
        
    Returns:
        Result message
    """
    checks = []
    issues = []
    
    # Check database
    db = ctx.get("db")
    if db:
        try:
            if hasattr(db, "get_facts"):
                facts = db.get_facts()
                checks.append(f"Database OK ({len(facts)} facts)")
        except Exception as e:
            issues.append(f"Database error: {e}")
    else:
        issues.append("No database configured")
    
    # Check LLM
    cfg = ctx.get("cfg")
    if cfg:
        base_url = cfg.get("base_url")
        api_key = cfg.get("api_key")
        model = cfg.get("model")
        
        if base_url and model:
            checks.append(f"LLM configured (model: {model})")
        else:
            issues.append("LLM not properly configured")
        
        if not api_key and "openai" in (base_url or ""):
            issues.append("API key missing for OpenAI")
    else:
        issues.append("No configuration available")
    
    # Check vector store
    vector = ctx.get("vector")
    if vector:
        checks.append("Vector store OK")
    else:
        issues.append("Vector store not configured")
    
    # Check tools
    tools = ctx.get("tools")
    if tools:
        tool_count = len(tools.names()) if hasattr(tools, "names") else 0
        checks.append(f"Tools OK ({tool_count} tools)")
    else:
        issues.append("Tools not configured")
    
    if issues:
        return f"Health check: {len(checks)} OK, {len(issues)} issues - {", ".join(issues[:3])}"
    else:
        return f"Health check: All {len(checks)} systems OK"


# Map action names to functions
AUTONOMOUS_ACTIONS = {
    "memory_cleanup": memory_cleanup,
    "self_review": self_review,
    "periodic_learning": periodic_learning,
    "skill_proposal": skill_proposal,
    "health_check": health_check,
}


def get_autonomous_action(action_name: str) -> Optional[Callable]:
    """Get an autonomous action function by name."""
    return AUTONOMOUS_ACTIONS.get(action_name)


# ============================================================
# Helper function to create scheduler with default actions
# ============================================================

def create_scheduler(db_path: str = "storage/scheduler.db",
                     ctx: Optional[Dict[str, Any]] = None) -> AutonomousScheduler:
    """
    Create a scheduler with default autonomous actions.
    
    Args:
        db_path: Path to the SQLite database
        ctx: Context dictionary to pass to actions
        
    Returns:
        AutonomousScheduler instance
    """
    def action_runner(action: str, params: Dict[str, Any]) -> Any:
        """Run an autonomous action."""
        if ctx:
            # Add params to context
            run_ctx = {**ctx, **params}
        else:
            run_ctx = params
        
        func = get_autonomous_action(action)
        if func:
            return func(run_ctx)
        else:
            return f"Unknown autonomous action: {action}"
    
    scheduler = AutonomousScheduler(db_path, action_runner)
    scheduler.add_default_tasks()
    return scheduler
