#!/usr/bin/env python3
"""
Tool Registry for Complete Self System

Provides:
- Tool registration and management
- OpenAI-compatible tool schemas
- Tool execution with safety checks
- Built-in tools (time, math, memory, etc.)
"""

import json
import math
import time
import datetime
import ast
import operator
from typing import Dict, Any, List, Optional, Callable


# Safe math functions
SAFE_FUNCS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "pow": math.pow,
    "pi": math.pi,
    "e": math.e,
}

SAFE_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

SAFE_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def safe_math(expression: str) -> float:
    """
    Evaluate a math expression safely.
    
    Args:
        expression: Math expression string
        
    Returns:
        Result of the expression
        
    Raises:
        ValueError: If expression is invalid or unsafe
    """
    expression = str(expression or "").strip().replace("^", "**")
    
    if not expression:
        raise ValueError("Empty expression")
    
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid expression: {exc}") from exc
    
    def _eval(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numeric constants are allowed")
        
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in SAFE_BINOPS:
                raise ValueError("Unsupported binary operator")
            return SAFE_BINOPS[op_type](_eval(node.left), _eval(node.right))
        
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in SAFE_UNARYOPS:
                raise ValueError("Unsupported unary operator")
            return SAFE_UNARYOPS[op_type](_eval(node.operand))
        
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only direct function calls are allowed")
            func_name = node.func.id
            if func_name not in SAFE_FUNCS:
                raise ValueError(f"Function not allowed: {func_name}")
            if node.keywords:
                raise ValueError("Keyword arguments are not allowed")
            args = [_eval(arg) for arg in node.args]
            return SAFE_FUNCS[func_name](*args)
        
        if isinstance(node, ast.Name):
            if node.id in SAFE_FUNCS:
                return SAFE_FUNCS[node.id]
            raise ValueError(f"Unknown name: {node.id}")
        
        raise ValueError("Unsupported expression element")
    
    return _eval(tree.body)


class ToolRegistry:
    """
    Registry for managing tools that can be called by the LLM.
    
    Features:
    - Register tools with schemas
    - List available tools
    - Execute tools by name
    - Generate OpenAI-compatible tool schemas
    """
    
    def __init__(self):
        """Initialize the ToolRegistry."""
        self.tools: Dict[str, Dict[str, Any]] = {}
    
    def register(self, name: str, description: str, parameters: Dict[str, Any], 
                 handler: Callable) -> None:
        """
        Register a new tool.
        
        Args:
            name: Tool name
            description: Tool description
            parameters: JSON Schema for tool parameters
            handler: Function to execute the tool
        """
        self.tools[name] = {
            "handler": handler,
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            },
        }
    
    def schemas(self) -> List[Dict[str, Any]]:
        """
        Get OpenAI-compatible tool schemas for all registered tools.
        
        Returns:
            List of tool schema dictionaries
        """
        return [tool["schema"] for tool in self.tools.values()]
    
    def names(self) -> List[str]:
        """
        Get list of all registered tool names.
        
        Returns:
            List of tool names
        """
        return sorted(self.tools.keys())
    
    def exists(self, name: str) -> bool:
        """
        Check if a tool exists.
        
        Args:
            name: Tool name to check
            
        Returns:
            True if tool exists
        """
        return name in self.tools
    
    def execute(self, name: str, args: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name
            args: Arguments to pass to the tool
            
        Returns:
            Result of the tool execution
        """
        if name not in self.tools:
            return f"Unknown tool: {name}"
        
        try:
            args = args or {}
            return self.tools[name]["handler"](args)
        except Exception as exc:
            return f"Tool error in {name}: {exc}"


# Global tool registry instance
tools = ToolRegistry()


# ============================================================
# Register Built-in Tools
# ============================================================

def register_builtin_tools(db=None, vector_store=None, browser=None, voice=None):
    """
    Register all built-in tools.
    
    Args:
        db: Database instance
        vector_store: Vector store instance
        browser: Browser manager instance
        voice: Voice manager instance
    """
    # Time tool
    tools.register(
        name="get_current_time",
        description="Get current local time",
        parameters={
            "type": "object",
            "properties": {},
        },
        handler=lambda args: datetime.datetime.now().isoformat(timespec="seconds")
    )
    
    # Math tool
    tools.register(
        name="calculate",
        description="Evaluate a math expression safely",
        parameters={
            "type": "object",
            "properties": {
                "expression": {"type": "string"},
            },
            "required": ["expression"],
        },
        handler=lambda args: safe_math(args.get("expression", "0"))
    )
    
    # Search memory tool
    if vector_store:
        tools.register(
            name="search_memory",
            description="Search long-term vector memory",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
            },
            handler=lambda args: json.dumps(
                vector_store.search(
                    args.get("query", ""),
                    int(args.get("limit", 5))
                ),
                indent=2
            )
        )
    
    # Save note tool
    if db:
        tools.register(
            name="save_note",
            description="Save a note into memory",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "tags": {"type": "string"},
                },
                "required": ["text"],
            },
            handler=lambda args: (
                db.add_note(args.get("text", ""), args.get("tags", "")),
                "Note saved."
            )[1]
        )
    
    # Remember fact tool
    if db:
        tools.register(
            name="remember_fact",
            description="Store a user fact",
            parameters={
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "value": {"type": "string"},
                },
                "required": ["key", "value"],
            },
            handler=lambda args: (
                db.set_fact(args.get("key", ""), args.get("value", "")),
                f"Remembered fact: {args.get('key', '')}"
            )[1]
        )
    
    # Fetch URL tool
    tools.register(
        name="fetch_url",
        description="Fetch a URL and extract text",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "max_chars": {"type": "integer"},
            },
            "required": ["url"],
        },
        handler=lambda args: {
            "text": "URL fetching not implemented in tools (use /browser open instead)",
            "url": args.get("url", "")
        }
    )
    
    # Browser tools
    if browser and browser.installed:
        tools.register(
            name="browser_navigate",
            description="Open a URL in a headless browser",
            parameters={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                },
                "required": ["url"],
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
                    "text": {"type": "string"},
                },
                "required": ["selector", "text"],
            },
            handler=lambda args: browser.fill(
                args.get("selector", ""),
                args.get("text", "")
            )
        )
        
        tools.register(
            name="browser_click",
            description="Click an element using CSS selector",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                },
                "required": ["selector"],
            },
            handler=lambda args: browser.click(args.get("selector", ""))
        )
        
        tools.register(
            name="browser_text",
            description="Extract text from browser page",
            parameters={
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                },
            },
            handler=lambda args: browser.get_text(args.get("selector", "body"))
        )
        
        tools.register(
            name="browser_screenshot",
            description="Take a screenshot of the current page",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                },
            },
            handler=lambda args: browser.take_screenshot(args.get("path", "screenshot.png"))
        )
    
    # Voice tools
    if voice:
        tools.register(
            name="speak",
            description="Speak text aloud",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                },
                "required": ["text"],
            },
            handler=lambda args: voice.speak(args.get("text", ""))
        )
        
        tools.register(
            name="listen",
            description="Listen to microphone input",
            parameters={
                "type": "object",
                "properties": {
                    "timeout": {"type": "number"},
                    "phrase_time_limit": {"type": "number"},
                },
            },
            handler=lambda args: voice.listen(
                timeout=float(args.get("timeout", 5.0)),
                phrase_time_limit=float(args.get("phrase_time_limit", 15.0))
            )
        )
