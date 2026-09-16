"""
Self-Growth Engine for Complete Self System

Provides self-reporting, self-critique, self-improvement proposals, goal management,
feedback learning, failure memory, memory consolidation, selective forgetting,
self-benchmarking, prompt evolution, skill versioning, and self-settings.
"""

import json
import uuid
import datetime
import time


DEFAULT_SELF_SETTINGS = {
    "enabled": True,
    "auto_reflect": True,
    "auto_consolidate": True,
    "auto_forget": False,
    "auto_benchmark": False,
    "auto_skill_proposals": False,

    "prompt_evolution": False,
    "self_test_skills": True,
    "require_human_approval": True,

    "max_skill_attempts": 3,
    "min_feedback_score": 0.6,
    "min_confidence_for_action": 0.65,

    "memory_retention_days": 30,
    "self_review_interval_minutes": 240,
    "consolidation_interval_minutes": 720,
    "benchmark_interval_minutes": 1440,
    "skill_proposal_interval_minutes": 2880,

    "curiosity_level": 0.30,
    "exploration_mode": "safe",
    "allow_self_prompt_activation": False,
    "allow_automatic_skill_install": False,
}


class SelfGrowthEngine:
    def __init__(self, ctx):
        self.ctx = ctx
        self.db = ctx["db"]
        self.cfg = ctx.get("cfg", {})
        self.ensure_tables()
        self.ensure_settings()

    def ensure_tables(self):
        self.db.execute("CREATE TABLE IF NOT EXISTS self_settings (key TEXT PRIMARY KEY, value TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS self_events (id TEXT PRIMARY KEY, ts TEXT, kind TEXT, payload TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS self_goals (id TEXT PRIMARY KEY, title TEXT, description TEXT, status TEXT, priority INTEGER, created_at TEXT, completed_at TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS self_feedback (id TEXT PRIMARY KEY, ts TEXT, target TEXT, rating REAL, comment TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS self_failures (id TEXT PRIMARY KEY, ts TEXT, context TEXT, error TEXT, analysis TEXT, fix_status TEXT)")
        self.db.execute("CREATE TABLE IF NOT EXISTS self_metrics (id TEXT PRIMARY KEY, ts TEXT, name TEXT, value REAL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS self_prompt_versions (id TEXT PRIMARY KEY, ts TEXT, prompt TEXT, score REAL, active INTEGER)")
        self.db.execute("CREATE TABLE IF NOT EXISTS skill_versions (id TEXT PRIMARY KEY, name TEXT, version INTEGER, code TEXT, status TEXT, created_at TEXT)")

    def ensure_settings(self):
        overrides = self.cfg.get("self_growth", {})
        if not isinstance(overrides, dict):
            overrides = {}
        for key, default_value in DEFAULT_SELF_SETTINGS.items():
            value = overrides.get(key, default_value)
            self.db.execute("INSERT OR IGNORE INTO self_settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))

    def get_setting(self, key):
        rows = self.db.query("SELECT value FROM self_settings WHERE key = ?", (key,))
        if not rows:
            return DEFAULT_SELF_SETTINGS.get(key)
        try:
            return json.loads(rows[0]["value"])
        except Exception:
            return rows[0]["value"]

    def set_setting(self, key, value):
        allowed = set(DEFAULT_SELF_SETTINGS.keys())
        if key not in allowed:
            return f"Unknown self setting: {key}"
        if key in {"max_skill_attempts", "memory_retention_days", "self_review_interval_minutes", "consolidation_interval_minutes", "benchmark_interval_minutes", "skill_proposal_interval_minutes"}:
            try:
                value = int(value)
            except Exception:
                return f"{key} must be an integer."
        if key in {"min_feedback_score", "min_confidence_for_action", "curiosity_level"}:
            try:
                value = float(value)
            except Exception:
                return f"{key} must be a number."
        if key in {"enabled", "auto_reflect", "auto_consolidate", "auto_forget", "auto_benchmark", "auto_skill_proposals", "prompt_evolution", "self_test_skills", "require_human_approval", "allow_self_prompt_activation", "allow_automatic_skill_install"}:
            value = str(value).strip().lower() in {"1", "true", "yes", "on", "y"}
        self.db.execute("INSERT OR REPLACE INTO self_settings (key, value) VALUES (?, ?)", (key, json.dumps(value)))
        self.log_event("setting_changed", {"key": key, "value": value})
        return f"Set self_growth.{key} = {value}"

    def all_settings(self):
        rows = self.db.query("SELECT key, value FROM self_settings")
        settings = {}
        for row in rows:
            try:
                settings[row["key"]] = json.loads(row["value"])
            except Exception:
                settings[row["key"]] = row["value"]
        return settings

    def log_event(self, kind, payload=None):
        self.db.execute("INSERT INTO self_events (id, ts, kind, payload) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), datetime.datetime.now().isoformat(timespec="seconds"), kind, json.dumps(payload or {}, ensure_ascii=False)))

    def record_metric(self, name, value):
        self.db.execute("INSERT INTO self_metrics (id, ts, name, value) VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), datetime.datetime.now().isoformat(timespec="seconds"), name, float(value)))

    def record_failure(self, context, error, analysis="", fix_status="open"):
        self.db.execute("INSERT INTO self_failures (id, ts, context, error, analysis, fix_status) VALUES (?, ?, ?, ?, ?, ?)", (str(uuid.uuid4()), datetime.datetime.now().isoformat(timespec="seconds"), str(context), str(error), str(analysis), fix_status))
        self.log_event("failure", {"context": context, "error": error})

    def record_feedback(self, target, rating, comment=""):
        if str(rating).lower() in {"good", "positive", "up", "like", "yes"}:
            rating = 1.0
        elif str(rating).lower() in {"bad", "negative", "down", "dislike", "no"}:
            rating = -1.0
        else:
            try:
                rating = float(rating)
            except Exception:
                rating = 0.0
        self.db.execute("INSERT INTO self_feedback (id, ts, target, rating, comment) VALUES (?, ?, ?, ?, ?)", (str(uuid.uuid4()), datetime.datetime.now().isoformat(timespec="seconds"), target, rating, comment))
        self.log_event("feedback", {"target": target, "rating": rating})
        return "Feedback recorded."

    def add_goal(self, title, description="", priority=3):
        goal_id = str(uuid.uuid4())
        self.db.execute("INSERT INTO self_goals (id, title, description, status, priority, created_at, completed_at) VALUES (?, ?, ?, 'open', ?, ?, NULL)", (goal_id, title, description, int(priority), datetime.datetime.now().isoformat(timespec="seconds")))
        self.log_event("goal_added", {"id": goal_id, "title": title})
        return f"Goal added: {title}"

    def complete_goal(self, goal_id):
        self.db.execute("UPDATE self_goals SET status = 'complete', completed_at = ? WHERE id = ?", (datetime.datetime.now().isoformat(timespec="seconds"), goal_id))
        self.log_event("goal_completed", {"id": goal_id})
        return "Goal marked complete."

    def list_goals(self, status=None):
        if status:
            rows = self.db.query("SELECT id, title, description, status, priority, created_at, completed_at FROM self_goals WHERE status = ? ORDER BY priority ASC, created_at DESC", (status,))
        else:
            rows = self.db.query("SELECT id, title, description, status, priority, created_at, completed_at FROM self_goals ORDER BY priority ASC, created_at DESC")
        return rows

    def next_goal(self):
        rows = self.db.query("SELECT id, title, description FROM self_goals WHERE status = 'open' ORDER BY priority ASC, created_at ASC LIMIT 1")
        return rows[0] if rows else None

    def self_report(self):
        report = ["=== SELF REPORT ==="]
        try:
            history_count = self.db.query("SELECT COUNT(*) AS c FROM history")[0]["c"]
        except:
            history_count = 0
        try:
            note_count = self.db.query("SELECT COUNT(*) AS c FROM notes")[0]["c"]
        except:
            note_count = 0
        try:
            memory_count = self.db.query("SELECT COUNT(*) AS c FROM memories")[0]["c"]
        except:
            memory_count = 0
        try:
            knowledge_count = self.db.query("SELECT COUNT(*) AS c FROM knowledge")[0]["c"]
        except:
            knowledge_count = 0
        report.append(f"history items: {history_count}")
        report.append(f"notes: {note_count}")
        report.append(f"vector memories: {memory_count}")
        report.append(f"knowledge items: {knowledge_count}")
        failures = self.db.query("SELECT context, error, fix_status FROM self_failures ORDER BY ts DESC LIMIT 5")
        report.append("\nRecent failures:")
        if failures:
            for f in failures:
                report.append(f"- [{f['fix_status']}] {f['context']} :: {f['error']}")
        else:
            report.append("- none")
        goals = self.list_goals("open")
        report.append("\nOpen goals:")
        if goals:
            for g in goals[:5]:
                report.append(f"- [{g['priority']}] {g['title']}")
        else:
            report.append("- none")
        feedback = self.db.query("SELECT target, rating, comment FROM self_feedback ORDER BY ts DESC LIMIT 5")
        report.append("\nRecent feedback:")
        if feedback:
            for item in feedback:
                report.append(f"- {item['target']} rating={item['rating']} :: {item['comment']}")
        else:
            report.append("- none")
        return "\n".join(report)

    def critique_recent(self, limit=12):
        simple_llm = self.ctx.get("simple_llm")
        if not simple_llm:
            return "simple_llm not available in ctx."
        history = self.db.get_history(limit)
        if not history:
            return "No recent history to critique."
        conversation = "\n".join(f"{row.get('role', 'unknown')}: {row.get('content', '')}" for row in history)
        prompt = f"""Review this AI assistant conversation. Identify: 1. What was done well. 2. What was weak or unsafe. 3. What should be improved next time. Be concise. Conversation: {conversation[:8000]}"""
        reply = simple_llm([{"role": "system", "content": "You are a self-improvement reviewer for an AI agent."}, {"role": "user", "content": prompt}])
        self.db.add_note(reply, tags="self_critique")
        if "vector" in self.ctx:
            self.ctx["vector"].add(reply, kind="self_critique")
        self.log_event("self_critique", {"summary": reply[:500]})
        return reply

    def propose_improvements(self):
        simple_llm = self.ctx.get("simple_llm")
        if not simple_llm:
            return "simple_llm not available in ctx."
        failures = self.db.query("SELECT context, error, analysis FROM self_failures ORDER BY ts DESC LIMIT 10")
        feedback = self.db.query("SELECT target, rating, comment FROM self_feedback ORDER BY ts DESC LIMIT 10")
        failure_text = "\n".join(f"- {f['context']} :: {f['error']}" for f in failures) or "No recorded failures."
        feedback_text = "\n".join(f"- {f['target']} rating={f['rating']} :: {f['comment']}" for f in feedback) or "No recorded feedback."
        prompt = f"""Based on these failures and feedback items, propose 3 safe improvements for this AI system. Failures: {failure_text} Feedback: {feedback_text} Return: 1. Immediate fix 2. Memory improvement 3. Skill/tool improvement Keep suggestions safe and concrete."""
        reply = simple_llm([{"role": "system", "content": "You propose safe improvements for an AI agent."}, {"role": "user", "content": prompt}])
        self.db.add_note(reply, tags="improvement_proposal")
        if "vector" in self.ctx:
            self.ctx["vector"].add(reply, kind="improvement_proposal")
        self.log_event("improvement_proposal", {"summary": reply[:500]})
        return reply

    def consolidate_memory(self):
        simple_llm = self.ctx.get("simple_llm")
        if not simple_llm:
            return "simple_llm not available in ctx."
        notes = self.db.list_notes(limit=30)
        if not notes:
            return "No notes to consolidate."
        note_text = "\n".join(row.get("text", "") for row in notes)
        prompt = f"""Consolidate these notes into durable long-term memory. Rules: - Keep useful facts. - Remove noise. - Produce concise memory statements. - Do not invent unsupported facts. Notes: {note_text[:8000]}"""
        reply = simple_llm([{"role": "system", "content": "You consolidate memories into stable knowledge."}, {"role": "user", "content": prompt}])
        self.db.add_note(reply, tags="memory_consolidation")
        if "vector" in self.ctx:
            self.ctx["vector"].add(reply, kind="memory_consolidation")
        self.log_event("memory_consolidation", {"summary": reply[:500]})
        return "Memory consolidation completed."

    def forget_low_value(self, days=None):
        if days is None:
            days = int(self.get_setting("memory_retention_days") or 30)
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat(timespec="seconds")
        try:
            cur = self.db.execute("DELETE FROM memories WHERE kind = 'conversation' AND created_at < ?", (cutoff,))
            removed_memories = cur.rowcount
        except:
            removed_memories = 0
        try:
            self.db.execute("DELETE FROM history WHERE created_at < ?", (cutoff,))
        except:
            pass
        self.log_event("forgetting", {"days": days, "removed_conversation_memories": removed_memories})
        return f"Forgetting complete. Removed {removed_memories} old conversation memories."

    def self_benchmark(self):
        results = []
        tools = self.ctx.get("tools")
        start = time.time()
        if tools and tools.exists("calculate"):
            try:
                math_result = tools.execute("calculate", {"expression": "17 * 4"})
                math_ok = "68" in str(math_result)
            except:
                math_ok = False
        else:
            math_ok = False
        math_time = time.time() - start
        self.record_metric("benchmark_math_ok", 1.0 if math_ok else 0.0)
        self.record_metric("benchmark_math_time", math_time)
        results.append(f"math tool: {'OK' if math_ok else 'FAILED'} in {math_time:.3f}s")
        start = time.time()
        if tools and tools.exists("search_memory"):
            try:
                tools.execute("search_memory", {"query": "self system", "limit": 2})
                memory_ok = True
            except:
                memory_ok = False
        else:
            memory_ok = False
        memory_time = time.time() - start
        self.record_metric("benchmark_memory_ok", 1.0 if memory_ok else 0.0)
        self.record_metric("benchmark_memory_time", memory_time)
        results.append(f"memory search: {'OK' if memory_ok else 'FAILED'} in {memory_time:.3f}s")
        simple_llm = self.ctx.get("simple_llm")
        start = time.time()
        llm_ok = False
        if simple_llm:
            reply = simple_llm([{"role": "user", "content": "Reply with OK."}])
            if reply and not str(reply).startswith("[API"):
                llm_ok = True
        llm_time = time.time() - start
        self.record_metric("benchmark_llm_ok", 1.0 if llm_ok else 0.0)
        self.record_metric("benchmark_llm_time", llm_time)
        results.append(f"LLM ping: {'OK' if llm_ok else 'FAILED'} in {llm_time:.3f}s")
        self.log_event("self_benchmark", {"results": results})
        return "\n".join(results)

    def evolve_system_prompt(self):
        if not self.get_setting("prompt_evolution"):
            return "Prompt evolution is disabled. Use /self set prompt_evolution true to enable."
        simple_llm = self.ctx.get("simple_llm")
        if not simple_llm:
            return "simple_llm not available in ctx."
        current_prompt = self.cfg.get("system_prompt", "")
        failures = self.db.query("SELECT context, error FROM self_failures ORDER BY ts DESC LIMIT 5")
        feedback = self.db.query("SELECT target, rating, comment FROM self_feedback ORDER BY ts DESC LIMIT 5")
        failure_text = "\n".join(f"- {f['context']} :: {f['error']}" for f in failures) or "No failures."
        feedback_text = "\n".join(f"- {f['target']} rating={f['rating']} :: {f['comment']}" for f in feedback) or "No feedback."
        prompt = f"""Improve this AI system prompt. Current system prompt: {current_prompt} Recent failures: {failure_text} Recent feedback: {feedback_text} Requirements: - Return only the improved system prompt. - Make it safer, clearer, and more useful. - Do not mention that it was improved."""
        improved_prompt = simple_llm([{"role": "system", "content": "You improve AI agent system prompts."}, {"role": "user", "content": prompt}])
        if not improved_prompt or improved_prompt.startswith("[API"):
            return "Prompt evolution failed because LLM API is unavailable."
        version_id = str(uuid.uuid4())
        self.db.execute("INSERT INTO self_prompt_versions (id, ts, prompt, score, active) VALUES (?, ?, ?, 0, 0)", (version_id, datetime.datetime.now().isoformat(timespec="seconds"), improved_prompt))
        self.log_event("prompt_evolved", {"version_id": version_id, "summary": improved_prompt[:300]})
        return f"New prompt candidate saved with id {version_id}. Review it before activation."

    def list_prompt_versions(self):
        return self.db.query("SELECT id, ts, prompt, score, active FROM self_prompt_versions ORDER BY ts DESC LIMIT 20")

    def activate_prompt(self, version_id):
        if not self.get_setting("allow_self_prompt_activation"):
            return "Self prompt activation is disabled. Use /self set allow_self_prompt_activation true to allow."
        rows = self.db.query("SELECT prompt FROM self_prompt_versions WHERE id = ?", (version_id,))
        if not rows:
            return "Prompt version not found."
        prompt = rows[0]["prompt"]
        self.db.execute("UPDATE self_prompt_versions SET active = 0")
        self.db.execute("UPDATE self_prompt_versions SET active = 1 WHERE id = ?", (version_id,))
        self.cfg["system_prompt"] = prompt
        save_config = self.ctx.get("save_config")
        if callable(save_config):
            save_config(self.cfg)
        self.log_event("prompt_activated", {"version_id": version_id})
        return "Prompt activated."

    def save_skill_version(self, name, code, status="generated"):
        rows = self.db.query("SELECT COALESCE(MAX(version), 0) AS max_version FROM skill_versions WHERE name = ?", (name,))
        version = int(rows[0]["max_version"]) + 1 if rows else 1
        version_id = str(uuid.uuid4())
        self.db.execute("INSERT INTO skill_versions (id, name, version, code, status, created_at) VALUES (?, ?, ?, ?, ?, ?)", (version_id, name, version, code, status, datetime.datetime.now().isoformat(timespec="seconds")))
        self.log_event("skill_version_saved", {"name": name, "version": version, "status": status})
        return f"Saved {name} version {version}."

    def list_skill_versions(self, name=None):
        if name:
            return self.db.query("SELECT id, name, version, status, created_at FROM skill_versions WHERE name = ? ORDER BY version DESC", (name,))
        return self.db.query("SELECT id, name, version, status, created_at FROM skill_versions ORDER BY created_at DESC LIMIT 100")

    def run_cycle(self):
        if not self.get_setting("enabled"):
            return "Self-growth engine is disabled."
        outputs = []
        if self.get_setting("auto_reflect"):
            outputs.append("Self critique:")
            outputs.append(self.critique_recent())
        if self.get_setting("auto_consolidate"):
            outputs.append(self.consolidate_memory())
        if self.get_setting("auto_forget"):
            outputs.append(self.forget_low_value())
        if self.get_setting("auto_benchmark"):
            outputs.append("Benchmark:")
            outputs.append(self.self_benchmark())
        if self.get_setting("auto_skill_proposals"):
            outputs.append(self.propose_improvements())
        self.log_event("growth_cycle", {"outputs": len(outputs)})
        return "\n\n".join(str(output) for output in outputs)
