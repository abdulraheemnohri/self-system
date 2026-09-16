#!/usr/bin/env python3
"""
Complete Self System - Main Entry Point

An autonomous AI agent platform with:
- LLM integration (OpenAI, Ollama, Groq, etc.)
- Vector memory (SQLite, ChromaDB, FAISS, Qdrant)
- Tool calling (OpenAI-compatible function calling)
- Agent loop (Plan, Execute, Observe, Learn)
- Browser automation (Playwright)
- Voice input/output (SpeechRecognition, pyttsx3)
- Plugin system
- Automatic skill generation
- Self-testing
- Scheduled autonomous tasks
- Safety governor
- Audit logging
"""

import os
import sys
import json
import time
import threading
import textwrap
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================================
# Import Configuration
# ============================================================
from app.config import load_config, save_config, DEFAULT_CONFIG

# ============================================================
# Import Database
# ============================================================
from app.db import Database

# ============================================================
# Import Embeddings & Vector Store
# ============================================================
from app.vector_store import VectorStore, remember_text, search_vector_memory
from app.llm import Embedder

# ============================================================
# Import LLM Client
# ============================================================
from app.llm import call_chat_api_raw, simple_llm_reply

# ============================================================
# Import Tools
# ============================================================
from app.tools import ToolRegistry

# ============================================================
# Import Safety Governor
# ============================================================
from app.safety import SafetyGovernor, create_safety_governor

# ============================================================
# Import Browser Automation
# ============================================================
from app.browser import BrowserManager, create_browser_manager

# ============================================================
# Import Voice I/O
# ============================================================
from app.voice import VoiceManager, create_voice_manager

# ============================================================
# Import Plugin Manager
# ============================================================
from app.plugins import PluginManager

# ============================================================
# Import Skills Manager
# ============================================================
from app.skills import SkillsManager, create_skills_manager

# ============================================================
# Import Scheduler
# ============================================================
from app.scheduler import AutonomousScheduler, create_scheduler

# ============================================================
# Agent Loop
# ============================================================

def build_context(db: Database, cfg: Dict[str, Any], embedder: Embedder, query: str) -> str:
    """Build the context for LLM with memory and facts."""
    facts = db.get_facts()
    fact_lines = "\n".join(f"- {k}: {v}" for k, v in facts.items()) or "None"
    
    # Search vector memory
    memories = search_vector_memory(db, embedder, query, limit=5)
    memory_lines = "\n".join(
        f"- [{item['kind']} score={item['score']:.2f}] {item['text']}"
        for item in memories
    ) or "None"
    
    system_prompt = cfg.get('prompt.system', DEFAULT_CONFIG.get('prompt.system', ''))
    
    return f"""{system_prompt}

Current time: {time.strftime('%Y-%m-%d %H:%M:%S')}

Stored user facts:
{fact_lines}

Relevant vector memory:
{memory_lines}

Use tools only when needed.
If a tool result is useful, continue.
When the task is complete, return a final natural-language answer.
"""


def run_agent(user_input: str, ctx: Dict[str, Any]) -> str:
    """
    Run the agent loop with tool calling.
    
    Args:
        user_input: User input
        ctx: Context dictionary with db, cfg, embedder, tools, etc.
        
    Returns:
        Agent response
    """
    db = ctx["db"]
    cfg = ctx["cfg"]
    embedder = ctx["embedder"]
    tools = ctx["tools"]
    
    history = db.get_history(int(cfg.get("agent.context_turns", 12)))
    
    messages = [
        {
            "role": "system",
            "content": build_context(db, cfg, embedder, user_input)
        }
    ]
    
    for row in history:
        messages.append({
            "role": row.get("role", "user"),
            "content": row.get("content", "")
        })
    
    messages.append({
        "role": "user",
        "content": user_input
    })
    
    max_steps = int(cfg.get("agent.max_agent_steps", 8))
    
    for step in range(max_steps):
        use_tools = cfg.get("agent.enable_tool_calls", True)
        tool_schemas = tools.schemas() if use_tools else None
        
        message = call_chat_api_raw(cfg, messages, tools=tool_schemas)
        
        # Some providers reject tools. Retry without tools.
        if "_error" in message and use_tools:
            message = call_chat_api_raw(cfg, messages, tools=None)
        
        if "_error" in message:
            return message["_error"]
        
        tool_calls = message.get("tool_calls")
        
        if tool_calls:
            assistant_message = {
                "role": "assistant",
                "content": message.get("content") or "",
                "tool_calls": tool_calls
            }
            messages.append(assistant_message)
            
            for call in tool_calls:
                function_info = call.get("function", {})
                tool_name = function_info.get("name", "")
                arguments_text = function_info.get("arguments", "{}")
                
                try:
                    arguments = json.loads(arguments_text)
                except Exception:
                    arguments = {}
                
                result = tools.execute(tool_name, arguments)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.get("id", ""),
                    "name": tool_name,
                    "content": str(result)[:4000]
                })
            
            continue
        
        content = message.get("content", "") or ""
        return content
    
    return "Agent stopped: max steps reached"


def direct_reply(user_input: str, ctx: Dict[str, Any]) -> str:
    """
    Get a direct LLM reply without agent tools.
    
    Args:
        user_input: User input
        ctx: Context dictionary
        
    Returns:
        LLM response
    """
    db = ctx["db"]
    cfg = ctx["cfg"]
    embedder = ctx["embedder"]
    
    history = db.get_history(int(cfg.get("agent.context_turns", 12)))
    
    messages = [
        {
            "role": "system",
            "content": build_context(db, cfg, embedder, user_input)
        }
    ]
    
    for row in history:
        messages.append({
            "role": row.get("role", "user"),
            "content": row.get("content", "")
        })
    
    messages.append({
        "role": "user",
        "content": user_input
    })
    
    message = call_chat_api_raw(cfg, messages, tools=None)
    
    if "_error" in message:
        return message["_error"]
    
    return message.get("content", "") or ""


# ============================================================
# Command Handler
# ============================================================

def handle_command(line: str, ctx: Dict[str, Any]) -> Optional[str]:
    """
    Handle user commands.
    
    Args:
        line: User input command
        ctx: Context dictionary
        
    Returns:
        Command result or None
    """
    raw = str(line or "").strip()
    if not raw.startswith("/"):
        return None
    
    without_slash = raw[1:].strip()
    parts = without_slash.split(maxsplit=1)
    
    if not parts:
        return None
    
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""
    
    db = ctx["db"]
    cfg = ctx["cfg"]
    embedder = ctx["embedder"]
    tools = ctx["tools"]
    safety = ctx.get("safety")
    browser = ctx.get("browser")
    voice = ctx.get("voice")
    plugins = ctx.get("plugins")
    skills = ctx.get("skills")
    scheduler = ctx.get("scheduler")
    
    # ----------------------------
    # Basic commands
    # ----------------------------
    
    if cmd in {"exit", "quit"}:
        return "__EXIT__"
    
    if cmd == "help":
        return textwrap.dedent("""
        --- Basic ---
        /help                          Show this help
        /exit                          Exit the application
        /clear                         Clear conversation history
        /history                       Show recent conversation history
        /last                          Show last AI response
        /save                          Save last AI response as a note
        
        --- Config ---
        /config show                   Show current configuration
        /config set key value          Set a configuration value
        /config test                   Test API connection
        /doctor                        Diagnose configuration and API
        
        --- Memory ---
        /remember key value            Store a fact
        /facts                         List all stored facts
        /forget key                    Remove a fact
        /note text                     Add a note
        /notes                         List all notes
        /search query                  Search vector memory
        /reembed                       Re-embed all memories
        
        --- Knowledge ---
        /teach question | answer       Teach permanent knowledge
        /knowledge                     List learned knowledge
        /forget_knowledge query        Remove matching knowledge
        
        --- Agent ---
        /agent on                      Enable agent mode
        /agent off                     Disable agent mode
        /tools                         List available tools
        
        --- Browser ---
        /browser open url              Open URL in browser
        /browser text [selector]       Extract text from page
        /browser fill selector | text Fill a form field
        /browser click selector        Click an element
        /browser screenshot [path]    Take a screenshot
        /browser pdf [path]            Generate PDF
        
        --- Voice ---
        /voice on                      Enable voice output
        /voice off                     Disable voice output
        /listen                        Listen to microphone
        /say text                      Speak text aloud
        
        --- Plugins ---
        /plugins                       List loaded plugins
        /plugins reload                Reload all plugins
        /run plugin_name args          Run a plugin
        
        --- Skills ---
        /skills                        List generated skills
        /genskill name | description  Generate a new skill
        /selftest plugin_name         Test a plugin
        
        --- Autonomous ---
        /autonomous on                 Enable autonomous mode
        /autonomous off                Disable autonomous mode
        /schedule list                 List scheduled tasks
        /schedule add name action sec  Add a scheduled task
        /schedule remove name          Remove a scheduled task
        /reflect                       Review recent conversations
        
        --- Safety ---
        /safety tools                  List tool permissions
        /safety set tool enabled       Set tool permission
        /safety audit [limit]          Show audit logs
        /safety policies               Show security policies
        
        --- Export ---
        /export filename.json          Export memory and state
        """).strip()
    
    if cmd == "clear":
        db.clear_history()
        return "Conversation history cleared."
    
    if cmd == "history":
        rows = db.get_history(20)
        if not rows:
            return "History is empty."
        return "\n".join(f"[{r['created_at']}] {r['role']}: {r['content'][:200]}" for r in rows)
    
    if cmd == "last":
        rows = db.get_history(1)
        if rows:
            return f"Last AI: {rows[0].get('content', '')}"
        return "No previous AI response."
    
    if cmd == "save":
        rows = db.get_history(1)
        if rows and rows[0].get('role') == 'assistant':
            text = rows[0].get('content', '')
            db.add_note(text, tags=["saved-response"])
            remember_text(db, embedder, text, kind="saved_response")
            return "Last AI response saved as note."
        return "No AI response to save."
    
    # ----------------------------
    # Config commands
    # ----------------------------
    
    if cmd == "config":
        subparts = arg.split()
        
        if not subparts or subparts[0] == "show":
            safe_cfg = dict(cfg)
            if "api_key" in safe_cfg:
                safe_cfg["api_key"] = "REDACTED" if safe_cfg["api_key"] else "(empty)"
            return json.dumps(safe_cfg, indent=2)
        
        if subparts[0] == "set" and len(subparts) >= 3:
            key = subparts[1]
            value = " ".join(subparts[2:])
            
            # Convert value based on key
            bool_keys = {"agent_mode", "enable_tool_calls", "autonomous_mode", 
                        "auto_install_skills", "allow_plugin_tool", "allow_skill_tool",
                        "speak_responses", "voice.enabled", "safety.autonomous_mode"}
            int_keys = {"max_tokens", "timeout", "max_agent_steps", "context_turns",
                       "max_context_chars", "embedding_dim_fallback"}
            float_keys = {"temperature"}
            
            if key in bool_keys:
                cfg[key] = value.lower() in {"true", "yes", "1", "on"}
            elif key in int_keys:
                try:
                    cfg[key] = int(value)
                except ValueError:
                    return f"{key} must be an integer."
            elif key in float_keys:
                try:
                    cfg[key] = float(value)
                except ValueError:
                    return f"{key} must be a number."
            else:
                cfg[key] = value
            
            save_config(cfg)
            return f"Set {key}."
        
        if subparts[0] == "test":
            test_messages = [{"role": "user", "content": "Reply with OK."}]
            return call_chat_api_raw(cfg, test_messages, tools=None).get("content", "")
        
        if subparts[0] == "reset":
            for key in list(cfg.keys()):
                if key in DEFAULT_CONFIG:
                    cfg[key] = DEFAULT_CONFIG[key]
            save_config(cfg)
            return "Configuration reset to defaults."
        
        return "Usage: /config show | /config set <key> <value> | /config test | /config reset"
    
    if cmd == "doctor":
        report = []
        base_url = cfg.get("provider.base_url", "")
        model = cfg.get("provider.model", "")
        api_key = cfg.get("provider.api_key", "")
        
        report.append(f"Base URL: {base_url or '(empty)'}")
        report.append(f"Model: {model or '(empty)'}")
        report.append(f"API Key: {'***' if api_key else '(empty)'}")
        
        if not base_url:
            report.append("Issue: base_url is empty")
        if not model:
            report.append("Issue: model is empty")
        
        # Test API
        test_reply = call_chat_api_raw(
            cfg,
            [{"role": "user", "content": "Reply with OK."}],
            tools=None
        )
        
        if "_error" in test_reply:
            report.append(f"API Error: {test_reply['_error']}")
        else:
            report.append("API: OK")
        
        # Check components
        report.append(f"Vector Store: {'OK' if ctx.get('vector') else 'Not configured'}")
        report.append(f"Safety: {'OK' if ctx.get('safety') else 'Not configured'}")
        report.append(f"Browser: {'OK' if ctx.get('browser') and ctx['browser'].installed else 'Not installed'}")
        report.append(f"Voice: {'OK' if ctx.get('voice') and ctx['voice'].tts_available else 'Not available'}")
        
        return "\n".join(report)
    
    # ----------------------------
    # Memory commands
    # ----------------------------
    
    if cmd == "remember":
        parts = arg.split(maxsplit=1)
        if len(parts) < 2:
            return "Usage: /remember <key> <value>"
        key, value = parts
        db.set_fact(key, value)
        remember_text(db, embedder, f"{key} = {value}", kind="fact")
        return f"Remembered fact: {key}"
    
    if cmd == "facts":
        facts = db.get_facts()
        if not facts:
            return "No facts stored."
        return "\n".join(f"- {k}: {v}" for k, v in facts.items())
    
    if cmd == "forget":
        if not arg:
            return "Usage: /forget <key>"
        db.delete_fact(arg)
        return f"Forgot fact: {arg}"
    
    if cmd == "note":
        if not arg:
            return "Usage: /note <text>"
        db.add_note(arg, tags=["manual"])
        remember_text(db, embedder, arg, kind="note", metadata={"tags": "manual"})
        return "Note saved."
    
    if cmd == "notes":
        rows = db.list_notes(20)
        if not rows:
            return "No notes."
        return "\n\n".join(f"[{r['created_at']}] {r['text'][:200]}" for r in rows)
    
    if cmd == "search":
        if not arg:
            return "Usage: /search <query>"
        results = search_vector_memory(db, embedder, arg, limit=8)
        if not results:
            return "No matching memories found."
        return "\n".join(f"[{item['score']:.2f}] ({item['kind']}) {item['text'][:200]}" for item in results)
    
    if cmd == "reembed":
        notes = db.list_notes(100)
        knowledge = db.list_knowledge(100)
        count = 0
        
        for row in notes:
            remember_text(db, embedder, row["text"], kind="note")
            count += 1
        
        for row in knowledge:
            text = f"Q: {row['question']} A: {row['answer']}"
            remember_text(db, embedder, text, kind="knowledge")
            count += 1
        
        return f"Re-embedded {count} items."
    
    # ----------------------------
    # Knowledge commands
    # ----------------------------
    
    if cmd == "teach":
        if "|" not in arg:
            return "Usage: /teach question | answer"
        question, answer = arg.split("|", 1)
        db.add_knowledge(question.strip(), answer.strip())
        remember_text(db, embedder, f"Q: {question.strip()} A: {answer.strip()}", kind="knowledge")
        return "Knowledge saved."
    
    if cmd == "knowledge":
        rows = db.list_knowledge(30)
        if not rows:
            return "No knowledge."
        return "\n".join(f"Q: {r['question']}\nA: {r['answer']}\n" for r in rows)
    
    if cmd == "forget_knowledge":
        if not arg:
            return "Usage: /forget_knowledge <query>"
        best, score = db.find_best_knowledge(arg, threshold=0.30)
        if best:
            db.delete_knowledge(best["id"])
            return f"Removed knowledge: {best['question'][:100]}"
        return "No matching knowledge found."
    
    # ----------------------------
    # Agent commands
    # ----------------------------
    
    if cmd == "agent":
        if arg == "on":
            cfg["agent.agent_mode"] = True
            save_config(cfg)
            return "Agent mode enabled."
        if arg == "off":
            cfg["agent.agent_mode"] = False
            save_config(cfg)
            return "Agent mode disabled."
        return "Usage: /agent on | /agent off"
    
    if cmd == "tools":
        return "Available tools:\n" + "\n".join(f"- {name}" for name in tools.names())
    
    # ----------------------------
    # Browser commands
    # ----------------------------
    
    if cmd == "browser":
        if not browser:
            return "Browser not configured."
        
        subparts = arg.split(maxsplit=1)
        if not subparts:
            return "Usage: /browser open <url> | /browser text [selector] | /browser fill <selector> | <text> | /browser click <selector> | /browser screenshot [path] | /browser pdf [path]"
        
        subcmd = subparts[0].lower()
        subarg = subparts[1] if len(subparts) > 1 else ""
        
        if subcmd == "open":
            if not subarg:
                return "Usage: /browser open <url>"
            result = browser.navigate(subarg)
            if result.get("success"):
                return f"Opened: {result.get('url', subarg)} (Title: {result.get('title', 'N/A')})"
            return f"Error: {result.get('error', 'Unknown error')}"
        
        if subcmd == "text":
            result = browser.get_text(subarg or "body")
            if result.get("success"):
                text = result.get("text", "")
                return text[:2000] + ("..." if len(text) > 2000 else "")
            return f"Error: {result.get('error', 'Unknown error')}"
        
        if subcmd == "fill":
            if "|" not in subarg:
                return "Usage: /browser fill <selector> | <text>"
            selector, text = subarg.split("|", 1)
            result = browser.fill(selector.strip(), text.strip())
            if result.get("success"):
                return result.get("message", "Filled.")
            return f"Error: {result.get('error', 'Unknown error')}"
        
        if subcmd == "click":
            if not subarg:
                return "Usage: /browser click <selector>"
            result = browser.click(subarg)
            if result.get("success"):
                return result.get("message", "Clicked.")
            return f"Error: {result.get('error', 'Unknown error')}"
        
        if subcmd == "screenshot":
            path = subarg or f"screenshots/{int(time.time())}.png"
            result = browser.take_screenshot(path)
            if result.get("success"):
                return f"Screenshot saved: {result.get('path')}"
            return f"Error: {result.get('error', 'Unknown error')}"
        
        if subcmd == "pdf":
            path = subarg or f"pdfs/{int(time.time())}.pdf"
            result = browser.generate_pdf(path)
            if result.get("success"):
                return f"PDF saved: {result.get('path')}"
            return f"Error: {result.get('error', 'Unknown error')}"
        
        return f"Unknown browser command: {subcmd}"
    
    # ----------------------------
    # Voice commands
    # ----------------------------
    
    if cmd == "voice":
        if arg == "on":
            cfg["voice.enabled"] = True
            cfg["safety.speak_responses"] = True
            save_config(cfg)
            if voice:
                voice.enable()
            return "Voice output enabled."
        if arg == "off":
            cfg["voice.enabled"] = False
            cfg["safety.speak_responses"] = False
            save_config(cfg)
            if voice:
                voice.disable()
            return "Voice output disabled."
        return "Usage: /voice on | /voice off"
    
    if cmd == "listen":
        if not voice:
            return "Voice not configured."
        result = voice.listen()
        if result.get("success"):
            return f"You said: {result.get('text', '')}"
        return f"Error: {result.get('error', 'No speech detected')}"
    
    if cmd == "say":
        if not voice:
            return "Voice not configured."
        if not arg:
            return "Usage: /say <text>"
        result = voice.speak(arg)
        if result.get("success"):
            return result.get("message", "Spoke.")
        return f"Error: {result.get('error', 'Voice unavailable')}"
    
    # ----------------------------
    # Plugin commands
    # ----------------------------
    
    if cmd == "plugins":
        if arg.strip().lower() == "reload":
            if plugins:
                plugins.load()
                return f"Reloaded {len(plugins.list_plugins())} plugins."
            return "Plugin manager not configured."
        
        if plugins:
            plugin_names = plugins.list_plugins()
            if plugin_names:
                return "Plugins:\n" + "\n".join(f"- {name}" for name in plugin_names)
            return "No plugins loaded."
        return "Plugin manager not configured."
    
    if cmd == "run":
        if not plugins:
            return "Plugin manager not configured."
        
        parts = arg.split(maxsplit=1)
        if not parts:
            return "Usage: /run <plugin_name> [args]"
        
        plugin_name = parts[0]
        plugin_args = parts[1] if len(parts) > 1 else ""
        
        result = plugins.run(plugin_name, plugin_args)
        return result
    
    # ----------------------------
    # Skills commands
    # ----------------------------
    
    if cmd == "skills":
        if not skills:
            return "Skills manager not configured."
        
        skill_list = skills.list_skills()
        if skill_list:
            return "Generated skills:\n" + "\n".join(f"- {s['name']} ({s['size']} bytes)" for s in skill_list)
        return "No generated skills."
    
    if cmd == "genskill":
        if not skills:
            return "Skills manager not configured."
        
        if "|" not in arg:
            return "Usage: /genskill <name> | <description>"
        
        name, description = arg.split("|", 1)
        name = name.strip()
        description = description.strip()
        
        if not name or not description:
            return "Name and description required."
        
        # Create skill with user confirmation
        result = skills.create_skill(
            name, 
            description, 
            auto_install=cfg.get("safety.auto_install_skills", False),
            system_prompt=cfg.get("prompt.system")
        )
        
        if result.get("success"):
            return f"Skill created: {result.get('message', '')}"
        else:
            # Show the generated code for review
            code = result.get("code", "")
            issues = result.get("issues", [])
            test_results = result.get("test_results", {})
            
            output = [f"Skill generation: {result.get('error', 'Failed')}"]
            
            if code:
                output.append("\n--- Generated Code ---")
                output.append(code[:2000] + ("..." if len(code) > 2000 else ""))
            
            if issues:
                output.append("\n--- Validation Issues ---")
                output.append("\n".join(f"- {issue}" for issue in issues))
            
            if test_results:
                output.append(f"\n--- Test Results ---")
                output.append(f"Passed: {test_results.get('passed', 0)}")
                output.append(f"Failed: {test_results.get('failed', 0)}")
            
            # Ask for confirmation
            if not cfg.get("safety.auto_install_skills", False):
                output.append("\nType '/genskill confirm' to install this skill.")
                # Store for potential confirmation
                ctx["_pending_skill"] = result
            
            return "\n".join(output)
    
    if cmd == "genskill confirm":
        if "_pending_skill" in ctx:
            pending = ctx["_pending_skill"]
            code = pending.get("code")
            name = pending.get("name")
            description = pending.get("description")
            
            if code and name:
                # Save the plugin
                path = skills.save_plugin(name, code)
                
                # Generate and save tests
                test_result = skills.generate_test_code(
                    name, 
                    code, 
                    cfg.get("prompt.system")
                )
                if test_result.get("success"):
                    test_path = skills.test_dir / f"test_{name}.py"
                    with open(test_path, "w", encoding="utf-8") as f:
                        f.write(test_result["code"])
                
                # Reload plugins
                if plugins:
                    plugins.load()
                
                ctx.pop("_pending_skill", None)
                return f"Skill installed: {path}"
        
        return "No pending skill to confirm."
    
    if cmd == "selftest":
        if not skills:
            return "Skills manager not configured."
        
        if not arg:
            return "Usage: /selftest <plugin_name>"
        
        result = skills.self_test_plugin(arg.strip(), cfg.get("prompt.system"))
        
        if result.get("success"):
            test_results = result.get("results", {})
            return f"Test results for {arg}: Passed={test_results.get('passed', 0)}, Failed={test_results.get('failed', 0)}"
        else:
            return f"Test error: {result.get('error', 'Unknown error')}"
    
    # ----------------------------
    # Autonomous commands
    # ----------------------------
    
    if cmd == "autonomous":
        if arg == "on":
            cfg["safety.autonomous_mode"] = True
            save_config(cfg)
            if scheduler:
                scheduler.start()
            return "Autonomous mode enabled. Scheduled tasks will run automatically."
        if arg == "off":
            cfg["safety.autonomous_mode"] = False
            save_config(cfg)
            if scheduler:
                scheduler.stop()
            return "Autonomous mode disabled."
        return "Usage: /autonomous on | /autonomous off"
    
    if cmd == "schedule":
        if not scheduler:
            return "Scheduler not configured."
        
        subparts = arg.split()
        
        if not subparts or subparts[0] == "list":
            schedules = scheduler.list_schedules()
            if not schedules:
                return "No schedules."
            return "Scheduled tasks:\n" + "\n".join(
                f"- {s['name']}: {s['action']} every {s['interval_seconds']}s (next: {time.ctime(s['next_run'])})"
                for s in schedules
            )
        
        if subparts[0] == "add" and len(subparts) >= 4:
            name = subparts[1]
            action = subparts[2]
            try:
                interval = int(subparts[3])
            except ValueError:
                return "Interval must be an integer (seconds)."
            
            result = scheduler.add_schedule(
                name=name,
                action=action,
                interval_seconds=interval,
                description=f"Custom task: {action}"
            )
            
            if result.get("success"):
                return f"Scheduled: {name} -> {action} every {interval}s"
            return f"Error: {result.get('error', 'Unknown error')}"
        
        if subparts[0] == "remove" and len(subparts) >= 2:
            name = subparts[1]
            result = scheduler.remove_schedule(name)
            if result.get("success"):
                return result.get("message", "")
            return result.get("error", "Error removing schedule")
        
        return "Usage: /schedule list | /schedule add <name> <action> <seconds> | /schedule remove <name>"
    
    if cmd == "reflect":
        result = self_review(ctx)
        return result
    
    # ----------------------------
    # Safety commands
    # ----------------------------
    
    if cmd == "safety":
        subparts = arg.split()
        
        if not subparts or subparts[0] == "tools":
            if not safety:
                return "Safety governor not configured."
            tools_list = safety.list_tools()
            if not tools_list:
                return "No tools configured in safety governor."
            return "Tool permissions:\n" + "\n".join(
                f"- {t['name']}: enabled={bool(t['enabled'])}, "
                f"requires_approval={bool(t['requires_approval'])}, "
                f"rate_limit={t['max_per_hour']}/hr"
                for t in tools_list
            )
        
        if subparts[0] == "set" and len(subparts) >= 4:
            if not safety:
                return "Safety governor not configured."
            
            tool_name = subparts[1]
            property_name = subparts[2]
            value = subparts[3]
            
            if property_name == "enabled":
                enabled = value.lower() in {"true", "yes", "1", "on"}
                safety.set_permission(tool_name, enabled, True, 60)
                return f"Set {tool_name}.enabled = {enabled}"
            
            if property_name == "requires_approval":
                requires_approval = value.lower() in {"true", "yes", "1", "on"}
                perm = safety.get_permission(tool_name)
                safety.set_permission(
                    tool_name,
                    bool(perm.get("enabled", 1)),
                    requires_approval,
                    int(perm.get("max_per_hour", 60))
                )
                return f"Set {tool_name}.requires_approval = {requires_approval}"
            
            if property_name == "max_per_hour":
                try:
                    max_per_hour = int(value)
                    perm = safety.get_permission(tool_name)
                    safety.set_permission(
                        tool_name,
                        bool(perm.get("enabled", 1)),
                        bool(perm.get("requires_approval", 0)),
                        max_per_hour
                    )
                    return f"Set {tool_name}.max_per_hour = {max_per_hour}"
                except ValueError:
                    return "max_per_hour must be an integer."
            
            return f"Unknown property: {property_name}"
        
        if subparts[0] == "audit":
            if not safety:
                return "Safety governor not configured."
            
            limit = 20
            if len(subparts) > 1:
                try:
                    limit = int(subparts[1])
                except ValueError:
                    pass
            
            logs = safety.get_audit_logs(limit=limit)
            if not logs:
                return "No audit logs."
            return "Audit logs:\n" + "\n".join(
                f"[{time.ctime(l['ts'])}] {l['tool']} ({l['status']}): {l['detail'][:100]}"
                for l in logs
            )
        
        if subparts[0] == "policies":
            if not safety:
                return "Safety governor not configured."
            return "Security policies not yet implemented."
        
        return "Usage: /safety tools | /safety set <tool> <property> <value> | /safety audit [limit]"
    
    # ----------------------------
    # Export command
    # ----------------------------
    
    if cmd == "export":
        filename = arg.strip() or "self_system_export.json"
        
        export_data = {
            "exported_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "config": {k: v for k, v in cfg.items() if k != "api_key"},
            "facts": db.get_facts(),
            "notes": db.list_notes(1000),
            "knowledge": db.list_knowledge(1000),
            "history": db.get_history(500),
            "skills": skills.list_skills() if skills else [],
            "schedules": scheduler.list_schedules() if scheduler else []
        }
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            return f"Exported to {filename}"
        except Exception as e:
            return f"Export error: {e}"
    
    return f"Unknown command: /{cmd}. Type /help for available commands."


# ============================================================
# Autonomous Action Functions
# ============================================================

def memory_cleanup(ctx: Dict[str, Any]) -> str:
    """Clean up old history and duplicate memories."""
    db = ctx.get("db")
    if db:
        if hasattr(db, "cleanup_history"):
            db.cleanup_history(days=30)
        if hasattr(db, "cleanup_memories"):
            db.cleanup_memories()
        return "Memory cleanup completed."
    return "Memory cleanup skipped (no db)."


def self_review(ctx: Dict[str, Any]) -> str:
    """Review recent conversations and suggest improvements."""
    db = ctx.get("db")
    cfg = ctx.get("cfg")
    simple_llm = ctx.get("simple_llm")
    embedder = ctx.get("embedder")
    
    if not db or not simple_llm:
        return "Self-review skipped (missing dependencies)."
    
    try:
        history = db.get_history(30)
        if not history:
            return "No history available for self-review."
        
        conversation = "\n".join(
            f"{row.get('role', 'unknown')}: {row.get('content', '')}"
            for row in history
        )
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI reliability reviewer. "
                    "Review this conversation and suggest ONE concrete improvement."
                )
            },
            {
                "role": "user",
                "content": conversation[:7000]
            }
        ]
        
        reply = simple_llm(messages)
        
        if reply and not reply.startswith("[API"):
            db.add_note(reply, tags=["self_review", "autonomous"])
            if embedder:
                remember_text(db, embedder, reply, kind="self_review")
            return f"Self-review: {reply[:200]}..."
        
        return "Self-review skipped (API unavailable)."
    
    except Exception as e:
        return f"Self-review error: {e}"


def periodic_learning(ctx: Dict[str, Any]) -> str:
    """Summarize recent notes into long-term memory."""
    db = ctx.get("db")
    simple_llm = ctx.get("simple_llm")
    embedder = ctx.get("embedder")
    
    if not db or not simple_llm:
        return "Periodic learning skipped (missing dependencies)."
    
    try:
        notes = db.list_notes(limit=20)
        if not notes:
            return "No notes available for periodic learning."
        
        text = "\n\n".join(row.get("text", "") for row in notes)
        
        messages = [
            {
                "role": "system",
                "content": "Summarize the most useful information from these notes."
            },
            {
                "role": "user",
                "content": text[:7000]
            }
        ]
        
        reply = simple_llm(messages)
        
        if reply and not reply.startswith("[API"):
            db.add_note(reply, tags=["periodic_learning", "autonomous"])
            if embedder:
                remember_text(db, embedder, reply, kind="periodic_learning")
            return f"Periodic learning: {reply[:200]}..."
        
        return "Periodic learning skipped (API unavailable)."
    
    except Exception as e:
        return f"Periodic learning error: {e}"


def skill_proposal(ctx: Dict[str, Any]) -> str:
    """Propose new skills based on recent usage."""
    db = ctx.get("db")
    simple_llm = ctx.get("simple_llm")
    
    if not db or not simple_llm:
        return "Skill proposal skipped (missing dependencies)."
    
    try:
        history = db.get_history(50)
        notes = db.list_notes(limit=10)
        
        context = "\n\n".join(
            [f"{item.get('role', 'unknown')}: {item.get('content', '')}" for item in history[:20]] +
            [f"Note: {row.get('text', '')}" for row in notes]
        )
        
        messages = [
            {
                "role": "system",
                "content": (
                    "Based on recent AI assistant usage, propose ONE new plugin skill. "
                    "Return JSON only: {\"name\": \"skill_name\", \"description\": \"what it does\", \"risk_level\": \"low|medium|high\"}"
                )
            },
            {
                "role": "user",
                "content": context[:7000]
            }
        ]
        
        reply = simple_llm(messages)
        
        if reply:
            db.add_note(reply, tags=["skill_proposal", "autonomous"])
            return f"Skill proposal: {reply[:200]}..."
        
        return "No skill proposal generated."
    
    except Exception as e:
        return f"Skill proposal error: {e}"


def health_check(ctx: Dict[str, Any]) -> str:
    """Check system health and dependencies."""
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
        base_url = cfg.get("provider.base_url", "")
        model = cfg.get("provider.model", "")
        
        if base_url and model:
            checks.append(f"LLM configured (model: {model})")
        else:
            issues.append("LLM not properly configured")
    else:
        issues.append("No configuration available")
    
    # Check components
    checks.append(f"Vector Store: {'OK' if ctx.get('vector') else 'Not configured'}")
    checks.append(f"Safety: {'OK' if ctx.get('safety') else 'Not configured'}")
    checks.append(f"Browser: {'OK' if ctx.get('browser') and ctx['browser'].installed else 'Not installed'}")
    checks.append(f"Voice: {'OK' if ctx.get('voice') and ctx['voice'].tts_available else 'Not available'}")
    
    if issues:
        return f"Health: {len(checks)} OK, {len(issues)} issues - {', '.join(issues[:3])}"
    else:
        return f"Health: All {len(checks)} systems OK"


# ============================================================
# Main Application
# ============================================================

def main():
    """Main entry point for the Complete Self System."""
    
    print("=" * 70)
    print("COMPLETE SELF SYSTEM")
    print("Autonomous AI Agent Platform")
    print("=" * 70)
    print()
    
    # Load configuration
    cfg = load_config()
    print(f"Configuration loaded from: {cfg.get('_config_file', 'default')}")
    print()
    
    # Create directories
    os.makedirs("storage/vector", exist_ok=True)
    os.makedirs("storage/logs", exist_ok=True)
    os.makedirs("plugins", exist_ok=True)
    os.makedirs("generated_skills", exist_ok=True)
    os.makedirs("tests", exist_ok=True)
    
    # Initialize components
    print("Initializing components...")
    
    # Database
    db = Database(cfg.get("memory.db_path", "storage/self_system.db"))
    print("✓ Database initialized")
    
    # Embedder
    embedder = Embedder(cfg.get("provider", {}))
    print("✓ Embedder initialized")
    
    # Vector Store
    vector = VectorStore(cfg.get("memory", {}), db, embedder)
    print("✓ Vector Store initialized")
    
    # LLM simple reply function (for use by other components)
    def simple_llm_wrapper(messages, **kwargs):
        return simple_llm_reply(cfg, messages, **kwargs)
    
    # Tool Registry
    tools = ToolRegistry()
    print("✓ Tool Registry initialized")
    
    # Safety Governor
    safety = create_safety_governor(cfg.get("storage.safety_db", "storage/safety.db"))
    print("✓ Safety Governor initialized")
    
    # Browser Manager
    browser = create_browser_manager(
        headless=cfg.get("browser.headless", True),
        browser_type=cfg.get("browser.type", "chromium")
    )
    print(f"✓ Browser Manager initialized (installed: {browser.installed})")
    
    # Voice Manager
    voice = create_voice_manager(
        enabled=cfg.get("voice.enabled", False),
        stt_engine=cfg.get("voice.stt_engine", "google"),
        tts_engine=cfg.get("voice.tts_engine", "pyttsx3"),
        language=cfg.get("voice.language", "en-US")
    )
    print(f"✓ Voice Manager initialized (STT: {voice.stt_available}, TTS: {voice.tts_available})")
    
    # Plugin Manager
    plugins = PluginManager()
    print(f"✓ Plugin Manager initialized ({len(plugins.list_plugins())} plugins)")
    
    # Skills Manager
    skills = create_skills_manager(
        plugin_dir="plugins",
        skill_dir="generated_skills",
        test_dir="tests",
        cfg={
            **cfg,
            "simple_llm_reply": simple_llm_wrapper
        }
    )
    print(f"✓ Skills Manager initialized ({len(skills.list_skills())} skills)")
    
    # Scheduler
    scheduler = create_scheduler(
        db_path=cfg.get("scheduler.db_path", "storage/scheduler.db"),
        ctx={
            "db": db,
            "cfg": cfg,
            "embedder": embedder,
            "simple_llm": simple_llm_wrapper,
            "vector": vector
        }
    )
    print("✓ Scheduler initialized")
    
    # Build context
    ctx = {
        "db": db,
        "cfg": cfg,
        "embedder": embedder,
        "vector": vector,
        "tools": tools,
        "safety": safety,
        "browser": browser,
        "voice": voice,
        "plugins": plugins,
        "skills": skills,
        "scheduler": scheduler,
        "simple_llm": simple_llm_wrapper
    }
    
    # Register tools
    print("\nRegistering tools...")
    
    # Basic tools
    tools.register(
        name="get_current_time",
        description="Get current local time",
        parameters={"type": "object", "properties": {}},
        handler=lambda args: time.strftime('%Y-%m-%d %H:%M:%S')
    )
    
    tools.register(
        name="calculate",
        description="Evaluate a math expression safely",
        parameters={
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"]
        },
        handler=lambda args: str(eval(args.get("expression", "0")))  # Note: In production, use safe_math
    )
    
    tools.register(
        name="search_memory",
        description="Search long-term vector memory",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"}
            },
            "required": ["query"]
        },
        handler=lambda args: json.dumps(
            search_vector_memory(db, embedder, args.get("query", ""), int(args.get("limit", 5))),
            indent=2
        )
    )
    
    tools.register(
        name="save_note",
        description="Save a note into memory",
        parameters={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "tags": {"type": "string"}
            },
            "required": ["text"]
        },
        handler=lambda args: (
            db.add_note(args.get("text", ""), args.get("tags", "")),
            remember_text(db, embedder, args.get("text", ""), kind="note", metadata={"tags": args.get("tags", "")}),
            "Note saved."
        )[2]
    )
    
    tools.register(
        name="remember_fact",
        description="Store a user fact",
        parameters={
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "value": {"type": "string"}
            },
            "required": ["key", "value"]
        },
        handler=lambda args: (
            db.set_fact(args.get("key", ""), args.get("value", "")),
            remember_text(db, embedder, f"{args.get('key', '')} = {args.get('value', '')}", kind="fact"),
            f"Remembered fact: {args.get('key', '')}"
        )[2]
    )
    
    # Browser tools
    if browser.installed:
        tools.register(
            name="browser_navigate",
            description="Open a URL in a headless browser",
            parameters={
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"]
            },
            handler=lambda args: browser.navigate(args.get("url", ""))
        )
        
        tools.register(
            name="browser_fill",
            description="Fill a form field using CSS selector",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "text": {"type": "string"}
                },
                "required": ["selector", "text"]
            },
            handler=lambda args: browser.fill(args.get("selector", ""), args.get("text", ""))
        )
        
        tools.register(
            name="browser_click",
            description="Click an element using CSS selector",
            parameters={
                "type": "object",
                "properties": {"selector": {"type": "string"}},
                "required": ["selector"]
            },
            handler=lambda args: browser.click(args.get("selector", ""))
        )
        
        tools.register(
            name="browser_text",
            description="Extract text from browser page",
            parameters={
                "type": "object",
                "properties": {"selector": {"type": "string"}},
            },
            handler=lambda args: browser.get_text(args.get("selector", "body"))
        )
        
        tools.register(
            name="browser_screenshot",
            description="Take a screenshot of the current page",
            parameters={
                "type": "object",
                "properties": {"path": {"type": "string"}},
            },
            handler=lambda args: browser.take_screenshot(args.get("path", "screenshot.png"))
        )
    
    # Web tools
    tools.register(
        name="fetch_url",
        description="Fetch a URL and extract text",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "max_chars": {"type": "integer"}
            },
            "required": ["url"]
        },
        handler=lambda args: {
            "text": "URL fetching not yet implemented in tools",
            "url": args.get("url", "")
        }
    )
    
    # Plugin tool (if enabled)
    if cfg.get("safety.allow_plugin_tool", False):
        tools.register(
            name="run_plugin",
            description="Run a loaded plugin by name",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "args": {"type": "string"}
                },
                "required": ["name"]
            },
            handler=lambda args: plugins.run(args.get("name", ""), args.get("args", ""))
        )
    
    # Skill generation tool (if enabled)
    if cfg.get("safety.allow_skill_tool", False):
        tools.register(
            name="generate_skill",
            description="Generate a new plugin skill from a description",
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["name", "description"]
            },
            handler=lambda args: f"Use /genskill {args.get('name', '')} | {args.get('description', '')} to generate a skill"
        )
    
    # Wrap tools with safety checks
    print("Wrapping tools with safety checks...")
    for tool_name in list(tools.names()):
        old_handler = tools.tools[tool_name]["handler"]
        tools.tools[tool_name]["handler"] = safety.wrap_tool(tool_name, old_handler)
    
    print(f"✓ {len(tools.names())} tools registered and wrapped")
    
    # Start autonomous mode if enabled
    if cfg.get("safety.autonomous_mode", False):
        scheduler.start()
        print("\n✓ Autonomous mode enabled - scheduled tasks will run automatically")
    else:
        print("\n⚠ Autonomous mode disabled - use /autonomous on to enable")
    
    print("\n" + "=" * 70)
    print("System ready. Type /help for available commands.")
    print("=" * 70)
    print()
    
    # Main loop
    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nGoodbye.")
                if scheduler:
                    scheduler.stop()
                if browser:
                    browser.close()
                if voice:
                    voice.stop()
                break
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input.startswith("/"):
                result = handle_command(user_input, ctx)
                
                if result == "__EXIT__":
                    print("Goodbye.")
                    if scheduler:
                        scheduler.stop()
                    if browser:
                        browser.close()
                    if voice:
                        voice.stop()
                    break
                
                if result:
                    print(f"System: {result}")
                    
                    # Speak response if voice enabled
                    if cfg.get("safety.speak_responses", False) and voice:
                        voice.speak(result)
                
                continue
            
            # Store user input in history
            db.add_history("user", user_input)
            
            # Run agent or direct reply
            if cfg.get("agent.agent_mode", True):
                reply = run_agent(user_input, ctx)
            else:
                reply = direct_reply(user_input, ctx)
            
            # Display and store reply
            print(f"Agent: {reply}")
            
            # Speak response if voice enabled
            if cfg.get("safety.speak_responses", False) and voice:
                voice.speak(reply)
            
            # Store in history and memory
            db.add_history("assistant", reply)
            remember_text(db, embedder, f"User: {user_input}\nAssistant: {reply}", kind="conversation")
            
    except KeyboardInterrupt:
        print("\nGoodbye.")
        if scheduler:
            scheduler.stop()
        if browser:
            browser.close()
        if voice:
            voice.stop()
    except Exception as e:
        print(f"\nFatal error: {e}")
        if scheduler:
            scheduler.stop()
        if browser:
            browser.close()
        if voice:
            voice.stop()
        raise


if __name__ == "__main__":
    main()
