"""
Configuration Manager for Complete Self System
کنفیگریشن مینیجر
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Load and manage configuration from multiple sources"""
    
    DEFAULT_CONFIG = {
        "system": {
            "name": "Complete Self System",
            "version": "1.0.0",
            "mode": "development",
        },
        "provider": {
            "base_url": "http://localhost:11434/v1",
            "api_key": "",
            "model": "llama3.1",
            "embedding_model": "nomic-embed-text",
            "timeout": 90
        },
        "agent": {
            "agent_mode": True,
            "enable_tool_calls": True,
            "max_agent_steps": 10,
            "context_turns": 16
        },
        "memory": {
            "vector_backend": "sqlite",
            "embedding_dim_fallback": 256
        },
        "safety": {
            "autonomous_mode": False,
            "auto_install_skills": False,
            "allow_plugin_tool": False,
            "allow_skill_tool": False
        },
        "voice": {
            "enabled": False,
            "speak_responses": False
        },
        "browser": {
            "headless": True,
            "timeout_ms": 30000
        },
        "scheduler": {
            "enabled": True,
            "tasks": [
                {"name": "memory_cleanup", "action": "maintenance", "interval_seconds": 3600},
                {"name": "self_review", "action": "self_review", "interval_seconds": 14400}
            ]
        }
    }
    
    def __init__(self, config_path=None):
        self.config_path = config_path or self._find_config_path()
        self.config = dict(self.DEFAULT_CONFIG)
        self._load_config()
        self._load_env()
    
    def _find_config_path(self):
        return "config.yaml"
    
    def _load_config(self):
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = yaml.safe_load(f)
                    if loaded:
                        self._deep_update(self.config, loaded)
        except Exception:
            pass
    
    def _load_env(self):
        pass
    
    def _deep_update(self, target, source):
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def get(self, *keys, default=None):
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default
        return value
    
    def set(self, *keys, value):
        current = self.config
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    def save(self, path=None):
        save_path = path or self.config_path
        try:
            with open(save_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
            return True
        except Exception:
            return False
    
    def as_dict(self):
        return dict(self.config)


config = ConfigManager()

def get_config():
    return config