#!/usr/bin/env python3
"""
Configuration Manager for Complete Self System

Provides:
- YAML configuration file loading
- Environment variable overrides
- Type conversion
- Default configuration
"""

import os
import yaml
import json
from typing import Dict, Any, Optional, List
from pathlib import Path


# Default configuration
DEFAULT_CONFIG = {
    # System settings
    "system": {
        "name": "Complete Self System",
        "version": "1.0.0",
        "mode": "development",
        "debug": False,
    },
    
    # Provider settings
    "provider": {
        "type": "openai-compatible",
        "base_url": "http://localhost:11434/v1",
        "api_key": "",
        "model": "llama3.1",
        "embedding_model": "nomic-embed-text",
        "use_api_embeddings": True,
        "timeout": 90,
        "max_tokens": 2000,
        "temperature": 0.2,
    },
    
    # Agent settings
    "agent": {
        "agent_mode": True,
        "enable_tool_calls": True,
        "max_agent_steps": 8,
        "context_turns": 12,
        "max_context_chars": 9000,
    },
    
    # Memory settings
    "memory": {
        "vector_backend": "sqlite",
        "db_path": "storage/self_system.db",
        "embedding_dim_fallback": 256,
        "similarity_threshold": 0.08,
        "knowledge_threshold": 0.82,
        "chroma": {
            "path": "storage/vector/chroma",
            "collection_name": "self_system_memory",
        },
        "faiss": {
            "path": "storage/vector/faiss.index",
            "dimension": 768,
        },
        "qdrant": {
            "url": "http://localhost:6333",
            "collection": "self_system",
        },
    },
    
    # Safety settings
    "safety": {
        "autonomous_mode": False,
        "auto_install_skills": False,
        "allow_plugin_tool": False,
        "allow_skill_tool": False,
        "speak_responses": False,
        "require_approval": [
            "browser_fill",
            "browser_click",
            "run_plugin",
            "generate_skill",
            "install_skill",
            "file_write",
            "shell",
            "execute_code",
        ],
        "disabled": [
            "shell",
            "execute_code",
        ],
    },
    
    # Voice settings
    "voice": {
        "enabled": False,
        "stt_engine": "google",
        "tts_engine": "pyttsx3",
        "language": "en-US",
        "rate": 150,
        "volume": 0.9,
    },
    
    # Browser settings
    "browser": {
        "headless": True,
        "type": "chromium",
        "timeout_ms": 30000,
        "wait_until": "domcontentloaded",
    },
    
    # Scheduler settings
    "scheduler": {
        "enabled": True,
        "db_path": "storage/scheduler.db",
        "default_tasks": [
            {
                "name": "memory_cleanup",
                "action": "memory_cleanup",
                "interval_seconds": 3600,
                "description": "Clean up old history and duplicate memories",
            },
            {
                "name": "self_review",
                "action": "self_review",
                "interval_seconds": 14400,
                "description": "Review recent conversations and suggest improvements",
            },
            {
                "name": "periodic_learning",
                "action": "periodic_learning",
                "interval_seconds": 43200,
                "description": "Summarize recent notes into long-term memory",
            },
            {
                "name": "skill_proposal",
                "action": "skill_proposal",
                "interval_seconds": 86400,
                "description": "Propose new skills based on recent usage",
            },
            {
                "name": "health_check",
                "action": "health_check",
                "interval_seconds": 21600,
                "description": "Check system health and dependencies",
            },
        ],
    },
    
    # Storage settings
    "storage": {
        "path": "storage",
        "safety_db": "storage/safety.db",
        "scheduler_db": "storage/scheduler.db",
        "plugins_dir": "plugins",
        "skills_dir": "generated_skills",
        "tests_dir": "tests",
    },
    
    # Plugin settings
    "plugins": {
        "auto_reload": True,
        "allow_dynamic": True,
    },
    
    # Logging settings
    "logging": {
        "level": "INFO",
        "file": "storage/self_system.log",
        "max_size": 10485760,
        "backup_count": 5,
    },
    
    # API settings
    "api": {
        "enabled": False,
        "host": "0.0.0.0",
        "port": 8000,
        "prefix": "/api/v1",
        "cors": True,
        "cors_origins": ["http://localhost:3000", "http://localhost:8080"],
    },
    
    # Dashboard settings
    "dashboard": {
        "enabled": False,
        "host": "0.0.0.0",
        "port": 8080,
        "title": "Complete Self System",
    },
    
    # Prompt settings
    "prompt": {
        "system": (
            "You are a complete self-growing AI assistant.\n"
            "Use tools when needed to accomplish tasks.\n"
            "Search memory for relevant information.\n"
            "Use memory only when relevant.\n"
            "Be concise, practical, and safe.\n"
            "If you do not know something, say so.\n"
            "Follow user instructions carefully."
        ),
        "starter": "How can I help you today?",
    },
}


class Config:
    """
    Configuration manager with YAML and environment variable support.
    
    Features:
    - Load from YAML file
    - Override with environment variables
    - Type conversion (bool, int, float)
    - Nested dictionary access
    - Save back to file
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the Config manager.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._config_file = None
        self._load_config()
        self._load_env_vars()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
                self._config_file = self.config_path
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            self._config = {}
            self._config_file = None
    
    def _load_env_vars(self) -> None:
        """Load configuration from environment variables."""
        # Mapping of environment variables to config keys
        env_mapping = {
            # Provider
            "AI_API_KEY": "provider.api_key",
            "AI_BASE_URL": "provider.base_url",
            "AI_MODEL": "provider.model",
            "AI_EMBEDDING_MODEL": "provider.embedding_model",
            "AI_TIMEOUT": "provider.timeout",
            "AI_MAX_TOKENS": "provider.max_tokens",
            "AI_TEMPERATURE": "provider.temperature",
            
            # Agent
            "AGENT_MODE": "agent.agent_mode",
            "ENABLE_TOOL_CALLS": "agent.enable_tool_calls",
            "MAX_AGENT_STEPS": "agent.max_agent_steps",
            "CONTEXT_TURNS": "agent.context_turns",
            "MAX_CONTEXT_CHARS": "agent.max_context_chars",
            
            # Memory
            "VECTOR_BACKEND": "memory.vector_backend",
            "DATABASE_PATH": "memory.db_path",
            "EMBEDDING_DIM_FALLBACK": "memory.embedding_dim_fallback",
            
            # Safety
            "AUTONOMOUS_MODE": "safety.autonomous_mode",
            "AUTO_INSTALL_SKILLS": "safety.auto_install_skills",
            "ALLOW_PLUGIN_TOOL": "safety.allow_plugin_tool",
            "ALLOW_SKILL_TOOL": "safety.allow_skill_tool",
            "SPEAK_RESPONSES": "safety.speak_responses",
            
            # Voice
            "VOICE_ENABLED": "voice.enabled",
            "VOICE_STT_ENGINE": "voice.stt_engine",
            "VOICE_TTS_ENGINE": "voice.tts_engine",
            "VOICE_LANGUAGE": "voice.language",
            "VOICE_RATE": "voice.rate",
            "VOICE_VOLUME": "voice.volume",
            
            # Browser
            "BROWSER_HEADLESS": "browser.headless",
            "BROWSER_TYPE": "browser.type",
            "BROWSER_TIMEOUT_MS": "browser.timeout_ms",
            
            # Scheduler
            "SCHEDULER_ENABLED": "scheduler.enabled",
            "SCHEDULER_DB_PATH": "scheduler.db_path",
        }
        
        for env_var, config_key in env_mapping.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                self._set_nested(config_key, self._convert_value(value))
    
    def _convert_value(self, value: str) -> Any:
        """Convert environment variable value to appropriate type."""
        if value.lower() in ('true', 'false', 'yes', 'no', '1', '0', 'on', 'off'):
            return value.lower() in ('true', 'yes', '1', 'on')
        
        try:
            return int(value)
        except ValueError:
            pass
        
        try:
            return float(value)
        except ValueError:
            pass
        
        # Try to parse as JSON
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
        
        return value
    
    def _set_nested(self, key: str, value: Any) -> None:
        """Set a nested key in the configuration."""
        keys = key.split('.')
        current = self._config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: Dot-separated key (e.g., "provider.base_url")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        current = self._config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by key.
        
        Args:
            key: Dot-separated key (e.g., "provider.base_url")
            value: Value to set
        """
        keys = key.split('.')
        current = self._config
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
        self._save_config()
    
    def _save_config(self) -> None:
        """Save configuration to YAML file."""
        if not self._config_file:
            return
        
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get the default configuration."""
        return DEFAULT_CONFIG
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        self._config = self.get_default_config()
        self._save_config()
    
    def to_dict(self) -> Dict[str, Any]:
        """Get the entire configuration as a dictionary."""
        return self._config
    
    def save_config(self, path: Optional[str] = None) -> None:
        """
        Save configuration to a specific path.
        
        Args:
            path: Path to save to (defaults to config_path)
        """
        save_path = path or self._config_file
        if not save_path:
            return
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")


# Global config instance
config = Config()


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Configuration dictionary
    """
    cfg = Config(config_path)
    return cfg.to_dict()


def save_config(cfg: Dict[str, Any], config_path: str = "config.yaml") -> None:
    """
    Save configuration to file.
    
    Args:
        cfg: Configuration dictionary
        config_path: Path to save to
    """
    # Create a temporary Config instance to save
    temp_config = Config()
    temp_config._config = cfg
    temp_config._config_file = config_path
    temp_config._save_config()
