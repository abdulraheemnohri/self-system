"""
Tool Registry for Complete Self System
ٹولز رجسٹری
"""

import json
import math
import operator
import ast
import hashlib
import re
from typing import Dict, Any, List, Callable, Optional
from .db import Database
from .vector_store import VectorStore


SAFE_FUNCS = {"abs": abs, "round": round, "min": min, "max": max, "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan, "log": math.log, "exp": math.exp, "floor": math.floor, "ceil": math.ceil}

SAFE_BINOPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow}

SAFE_UNARYOPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}


def safe_math(expression):
    expression = str(expression or "").strip().replace("^", "**")
    if not expression:
        raise ValueError("Empty expression")
    tree = ast.parse(expression, mode="eval")
    def _eval(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numeric constants allowed")
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
                raise ValueError("Only direct function calls allowed")
            name = node.func.id
            if name not in SAFE_FUNCS:
                raise ValueError(f"Function not allowed: {name}")
            if node.keywords:
                raise ValueError("Keyword arguments not allowed")
            args = [_eval(arg) for arg in node.args]
            return SAFE_FUNCS[name](*args)
        if isinstance(node, ast.Name):
            if node.id in SAFE_FUNCS:
                return SAFE_FUNCS[node.id]
            raise ValueError(f"Unknown name: {node.id}")
        raise ValueError("Unsupported expression element")
    return _eval(tree.body)


class ToolRegistry:
    """Registry for all available tools"""
    
    def __init__(self):
        self.tools = {}
    
    def register(self, name, description, parameters, handler):
        self.tools[name] = {"handler": handler, "schema": {"type": "function", "function": {"name": name, "description": description, "parameters": parameters}}}
    
    def schemas(self):
        return [tool["schema"] for tool in self.tools.values()]
    
    def names(self):
        return sorted(self.tools.keys())
    
    def exists(self, name):
        return name in self.tools
    
    def execute(self, name, args=None):
        if name not in self.tools:
            return f"Unknown tool: {name}"
        try:
            return self.tools[name]["handler"](args or {})
        except Exception as exc:
            return f"Tool error: {exc}"


class ToolFactory:
    """Factory for creating standard tools"""
    
    def __init__(self, db, vector_store):
        self.db = db
        self.vector = vector_store
        self.registry = ToolRegistry()
        self._register_standard_tools()
    
    def _register_standard_tools(self):
        self.registry.register("get_current_time", "Get current local time", {"type": "object", "properties": {}}, handler=lambda args: __import__("datetime").datetime.now().isoformat(timespec="seconds"))
        self.registry.register("calculate", "Evaluate a math expression safely", {"type": "object", "properties": {"expression": {"type": "string"}}, "required": ["expression"]}, handler=lambda args: safe_math(args.get("expression", "")))
        self.registry.register("search_memory", "Search long-term vector memory", {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}, handler=lambda args: json.dumps(self.vector.search_memory(args.get("query", ""), int(args.get("limit", 5))), indent=2, ensure_ascii=False))
        self.registry.register("save_note", "Save a note into memory", {"type": "object", "properties": {"text": {"type": "string"}, "tags": {"type": "string"}}, "required": ["text"]}, handler=lambda args: (self.db.add_note(args.get("text", ""), args.get("tags", "")), self.vector.remember_note(args.get("text", ""), args.get("tags", "")), "Note saved.")[2])
        self.registry.register("remember_fact", "Store a user fact", {"type": "object", "properties": {"key": {"type": "string"}, "value": {"type": "string"}}, "required": ["key", "value"]}, handler=lambda args: (self.db.set_fact(args.get("key", ""), args.get("value", "")), self.vector.remember_fact(args.get("key", ""), args.get("value", "")), f"Remembered fact: {args.get('key', "" )}")[2])
    
    def get_registry(self):
        return self.registry


_tool_factory = None

def get_tool_registry(db, vector_store):
    global _tool_factory
    if _tool_factory is None:
        _tool_factory = ToolFactory(db, vector_store)
    return _tool_factory.get_registry()