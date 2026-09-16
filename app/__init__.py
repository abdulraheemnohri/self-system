#!/usr/bin/env python3
"""
Complete Self System Package

This package contains all the modules for the autonomous AI agent.

Features:
- LLM integration (OpenAI, Ollama, Groq, etc.)
- Vector memory (SQLite, ChromaDB, FAISS, Qdrant)
- Tool calling (OpenAI-compatible function calling)
- Agent planning loop
- Browser automation (Playwright)
- Voice input/output (SpeechRecognition, pyttsx3)
- Plugin system
- Automatic skill generation
- Self-testing
- Scheduled autonomous tasks
- Safety governor
- Audit logging

Author: Abdulraheem Nohari
License: MIT
"""

__version__ = "1.0.0"
__author__ = "Abdulraheem Nohri"
__description__ = "Complete Self System - Autonomous AI Agent Platform"

# Import key modules for easy access
from .config import load_config, save_config, DEFAULT_CONFIG
from .db import Database
from .llm import Embedder, call_chat_api_raw, simple_llm_reply
from .vector_store import VectorStore, remember_text, search_vector_memory
from .tools import ToolRegistry
from .safety import SafetyGovernor, create_safety_governor
from .browser import BrowserManager, create_browser_manager
from .voice import VoiceManager, create_voice_manager
from .plugins import PluginManager
from .skills import SkillsManager, create_skills_manager
from .scheduler import AutonomousScheduler, create_scheduler
from .agent import run_agent, direct_reply, build_context

__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "load_config",
    "save_config", 
    "DEFAULT_CONFIG",
    "Database",
    "Embedder",
    "call_chat_api_raw",
    "simple_llm_reply",
    "VectorStore",
    "remember_text",
    "search_vector_memory",
    "ToolRegistry",
    "SafetyGovernor",
    "create_safety_governor",
    "BrowserManager",
    "create_browser_manager",
    "VoiceManager",
    "create_voice_manager",
    "PluginManager",
    "SkillsManager",
    "create_skills_manager",
    "AutonomousScheduler",
    "create_scheduler",
    "run_agent",
    "direct_reply",
    "build_context",
]
