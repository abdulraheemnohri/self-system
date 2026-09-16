"""
Complete Allostatic Self System - Core Package

This package contains all the modules for the Complete Allostatic Self System,
a self-growing AI agent with biologically-inspired internal regulation.
"""

__version__ = "1.0.0"
__author__ = "Abdulraheem Nohari"
__description__ = "Complete Allostatic Self System - A self-growing AI agent with memory, tools, self-reflection, and biological regulation"

# Package imports for easier access
from .config import load_config, save_config, get_setting, set_setting
from .db import connect, execute, query, create_tables, backup, close
from .event_bus import EventBus, subscribe, publish, unsubscribe, get_recent_events
from .llm import LLMClient, chat, chat_with_tools, stream_chat, embed, test_connection, estimate_tokens
from .embeddings import EmbeddingClient, generate_embedding, embed_texts
from .memory import MemorySystem, store_memory, retrieve_memory, search_memory, consolidate_memory
from .vector_store import VectorStore, add_vectors, search_vectors, delete_vectors
from .self_system import SelfSystem, self_report, self_critique, propose_improvements, add_goal
from .allostatic_regulator import AllostaticRegulator, tick, get_state, apply_event, compute_allostatic_load
from .neurochemistry import Neurochemistry, spike_dopamine, spike_cortisol, decay_chemicals
from .drives import Drives, get_drive, set_drive, increase_drive
from .sleep_engine import SleepEngine, should_sleep, start_sleep, collect_recent_memories
from .world_model import WorldModel, predict_outcome, estimate_cost, compute_surprise
from .planner import Planner, create_plan, execute_plan, simulate_plan
from .tool_registry import ToolRegistry, register_tool, unregister_tool, execute_tool, list_tools
from .skill_factory import SkillFactory, generate_skill, validate_skill, test_skill
from .self_testing import SelfTesting, run_tests, create_test_report
from .safety_governor import SafetyGovernor, can_execute, require_approval, check_budget
from .scheduler import Scheduler, add_task, remove_task, run_due_tasks
from .cli import CLI, run_cli
from .api import APIServer, run_api

__all__ = [
    # Config
    'load_config', 'save_config', 'get_setting', 'set_setting',
    
    # Database
    'connect', 'execute', 'query', 'create_tables', 'backup', 'close',
    
    # Event Bus
    'EventBus', 'subscribe', 'publish', 'unsubscribe', 'get_recent_events',
    
    # LLM
    'LLMClient', 'chat', 'chat_with_tools', 'stream_chat', 'embed', 'test_connection', 'estimate_tokens',
    
    # Embeddings
    'EmbeddingClient', 'generate_embedding', 'embed_texts',
    
    # Memory
    'MemorySystem', 'store_memory', 'retrieve_memory', 'search_memory', 'consolidate_memory',
    
    # Vector Store
    'VectorStore', 'add_vectors', 'search_vectors', 'delete_vectors',
    
    # Self System
    'SelfSystem', 'self_report', 'self_critique', 'propose_improvements', 'add_goal',
    
    # Allostatic Regulator
    'AllostaticRegulator', 'tick', 'get_state', 'apply_event', 'compute_allostatic_load',
    
    # Neurochemistry
    'Neurochemistry', 'spike_dopamine', 'spike_cortisol', 'decay_chemicals',
    
    # Drives
    'Drives', 'get_drive', 'set_drive', 'increase_drive',
    
    # Sleep Engine
    'SleepEngine', 'should_sleep', 'start_sleep', 'collect_recent_memories',
    
    # World Model
    'WorldModel', 'predict_outcome', 'estimate_cost', 'compute_surprise',
    
    # Planner
    'Planner', 'create_plan', 'execute_plan', 'simulate_plan',
    
    # Tool Registry
    'ToolRegistry', 'register_tool', 'unregister_tool', 'execute_tool', 'list_tools',
    
    # Skill Factory
    'SkillFactory', 'generate_skill', 'validate_skill', 'test_skill',
    
    # Self Testing
    'SelfTesting', 'run_tests', 'create_test_report',
    
    # Safety Governor
    'SafetyGovernor', 'can_execute', 'require_approval', 'check_budget',
    
    # Scheduler
    'Scheduler', 'add_task', 'remove_task', 'run_due_tasks',
    
    # CLI
    'CLI', 'run_cli',
    
    # API
    'APIServer', 'run_api',
]