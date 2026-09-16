"""
Agent Core for Complete Self System

Implements the agent loop: perceive, retrieve, plan, act, observe, learn
"""

import json
import time
from typing import List, Dict, Any, Optional, Tuple
from .config import config
from .llm import llm_client, simple_llm_reply
from .db import db
from .vector_store import vector_store
from .tools import tools


class Agent:
    def __init__(self):
        self.max_steps = config.get('agent.max_agent_steps', 10)
        self.context_turns = config.get('agent.context_turns', 16)
        self.enable_tool_calls = config.get('agent.enable_tool_calls', True)
        self.history: List[Dict[str, Any]] = []
    
    def reset_context(self) -> None:
        self.history = []
    
    def add_to_history(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        self.history.append({'role': role, 'content': content, 'metadata': metadata or {}, 'timestamp': time.time()})
        if len(self.history) > self.context_turns * 2:
            self.history = self.history[-self.context_turns * 2:]
        db.add_history(role, content)
    
    def get_context(self) -> List[Dict[str, Any]]:
        return [{'role': msg['role'], 'content': msg['content']} for msg in self.history]
    
    def _retrieve_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        vector_results = vector_store.search(query, limit)
        fact_results = db.get_facts(limit)
        knowledge_results = db.search_knowledge(query, limit)
        all_results = []
        seen_texts = set()
        for result in vector_results + fact_results + knowledge_results:
            text = result.get('text', '') or result.get('content', '') or f"{result.get('key')}: {result.get('value')}"
            if text and text not in seen_texts:
                seen_texts.add(text)
                all_results.append(result)
        return all_results[:limit]
    
    def _format_memory(self, memories: List[Dict[str, Any]]) -> str:
        if not memories:
            return ""
        parts = []
        for i, mem in enumerate(memories, 1):
            text = mem.get('text', '') or mem.get('content', '') or f"{mem.get('key')}: {mem.get('value')}"
            score = mem.get('score', 0)
            kind = mem.get('kind', mem.get('category', 'note'))
            parts.append(f"Memory {i} [{kind}] (relevance: {score*100:.0f}%): {text[:500]}")
        return "\n".join(parts)
    
    def _plan(self, query: str, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        context = self.get_context()
        memory_text = self._format_memory(memories)
        prompt = f"Plan how to answer: {query}\n\nMemories:\n{memory_text}"
        messages = [{'role': 'system', 'content': 'You are a helpful AI planning assistant.'}, {'role': 'user', 'content': prompt}]
        response = simple_llm_reply(messages, max_tokens=2000, temperature=0.3)
        try:
            data = json.loads(response)
            return data.get('steps', [])
        except:
            return [{'action': 'respond', 'content': response}]
    
    def _execute_step(self, step: Dict[str, Any]) -> Tuple[str, bool]:
        action = step.get('action', '')
        if action == 'tool':
            tool_name = step.get('tool', '')
            args = step.get('args', {})
            tool = tools.get_tool(tool_name)
            if not tool:
                return f"Tool {tool_name} not found.", False
            if tool.get('requires_approval', False):
                return f"Tool {tool_name} requires approval.", False
            try:
                result = tools.execute_tool(tool_name, args)
                return f"Tool {tool_name}: {result}", False
            except Exception as e:
                return f"Tool {tool_name} failed: {str(e)}", False
        elif action == 'respond':
            return step.get('content', ''), True
        return f"Unknown action: {action}", False
    
    def run(self, query: str) -> str:
        self.add_to_history('user', query)
        memories = self._retrieve_memory(query, limit=5)
        plan = self._plan(query, memories)
        results = []
        for step in plan[:self.max_steps]:
            result, is_final = self._execute_step(step)
            results.append(result)
            if is_final:
                break
        response = "\n\n".join(results)
        self.add_to_history('assistant', response)
        vector_store.add(f"Q: {query}\nA: {response}", kind='conversation')
        return response
    
    def direct_reply(self, query: str) -> str:
        memories = self._retrieve_memory(query, limit=5)
        memory_text = self._format_memory(memories)
        context = self.get_context()
        context_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context[-4:]])
        prompt = f"Answer: {query}\n\nContext:\n{context_text}\n\nMemories:\n{memory_text}"
        messages = [{'role': 'system', 'content': 'You are a helpful AI assistant.'}, {'role': 'user', 'content': prompt}]
        response = simple_llm_reply(messages, max_tokens=4096, temperature=0.7)
        self.add_to_history('user', query)
        self.add_to_history('assistant', response)
        vector_store.add(f"Q: {query}\nA: {response}", kind='conversation')
        return response
    
    def handle_command(self, command: str) -> str:
        command = command.strip().lower()
        if command in ('/help', 'help'):
            return self._help()
        elif command.startswith('/remember '):
            parts = command.split(' ', 2)
            if len(parts) >= 3:
                key, value = parts[1], parts[2]
                db.add_fact(key, value)
                vector_store.add(f"{key}: {value}", kind='fact', metadata={'key': key})
                return f"Remembered: {key} = {value}"
            return "Usage: /remember <key> <value>"
        elif command.startswith('/note '):
            text = command[6:].strip()
            if text:
                db.add_note(text)
                vector_store.add(text, kind='note')
                return f"Note saved: {text[:100]}"
            return "Usage: /note <text>"
        elif command in ('/facts', 'facts'):
            facts = db.get_facts(20)
            return "\n".join([f"{f['key']} = {f['value']}" for f in facts]) if facts else "No facts."
        elif command in ('/notes', 'notes'):
            notes = db.list_notes(20)
            return "\n".join([f"- {n['text'][:200]}" for n in notes]) if notes else "No notes."
        elif command in ('/memory', 'memory'):
            return str(vector_store.get_stats())
        elif command in ('/tools', 'tools'):
            return "Tools:\n" + "\n".join([f"- {t['name']}: {t['description']}" for t in tools.list_tools()])
        elif command in ('/clear', 'clear'):
            self.reset_context()
            return "Context cleared."
        elif command in ('/stats', 'stats'):
            return str(db.get_stats())
        return f"Unknown command: {command}"
    
    def _help(self) -> str:
        return "Complete Self System Commands:\n/remember <k> <v> - Remember fact\n/note <t> - Save note\n/facts - List facts\n/notes - List notes\n/tools - List tools\n/clear - Clear context\n/stats - Stats\n/help - Help\n/exit - Exit"


agent = Agent()

def run_agent(query: str) -> str:
    use_agent_mode = config.get('agent.agent_mode', True)
    enable_tool_calls = config.get('agent.enable_tool_calls', True)
    if use_agent_mode and enable_tool_calls:
        return agent.run(query)
    return agent.direct_reply(query)

def direct_reply(query: str) -> str:
    return agent.direct_reply(query)
