#!/usr/bin/env python3
"""
Agent Module for Complete Self System

Provides:
- Agent loop (Plan, Execute, Observe, Learn)
- Context building with memory and facts
- Tool calling integration
- Direct reply without tools
"""

import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path


class Agent:
    """
    Agent that can call tools and use memory to accomplish tasks.
    
    Features:
    - Multi-step tool calling
    - Memory retrieval
    - Context building
    - Conversation history
    """
    
    def __init__(self, db=None, cfg=None, embedder=None, tools=None):
        """
        Initialize the Agent.
        
        Args:
            db: Database instance
            cfg: Configuration dictionary
            embedder: Embedder instance
            tools: ToolRegistry instance
        """
        self.db = db
        self.cfg = cfg or {}
        self.embedder = embedder
        self.tools = tools
        self.history = []
    
    def build_context(self, query: str = "") -> str:
        """
        Build the context for LLM with memory and facts.
        
        Args:
            query: User query
            
        Returns:
            Context string
        """
        if not self.db or not self.embedder:
            return ""
        
        # Get facts
        facts = self.db.get_facts()
        fact_lines = "\n".join(f"- {k}: {v}" for k, v in facts.items()) or "None"
        
        # Search vector memory
        from app.vector_store import search_vector_memory
        memories = search_vector_memory(self.db, self.embedder, query, limit=5)
        memory_lines = "\n".join(
            f"- [{item['kind']} score={item['score']:.2f}] {item['text'][:200]}"
            for item in memories
        ) or "None"
        
        system_prompt = self.cfg.get('prompt.system', 
            "You are a complete self-growing AI assistant. "
            "Use tools when needed to accomplish tasks. "
            "Search memory for relevant information. "
            "Use memory only when relevant. "
            "Be concise, practical, and safe. "
            "If you do not know something, say so."
        )
        
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
    
    def run(self, user_input: str) -> str:
        """
        Run the agent loop with tool calling.
        
        Args:
            user_input: User input
            
        Returns:
            Agent response
        """
        if not self.db or not self.cfg or not self.embedder or not self.tools:
            return "Agent components not initialized."
        
        history = self.db.get_history(int(self.cfg.get("agent.context_turns", 12)))
        
        messages = [
            {
                "role": "system",
                "content": self.build_context(user_input)
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
        
        max_steps = int(self.cfg.get("agent.max_agent_steps", 8))
        
        for step in range(max_steps):
            use_tools = self.cfg.get("agent.enable_tool_calls", True)
            tool_schemas = self.tools.schemas() if use_tools else None
            
            # Import here to avoid circular imports
            from app.llm import call_chat_api_raw
            message = call_chat_api_raw(self.cfg, messages, tools=tool_schemas)
            
            # Some providers reject tools. Retry without tools.
            if "_error" in message and use_tools:
                message = call_chat_api_raw(self.cfg, messages, tools=None)
            
            if "_error" in message:
                return message["_error"]
            
            # Check for tool calls
            tool_calls = message.get("tool_calls")
            
            if tool_calls:
                # Add assistant message with tool calls
                assistant_message = {
                    "role": "assistant",
                    "content": message.get("content") or "",
                    "tool_calls": tool_calls
                }
                messages.append(assistant_message)
                
                # Execute each tool call
                for call in tool_calls:
                    function_info = call.get("function", {})
                    tool_name = function_info.get("name", "")
                    arguments_text = function_info.get("arguments", "{}")
                    
                    try:
                        arguments = json.loads(arguments_text)
                    except Exception:
                        arguments = {}
                    
                    # Execute the tool
                    result = self.tools.execute(tool_name, arguments)
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.get("id", ""),
                        "name": tool_name,
                        "content": str(result)[:4000]
                    })
                
                # Continue to next step
                continue
            
            # No tool calls, return the content
            content = message.get("content", "") or ""
            return content
        
        return "Agent stopped: max steps reached"
    
    def direct_reply(self, user_input: str) -> str:
        """
        Get a direct LLM reply without agent tools.
        
        Args:
            user_input: User input
            
        Returns:
            LLM response
        """
        if not self.db or not self.cfg or not self.embedder:
            return "Agent components not initialized."
        
        history = self.db.get_history(int(self.cfg.get("agent.context_turns", 12)))
        
        messages = [
            {
                "role": "system",
                "content": self.build_context(user_input)
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
        
        # Import here to avoid circular imports
        from app.llm import call_chat_api_raw
        message = call_chat_api_raw(self.cfg, messages, tools=None)
        
        if "_error" in message:
            return message["_error"]
        
        return message.get("content", "") or ""


# Standalone functions (for use without Agent class)
def build_context(db, cfg: Dict[str, Any], embedder, query: str = "") -> str:
    """
    Build context for LLM with memory and facts (standalone function).
    
    Args:
        db: Database instance
        cfg: Configuration dictionary
        embedder: Embedder instance
        query: User query
        
    Returns:
        Context string
    """
    if not db or not embedder:
        return ""
    
    # Get facts
    facts = db.get_facts()
    fact_lines = "\n".join(f"- {k}: {v}" for k, v in facts.items()) or "None"
    
    # Search vector memory
    from app.vector_store import search_vector_memory
    memories = search_vector_memory(db, embedder, query, limit=5)
    memory_lines = "\n".join(
        f"- [{item['kind']} score={item['score']:.2f}] {item['text'][:200]}"
        for item in memories
    ) or "None"
    
    system_prompt = cfg.get('prompt.system', 
        "You are a complete self-growing AI assistant. "
        "Use tools when needed to accomplish tasks. "
        "Search memory for relevant information. "
        "Use memory only when relevant. "
        "Be concise, practical, and safe. "
        "If you do not know something, say so."
    )
    
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
    Run the agent loop with tool calling (standalone function).
    
    Args:
        user_input: User input
        ctx: Context dictionary with db, cfg, embedder, tools
        
    Returns:
        Agent response
    """
    db = ctx.get("db")
    cfg = ctx.get("cfg", {})
    embedder = ctx.get("embedder")
    tools = ctx.get("tools")
    
    history = db.get_history(int(cfg.get("agent.context_turns", 12))) if db else []
    
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
    
    from app.llm import call_chat_api_raw
    max_steps = int(cfg.get("agent.max_agent_steps", 8))
    
    for step in range(max_steps):
        use_tools = cfg.get("agent.enable_tool_calls", True)
        tool_schemas = tools.schemas() if use_tools and tools else None
        
        message = call_chat_api_raw(cfg, messages, tools=tool_schemas)
        
        # Some providers reject tools. Retry without tools.
        if "_error" in message and use_tools:
            message = call_chat_api_raw(cfg, messages, tools=None)
        
        if "_error" in message:
            return message["_error"]
        
        # Check for tool calls
        tool_calls = message.get("tool_calls")
        
        if tool_calls:
            # Add assistant message with tool calls
            assistant_message = {
                "role": "assistant",
                "content": message.get("content") or "",
                "tool_calls": tool_calls
            }
            messages.append(assistant_message)
            
            # Execute each tool call
            for call in tool_calls:
                function_info = call.get("function", {})
                tool_name = function_info.get("name", "")
                arguments_text = function_info.get("arguments", "{}")
                
                try:
                    arguments = json.loads(arguments_text)
                except Exception:
                    arguments = {}
                
                # Execute the tool
                result = tools.execute(tool_name, arguments)
                
                # Add tool result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.get("id", ""),
                    "name": tool_name,
                    "content": str(result)[:4000]
                })
            
            # Continue to next step
            continue
        
        # No tool calls, return the content
        content = message.get("content", "") or ""
        return content
    
    return "Agent stopped: max steps reached"


def direct_reply(user_input: str, ctx: Dict[str, Any]) -> str:
    """
    Get a direct LLM reply without agent tools (standalone function).
    
    Args:
        user_input: User input
        ctx: Context dictionary
        
    Returns:
        LLM response
    """
    db = ctx.get("db")
    cfg = ctx.get("cfg", {})
    embedder = ctx.get("embedder")
    
    history = db.get_history(int(cfg.get("agent.context_turns", 12))) if db else []
    
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
    
    from app.llm import call_chat_api_raw
    message = call_chat_api_raw(cfg, messages, tools=None)
    
    if "_error" in message:
        return message["_error"]
    
    return message.get("content", "") or ""


def parse_json_action(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse a JSON action from text (fallback for providers without tool calling).
    
    Args:
        text: Text to parse
        
    Returns:
        Action dictionary or None
    """
    try:
        import re
        match = re.search(r"\{.*\}", str(text), re.DOTALL)
        if not match:
            return None
        
        data = json.loads(match.group(0))
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    
    return None
