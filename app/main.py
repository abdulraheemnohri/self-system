#!/usr/bin/env python3
"""
Complete Self System - Main Application
خود کار نظام - مین ایپلی کیشن

Version: 1.0.0
Author: Abdulraheem Nohari
"""

import os
import sys
import time
import threading
import json
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from .config import get_config
from .db import Database
from .vector_store import VectorStore
from .agent import Agent
from .tools import get_tool_registry


class CompleteSelfSystem:
    """Main application class for the Complete Self System"""
    
    def __init__(self):
        self.cfg = get_config()
        self._initialize_storage()
        self.db = Database(self.cfg.get("memory", "db_path") or "storage/self_system.db")
        self.vector = VectorStore(self.db)
        self.agent = Agent(self.db, self.vector)
        self.tools = get_tool_registry(self.db, self.vector)
        self._initialize_directories()
        self.scheduler_thread = None
        if self.cfg.get("scheduler", "enabled", False):
            self._start_scheduler()
    
    def _initialize_storage(self):
        storage_dirs = ["storage", "plugins", "tests", "generated_skills", "storage/vector"]
        for dir_path in storage_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def _initialize_directories(self):
        Path("plugins").mkdir(parents=True, exist_ok=True)
        Path("tests").mkdir(parents=True, exist_ok=True)
        Path("generated_skills").mkdir(parents=True, exist_ok=True)
        sample_plugin = Path("plugins/sample_tool.py")
        if not sample_plugin.exists():
            with open(sample_plugin, 'w') as f:
                f.write("""def execute(args):
    return f"Sample plugin received: {args}"""")
    
    def _start_scheduler(self):
        def scheduler_loop():
            while True:
                try:
                    now_ts = time.time()
                    due_tasks = self.db.get_due_schedules(now_ts)
                    for task in due_tasks:
                        action = task.get("action", "")
                        try:
                            result = self._run_autonomous_action(action)
                            print(f"[autonomous:{action}] {result}")
                        except Exception as exc:
                            print(f"[autonomous:{action}] error: {exc}")
                        self.db.update_schedule_last_run(task["id"], time.time())
                except Exception as exc:
                    print(f"[scheduler error] {exc}")
                time.sleep(30)
        self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        print("[scheduler] Autonomous mode enabled")
    
    def _run_autonomous_action(self, action):
        if action == "memory_cleanup":
            self.db.cleanup_history(days=30)
            self.db.cleanup_memories()
            return "Memory cleanup completed"
        if action == "self_review":
            return self._self_review()
        if action == "periodic_learning":
            return self._periodic_learning()
        return f"Unknown autonomous action: {action}"
    
    def _self_review(self):
        history = self.db.get_history(30)
        if not history:
            return "No history to review"
        conversation = "\n".join(f"{item.get('role')}: {item.get('content')}" for item in history)
        messages = [{"role": "system", "content": "Review this AI conversation and suggest one improvement."}, {"role": "user", "content": conversation[:6000]}]
        from .llm import get_llm_client
        llm = get_llm_client()
        reply = llm.simple_chat(messages, use_tools=False)
        if reply and not reply.startswith("[API"):
            self.db.add_note(reply, tags="self_review")
            self.vector.add_memory(reply, kind="self_review")
            return "Self-review saved"
        return "Self-review skipped"
    
    def _periodic_learning(self):
        notes = self.db.list_notes(limit=10)
        if not notes:
            return "No notes to learn from"
        text = "\n".join(row.get("text", "") for row in notes)
        messages = [{"role": "system", "content": "Summarize the most useful information from these notes."}, {"role": "user", "content": text[:6000]}]
        from .llm import get_llm_client
        llm = get_llm_client()
        reply = llm.simple_chat(messages, use_tools=False)
        if reply and not reply.startswith("[API"):
            self.db.add_note(reply, tags="periodic_learning")
            self.vector.add_memory(reply, kind="periodic_learning")
            return "Periodic learning summary saved"
        return "Periodic learning skipped"
    
    def handle_command(self, command):
        raw = str(command or "").strip()
        if not raw.startswith("/"):
            return None
        without_slash = raw[1:].strip()
        parts = without_slash.split(maxsplit=1)
        if not parts:
            return None
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""
        if cmd in {"exit", "quit"}:
            return "__EXIT__"
        if cmd == "help":
            return self._get_help_text()
        if cmd == "clear":
            self.db.clear_history()
            return "History cleared"
        if cmd == "history":
            rows = self.db.get_history(20)
            if not rows:
                return "History empty"
            return "\n".join(f"{r['role']}: {r['content']}" for r in rows)
        if cmd == "config":
            return self._handle_config_command(arg)
        if cmd == "remember":
            subparts = arg.split(maxsplit=1)
            if len(subparts) < 2:
                return "Usage: /remember key value"
            key, value = subparts
            self.db.set_fact(key, value)
            self.vector.remember_fact(key, value)
            return f"Remembered {key}"
        if cmd == "facts":
            facts = self.db.get_facts()
            if not facts:
                return "No facts"
            return "\n".join(f"{k}: {v}" for k, v in facts.items())
        if cmd == "forget":
            if not arg:
                return "Usage: /forget key"
            self.db.delete_fact(arg)
            return f"Forgot {arg}"
        if cmd == "note":
            if not arg:
                return "Usage: /note text"
            self.db.add_note(arg, tags="manual")
            self.vector.remember_note(arg, tags="manual")
            return "Note saved"
        if cmd == "notes":
            rows = self.db.list_notes(20)
            if not rows:
                return "No notes"
            return "\n\n".join(f"[{r['created_at']}] {r['text']}" for r in rows)
        if cmd == "search":
            if not arg:
                return "Usage: /search query"
            results = self.vector.search_memory(arg, limit=8)
            if not results:
                return "No vector memory found"
            lines = []
            for item in results:
                lines.append(f"[{item['score']:.2f}] ({item['kind']}) {item['text']}")
            return "\n".join(lines)
        if cmd == "teach":
            if "|" not in arg:
                return "Usage: /teach question | answer"
            question, answer = arg.split("|", 1)
            self.db.add_knowledge(question.strip(), answer.strip())
            self.vector.remember_knowledge(question.strip(), answer.strip())
            return "Knowledge saved"
        if cmd == "knowledge":
            rows = self.db.list_knowledge(30)
            if not rows:
                return "No knowledge"
            return "\n".join(f"Q: {r['question']}\nA: {r['answer']}\n" for r in rows)
        if cmd == "agent":
            if arg == "on":
                self.cfg.set("agent", "agent_mode", True)
                self.cfg.save()
                return "Agent mode enabled"
            if arg == "off":
                self.cfg.set("agent", "agent_mode", False)
                self.cfg.save()
                return "Agent mode disabled"
            return "Usage: /agent on | /agent off"
        if cmd == "tools":
            return "\n".join(f"- {name}" for name in self.tools.names())
        if cmd == "plugins":
            import os
            plugin_dir = Path("plugins")
            plugins = []
            if plugin_dir.exists():
                for filename in os.listdir(plugin_dir):
                    if filename.endswith(".py"):
                        plugins.append(filename[:-3])
            if not plugins:
                return "No plugins"
            return "\n".join(f"- {name}" for name in sorted(plugins))
        if cmd == "skills":
            rows = self.db.list_skills(30)
            if not rows:
                return "No generated skills"
            return "\n".join(f"[{r['status']}] {r['name']} - {r['description']}" for r in rows)
        if cmd == "reembed":
            notes = self.db.list_notes(100)
            knowledge = self.db.list_knowledge(100)
            count = 0
            for row in notes:
                self.vector.remember_note(row["text"], kind="note")
                count += 1
            for row in knowledge:
                self.vector.remember_knowledge(row["question"], row["answer"])
                count += 1
            return f"Re-embedded {count} items"
        if cmd == "export":
            import os
            filename = os.path.basename(arg.strip() or "self_system_export.json")
            export_data = {"exported_at": self._get_current_time(), "facts": self.db.get_facts(), "notes": self.db.list_notes(1000), "knowledge": self.db.list_knowledge(1000), "history": self.db.get_history(500), "skills": self.db.list_skills(1000), "schedules": self.db.list_schedules()}
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            return f"Exported to {filename}"
        return f"Unknown command: /{cmd}. Try /help"
    
    def _get_help_text(self):
        return """Available commands:
Basic:
  /help - Show this help
  /exit - Exit the application
  /clear - Clear conversation history
  /history - Show conversation history
Config:
  /config show - Show current configuration
  /config set key value - Set a configuration value
Memory:
  /remember key value - Store a fact
  /facts - List all facts
  /forget key - Remove a fact
  /note text - Save a note
  /notes - List notes
  /search query - Search vector memory
  /reembed - Re-embed all memories
Knowledge:
  /teach question | answer - Add knowledge
  /knowledge - List knowledge entries
Agent:
  /agent on/off - Enable/disable agent mode
  /tools - List available tools
Plugins:
  /plugins - List plugins
  /skills - List generated skills
Export:
  /export filename.json - Export data"""
    
    def _handle_config_command(self, arg):
        subparts = arg.split()
        if not subparts or subparts[0] == "show":
            safe_cfg = dict(self.cfg.as_dict())
            safe_cfg["provider"]["api_key"] = self._mask_key(safe_cfg["provider"].get("api_key", ""))
            return json.dumps(safe_cfg, indent=2)
        if subparts[0] == "set" and len(subparts) >= 3:
            key_path = subparts[1].split(".")
            value = " ".join(subparts[2:])
            current = self.cfg.get(*key_path)
            if isinstance(current, bool):
                value = value.lower() in {"true", "yes", "1", "on", "y"}
            elif isinstance(current, int):
                try:
                    value = int(value)
                except ValueError:
                    return f"{key_path[-1]} must be integer"
            elif isinstance(current, float):
                try:
                    value = float(value)
                except ValueError:
                    return f"{key_path[-1]} must be number"
            self.cfg.set(*key_path, value)
            self.cfg.save()
            return f"Set {'.'.join(key_path)}"
        return "Usage: /config show | /config set key value"
    
    def _get_current_time(self):
        from datetime import datetime
        return datetime.now().isoformat(timespec="seconds")
    
    def _mask_key(self, value):
        value = str(value or "")
        if not value:
            return "(empty)"
        if len(value) <= 8:
            return "*" * len(value)
        return value[:4] + "..." + value[-4:]
    
    def run(self):
        print("=" * 60)
        print("COMPLETE SELF SYSTEM")
        print("خود کار نظام")
        print("=" * 60)
        print(f"Version: {self.cfg.get('system', 'version')}")
        print(f"Mode: {self.cfg.get('system', 'mode')}")
        print(f"Agent mode: {'enabled' if self.cfg.get('agent', 'agent_mode') else 'disabled'}")
        print(f"Vector backend: {self.cfg.get('memory', 'vector_backend')}")
        print()
        print("Type /help for commands")
        print()
        while True:
            try:
                user_input = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye")
                break
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit", "/exit"}:
                print("Goodbye")
                break
            if user_input.startswith("/"):
                result = self.handle_command(user_input)
                if result == "__EXIT__":
                    break
                if result:
                    print(result)
                continue
            self.db.add_history("user", user_input)
            if self.cfg.get("agent", "agent_mode", True):
                reply = self.agent.run(user_input)
            else:
                reply = self.agent.direct_reply(user_input)
            print(f"Agent: {reply}")
            self.db.add_history("assistant", reply)
            self.vector.add_memory(f"User: {user_input}\nAssistant: {reply}", kind="conversation")


def main():
    system = CompleteSelfSystem()
    system.run()


if __name__ == "__main__":
    main()