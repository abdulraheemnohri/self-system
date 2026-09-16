"""
Agent Loop for Complete Self System
ایجنٹ لوپ
"""

import json
import re
from typing import Dict, Any, List, Optional
from .config import get_config
from .llm import get_llm_client
from .db import Database
from .vector_store import VectorStore
from .tools import get_tool_registry


class Agent:
    """Autonomous agent that plans and executes tasks"""
    
    def __init__(self, db, vector_store):
        self.db = db
        self.vector = vector_store
        self.cfg = get_config()
        self.llm = get_llm_client()
        self.tools = get_tool_registry(db, vector_store)
    
    def build_context(self, user_input):
        facts = self.db.get_facts()
        fact_lines = "\n".join(f"- {k}: {v}" for k, v in facts.items()) or "None"
        memories = self.vector.search_memory(user_input, limit=5)
        memory_lines = "\n".join(f"- [{item["kind"]} score={item["score"]:.2f}] {item["text"]}" for item in memories) or "None"
        system_prompt = self.cfg.get("system", "prompt") or "You are Mega Agent, a self-growing AI assistant."
        return f"""{system_prompt}

Current time: {self._get_current_time()}

Stored facts:
{fact_lines}

Relevant vector memory:
{memory_lines}

Use tools only when needed.
If a tool result is useful, continue.
When the task is complete, return a final natural-language answer."""
    
    def _get_current_time(self):
        from datetime import datetime
        return datetime.now().isoformat(timespec="seconds")
    
    def run(self, user_input):
        history = self.db.get_history(int(self.cfg.get("agent", "context_turns") or 12))
        messages = [{"role": "system", "content": self.build_context(user_input)}]
        for row in history:
            messages.append({"role": row.get("role", "user"), "content": row.get("content", "")})
        messages.append({"role": "user", "content": user_input})
        max_steps = int(self.cfg.get("agent", "max_agent_steps") or 8)
        for step in range(max_steps):
            use_tools = self.cfg.get("agent", "enable_tool_calls", True)
            tool_schemas = self.tools.schemas() if use_tools else None
            result = self.llm.call_chat_api(messages, tools=tool_schemas)
            if "_error" in result and use_tools:
                result = self.llm.call_chat_api(messages, tools=None)
            if "_error" in result:
                return result["_error"]
            tool_calls = result.get("tool_calls")
            if tool_calls:
                assistant_message = {"role": "assistant", "content": result.get("content") or "", "tool_calls": tool_calls}
                messages.append(assistant_message)
                for call in tool_calls:
                    function_info = call.get("function", {})
                    tool_name = function_info.get("name", "")
                    arguments_text = function_info.get("arguments", "{}")
                    try:
                        arguments = json.loads(arguments_text)
                    except Exception:
                        arguments = {}
                    tool_result = self.tools.execute(tool_name, arguments)
                    messages.append({"role": "tool", "tool_call_id": call.get("id", ""), "name": tool_name, "content": str(tool_result)[:4000]})
                continue
            content = result.get("content", "") or ""
            action = self._parse_json_action(content)
            if action and "tool" in action and self.tools.exists(action.get("tool")):
                messages.append({"role": "assistant", "content": content})
                tool_result = self.tools.execute(action.get("tool"), action.get("args", {}))
                messages.append({"role": "tool", "content": str(tool_result)[:4000]})
                continue
            return content
        return "Agent stopped: max steps reached."
    
    def _parse_json_action(self, text):
        try:
            match = re.search(r"\{.*\}", str(text), re.DOTALL)
            if not match:
                return None
            data = json.loads(match.group(0))
            if isinstance(data, dict):
                return data
        except Exception:
            return None
        return None
    
    def direct_reply(self, user_input):
        history = self.db.get_history(int(self.cfg.get("agent", "context_turns") or 12))
        messages = [{"role": "system", "content": self.build_context(user_input)}]
        for row in history:
            messages.append({"role": row.get("role", "user"), "content": row.get("content", "")})
        messages.append({"role": "user", "content": user_input})
        result = self.llm.call_chat_api(messages, tools=None)
        if "_error" in result:
            return result["_error"]
        return result.get("content", "") or ""