#!/usr/bin/env python3
"""
Plugin Manager for the Complete Self System

Provides:
- Plugin loading and management
- Dynamic plugin reloading
- Plugin execution
- Sample plugin creation
"""

import os
import re
import importlib.util
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable


class PluginManager:
    """
    Manages plugins for the Complete Self System.
    
    Features:
    - Load plugins from directory
    - Execute plugins by name
    - Reload plugins dynamically
    - Create sample plugins
    - List available plugins
    """
    
    def __init__(self, plugin_dir: str = "plugins"):
        """
        Initialize the PluginManager.
        
        Args:
            plugin_dir: Directory to load plugins from
        """
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, Dict[str, Any]] = {}
        
        # Create directory if it doesn't exist
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample plugin if none exists
        self._create_sample_plugin()
        
        # Load plugins
        self.load()
    
    def _create_sample_plugin(self) -> None:
        """Create a sample plugin if none exists."""
        sample_path = self.plugin_dir / "sample_tool.py"
        
        if not sample_path.exists():
            code = '''#!/usr/bin/env python3
"""
Sample Plugin for Complete Self System

This is a sample plugin that demonstrates the plugin interface.
All plugins must define an `execute(args)` function.

Usage:
    /run sample_tool hello world
    
Result:
    Sample plugin received: hello world
"""


def execute(args):
    """
    Execute the plugin with given arguments.
    
    Args:
        args: Plugin arguments (can be string, dict, or any type)
        
    Returns:
        Result of the plugin execution
    """
    # If args is a string, just return it with prefix
    if isinstance(args, str):
        return f"Sample plugin received: {args}"
    
    # If args is a dict, handle different actions
    if isinstance(args, dict):
        action = args.get("action", "echo")
        text = args.get("text", "")
        
        if action == "reverse":
            return text[::-1]
        elif action == "uppercase":
            return text.upper()
        elif action == "lowercase":
            return text.lower()
        elif action == "count_words":
            return str(len(text.split()))
        elif action == "count_chars":
            return str(len(text))
        else:
            return f"Sample plugin received: {args}"
    
    # For any other type, convert to string
    return f"Sample plugin received: {args}"
'''
            
            with open(sample_path, "w", encoding="utf-8") as f:
                f.write(code)
    
    def load(self) -> None:
        """Load all plugins from the plugin directory."""
        self.plugins = {}
        
        for plugin_file in self.plugin_dir.glob("*.py"):
            try:
                name = plugin_file.stem
                
                # Skip __init__.py
                if name == "__init__":
                    continue
                
                # Load the module
                spec = importlib.util.spec_from_file_location(name, str(plugin_file))
                if spec is None:
                    print(f"[Plugin] Could not create spec for {plugin_file.name}")
                    continue
                
                module = importlib.util.module_from_spec(spec)
                if module is None:
                    print(f"[Plugin] Could not create module for {plugin_file.name}")
                    continue
                
                spec.loader.exec_module(module)
                
                # Check for execute function
                if hasattr(module, "execute") and callable(module.execute):
                    self.plugins[name] = {
                        "module": module,
                        "execute": module.execute,
                        "path": str(plugin_file),
                        "name": name
                    }
                    print(f"[Plugin] Loaded: {name}")
                else:
                    print(f"[Plugin] No execute() function in {plugin_file.name}")
                    
            except Exception as e:
                print(f"[Plugin] Error loading {plugin_file.name}: {e}")
    
    def list_plugins(self) -> List[str]:
        """
        List all loaded plugins.
        
        Returns:
            List of plugin names
        """
        return sorted(self.plugins.keys())
    
    def get_plugin(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a plugin by name.
        
        Args:
            name: Name of the plugin
            
        Returns:
            Plugin dictionary or None
        """
        return self.plugins.get(name)
    
    def run(self, name: str, args: Any = None) -> str:
        """
        Run a plugin by name.
        
        Args:
            name: Name of the plugin
            args: Arguments to pass to the plugin
            
        Returns:
            Result of the plugin execution
        """
        name = str(name or "").strip()
        
        if name not in self.plugins:
            available = ", ".join(self.list_plugins())
            return f"Plugin '{name}' not found. Available plugins: {available}"
        
        try:
            result = self.plugins[name]["execute"](args)
            return str(result)
        except Exception as e:
            return f"Plugin error in {name}: {e}"
    
    def save_plugin(self, name: str, code: str) -> Path:
        """
        Save a plugin to the plugin directory.
        
        Args:
            name: Name of the plugin
            code: Plugin code
            
        Returns:
            Path to the saved plugin file
        """
        # Sanitize name
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
        if not safe_name:
            raise ValueError("Invalid plugin name")
        
        path = self.plugin_dir / f"{safe_name}.py"
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        
        # Reload plugins
        self.load()
        
        return path
    
    def delete_plugin(self, name: str) -> bool:
        """
        Delete a plugin.
        
        Args:
            name: Name of the plugin to delete
            
        Returns:
            True if deleted, False otherwise
        """
        if name not in self.plugins:
            return False
        
        try:
            path = self.plugin_dir / f"{name}.py"
            if path.exists():
                path.unlink()
            
            # Remove from plugins dict
            del self.plugins[name]
            
            return True
        except Exception:
            return False
    
    def get_plugin_code(self, name: str) -> Optional[str]:
        """
        Get the code of a plugin.
        
        Args:
            name: Name of the plugin
            
        Returns:
            Plugin code or None
        """
        if name not in self.plugins:
            return None
        
        path = self.plugins[name]["path"]
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None
    
    def reload(self) -> None:
        """Reload all plugins."""
        self.load()


# Singleton instance
plugins = PluginManager()


def get_plugin_manager() -> PluginManager:
    """Get the singleton plugin manager instance."""
    return plugins
