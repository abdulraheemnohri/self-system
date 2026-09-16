"""
Configuration Manager for Complete Self System
کنفیگریشن مینیجر برائے خود کار نظام
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration manager with YAML and environment variable support"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self._load_config()
        self._load_env_vars()
    
    def _load_config(self) -> None:
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load config file: {e}")
            self._config = {}
    
    def _load_env_vars(self) -> None:
        env_mapping = {
            'API_KEY': 'provider.api_key',
            'BASE_URL': 'provider.base_url',
            'MODEL': 'provider.model',
            'EMBEDDING_MODEL': 'provider.embedding_model',
            'VECTOR_BACKEND': 'memory.vector_backend',
            'QDRANT_URL': 'memory.qdrant_url',
            'QDRANT_COLLECTION': 'memory.qdrant_collection',
            'AUTONOMOUS_MODE': 'safety.autonomous_mode',
            'AUTO_INSTALL_SKILLS': 'safety.auto_install_skills',
            'ALLOW_PLUGIN_TOOL': 'safety.allow_plugin_tool',
            'ALLOW_SKILL_TOOL': 'safety.allow_skill_tool',
            'VOICE_ENABLED': 'voice.enabled',
            'STT_ENGINE': 'voice.stt_engine',
            'TTS_ENGINE': 'voice.tts_engine',
            'BROWSER_HEADLESS': 'browser.headless',
            'BROWSER_TIMEOUT_MS': 'browser.timeout_ms',
        }
        
        for env_var, config_key in env_mapping.items():
            if env_var in os.environ:
                value = os.environ[env_var]
                if value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '').replace('-', '').isdigit():
                    value = float(value)
                keys = config_key.split('.')
                current = self._config
                for key in keys[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                current[keys[-1]] = value
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        keys = key.split('.')
        current = self._config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current
    
    def set(self, key: str, value: Any) -> None:
        keys = key.split('.')
        current = self._config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
        self._save_config()
    
    def _save_config(self) -> None:
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")
    
    def get_default_config(self) -> Dict[str, Any]:
        return {
            'system': {'name': 'Complete Self System', 'version': '1.0', 'mode': 'development'},
            'provider': {'base_url': 'http://localhost:11434/v1', 'api_key': '', 'model': 'llama3.1', 'embedding_model': 'nomic-embed-text', 'use_api_embeddings': True},
            'agent': {'agent_mode': True, 'enable_tool_calls': True, 'max_agent_steps': 10, 'context_turns': 16},
            'memory': {'vector_backend': 'sqlite', 'qdrant_url': 'http://localhost:6333', 'qdrant_collection': 'self_system'},
            'safety': {'autonomous_mode': False, 'auto_install_skills': False, 'allow_plugin_tool': False, 'allow_skill_tool': False, 'require_approval': ['browser_fill', 'browser_click', 'run_plugin', 'generate_skill', 'install_skill', 'file_write', 'shell'], 'disabled': ['shell']},
            'voice': {'enabled': False, 'stt_engine': 'faster-whisper', 'tts_engine': 'piper'},
            'browser': {'headless': True, 'timeout_ms': 30000},
            'scheduler': {'enabled': True, 'tasks': [{'name': 'memory_cleanup', 'action': 'maintenance', 'interval_seconds': 3600}, {'name': 'self_review', 'action': 'self_review', 'interval_seconds': 14400}, {'name': 'periodic_learning', 'action': 'periodic_learning', 'interval_seconds': 43200}, {'name': 'skill_proposal', 'action': 'skill_proposal', 'interval_seconds': 86400}]}
        }
    
    def reset_to_defaults(self) -> None:
        self._config = self.get_default_config()
        self._save_config()


config = Config()