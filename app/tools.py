"""
Tool Registry for Complete Self System
ٹولز رجسٹری برائے خود کار نظام
"""

import json
import math
import time
import datetime
import subprocess
import os
from typing import Dict, Any, List, Optional, Callable
from .db import db
from .llm import llm_client
from .vector_store import vector_store
from .config import config


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        self.register_tool('get_current_time', 'Get current time', self._get_current_time, {'timezone': {'type': 'string', 'default': 'UTC'}})
        self.register_tool('calculate', 'Perform calculations', self._calculate, {'expression': {'type': 'string', 'required': True}})
        self.register_tool('search_memory', 'Search memory', self._search_memory, {'query': {'type': 'string', 'required': True}, 'limit': {'type': 'integer', 'default': 5}})
        self.register_tool('save_note', 'Save a note', self._save_note, {'text': {'type': 'string', 'required': True}, 'tags': {'type': 'string', 'default': ''}})
        self.register_tool('remember_fact', 'Remember a fact', self._remember_fact, {'key': {'type': 'string', 'required': True}, 'value': {'type': 'string', 'required': True}})
        self.register_tool('get_fact', 'Get a fact', self._get_fact, {'key': {'type': 'string', 'required': True}})
        self.register_tool('fetch_url', 'Fetch URL', self._fetch_url, {'url': {'type': 'string', 'required': True}})
        self.register_tool('read_file', 'Read file', self._read_file, {'path': {'type': 'string', 'required': True}})
        self.register_tool('write_file', 'Write file', self._write_file, {'path': {'type': 'string', 'required': True}, 'content': {'type': 'string', 'required': True}}, requires_approval=True)
        self.register_tool('shell', 'Execute shell', self._shell, {'command': {'type': 'string', 'required': True}}, requires_approval=True)
    
    def register_tool(self, name: str, description: str, handler: Callable, parameters: Dict = None, requires_approval: bool = False):
        self.tools[name] = {'name': name, 'description': description, 'handler': handler, 'parameters': parameters or {}, 'requires_approval': requires_approval}
    
    def get_tool(self, name: str) -> Optional[Dict]:
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict]:
        return list(self.tools.values())
    
    def execute_tool(self, name: str, args: Dict) -> Any:
        tool = self.get_tool(name)
        if not tool:
            return f"Tool {name} not found"
        if tool.get('requires_approval', False):
            return f"Tool {name} requires approval"
        return tool['handler'](args)
    
    def _get_current_time(self, args):
        timezone = args.get('timezone', 'UTC')
        if timezone.upper() == 'UTC':
            return datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        try:
            import pytz
            tz = pytz.timezone(timezone)
            return datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')
        except:
            return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _calculate(self, args):
        expression = args.get('expression', '')
        if not expression:
            return "No expression"
        try:
            result = eval(expression, {'__builtins__': None}, {'sin': math.sin, 'cos': math.cos, 'tan': math.tan, 'sqrt': math.sqrt, 'log': math.log, 'log10': math.log10, 'exp': math.exp, 'pi': math.pi, 'e': math.e, 'pow': math.pow, 'abs': abs, 'round': round, 'min': min, 'max': max, 'sum': sum})
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _search_memory(self, args):
        query = args.get('query', '')
        limit = args.get('limit', 5)
        if not query:
            return "No query"
        results = vector_store.search(query, limit)
        if not results:
            return "No results"
        return "\n".join([f"{i+1}. [{r['score']*100:.0f}%] {r['text'][:200]}" for i, r in enumerate(results)])
    
    def _save_note(self, args):
        text = args.get('text', '')
        tags = args.get('tags', '')
        if not text:
            return "No text"
        note_id = db.add_note(text, tags)
        vector_store.add(text, kind='note', metadata={'tags': tags})
        return f"Note saved: {note_id}"
    
    def _remember_fact(self, args):
        key = args.get('key', '')
        value = args.get('value', '')
        if not key or not value:
            return "Key and value required"
        db.add_fact(key, value)
        vector_store.add(f"{key}: {value}", kind='fact', metadata={'key': key})
        return f"Fact saved: {key} = {value}"
    
    def _get_fact(self, args):
        key = args.get('key', '')
        fact = db.get_fact(key)
        return f"{fact['key']} = {fact['value']}" if fact else f"Fact {key} not found"
    
    def _fetch_url(self, args):
        url = args.get('url', '')
        if not url:
            return "No URL"
        try:
            import requests
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return f"URL: {url}\n\n{response.text[:10000]}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _read_file(self, args):
        path = args.get('path', '')
        if not path:
            return "No path"
        try:
            if not os.path.exists(path):
                return f"File not found: {path}"
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            if len(content) > 10000:
                content = content[:10000] + "\n\n... (truncated)"
            return f"File: {path}\n\n{content}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _write_file(self, args):
        path = args.get('path', '')
        content = args.get('content', '')
        if not path or not content:
            return "Path and content required"
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"File written: {path}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _shell(self, args):
        command = args.get('command', '')
        if not command:
            return "No command"
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout or result.stderr
            if len(output) > 5000:
                output = output[:5000] + "\n\n... (truncated)"
            return f"Exit code: {result.returncode}\n\n{output}"
        except Exception as e:
            return f"Error: {str(e)}"


tools = ToolRegistry()