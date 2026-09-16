#!/usr/bin/env python3
"""
Skills Manager for the Complete Self System

Provides:
- Automatic skill/plugin generation using LLM
- Code validation for safety
- Test generation and execution
- Plugin management
- Self-testing capabilities
"""

import os
import json
import ast
import uuid
import importlib.util
import re
import textwrap
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path


# Modules that are blocked for security reasons
BLOCKED_MODULES = {
    "os",
    "subprocess",
    "socket",
    "shutil",
    "sys",
    "importlib",
    "ctypes",
    "pathlib",
    "pickle",
    "marshal",
    "requests",
    "urllib",
    "webbrowser",
    "threading",
    "multiprocessing",
    "asyncio",
    "signal",
    "tempfile",
    "builtins",
    "__builtins__",
    "eval",
    "exec",
    "compile",
}

# Blocked function calls
BLOCKED_CALLS = {
    "eval",
    "exec",
    "compile",
    "open",
    "input",
    "__import__",
    "globals",
    "locals",
    "vars",
    "breakpoint",
    "help",
    "dir",
    "getattr",
    "setattr",
    "delattr",
}

# Blocked attributes
BLOCKED_ATTRS = {
    "__class__",
    "__bases__",
    "__subclasses__",
    "__mro__",
    "__code__",
    "__globals__",
    "__builtins__",
    "__import__",
}


class SkillsManager:
    """
    Manages AI-generated skills/plugins.
    
    Features:
    - Generate new skills from natural language descriptions
    - Validate skill code for safety
    - Generate and run tests for skills
    - Manage installed plugins
    - Self-testing capabilities
    """
    
    def __init__(self, plugin_dir: str = "plugins", skill_dir: str = "generated_skills",
                 test_dir: str = "tests", cfg: Optional[Dict[str, Any]] = None):
        """
        Initialize the SkillsManager.
        
        Args:
            plugin_dir: Directory for plugins
            skill_dir: Directory for generated skills
            test_dir: Directory for tests
            cfg: Configuration dictionary
        """
        self.plugin_dir = Path(plugin_dir)
        self.skill_dir = Path(skill_dir)
        self.test_dir = Path(test_dir)
        self.cfg = cfg or {}
        
        # Create directories if they don't exist
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        self.skill_dir.mkdir(parents=True, exist_ok=True)
        self.test_dir.mkdir(parents=True, exist_ok=True)
        
        # Load plugins
        self.plugins: Dict[str, Any] = {}
        self.load_plugins()
    
    def load_plugins(self) -> None:
        """Load all plugins from the plugin directory."""
        self.plugins = {}
        
        for plugin_file in self.plugin_dir.glob("*.py"):
            try:
                name = plugin_file.stem
                spec = importlib.util.spec_from_file_location(name, str(plugin_file))
                if spec is None:
                    continue
                    
                module = importlib.util.module_from_spec(spec)
                if module is None:
                    continue
                    
                spec.loader.exec_module(module)
                
                if hasattr(module, "execute"):
                    self.plugins[name] = {
                        "module": module,
                        "execute": module.execute,
                        "path": str(plugin_file)
                    }
            except Exception as e:
                print(f"[Skills] Error loading plugin {plugin_file.name}: {e}")
    
    def list_plugins(self) -> List[str]:
        """List all loaded plugins."""
        return sorted(self.plugins.keys())
    
    def run_plugin(self, name: str, args: Any = None) -> Dict[str, Any]:
        """
        Run a plugin by name.
        
        Args:
            name: Name of the plugin
            args: Arguments to pass to the plugin
            
        Returns:
            Dictionary with result or error
        """
        if name not in self.plugins:
            return {
                "success": False,
                "error": f"Plugin '{name}' not found",
                "available": self.list_plugins()
            }
        
        try:
            result = self.plugins[name]["execute"](args)
            return {"success": True, "result": result, "plugin": name}
        except Exception as e:
            return {"success": False, "error": str(e), "plugin": name}
    
    def generate_skill_code(self, name: str, description: str, 
                           system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate Python code for a new skill using LLM.
        
        Args:
            name: Name of the skill
            description: Description of what the skill should do
            system_prompt: Optional system prompt for the LLM
            
        Returns:
            Dictionary with generated code or error
        """
        # Check if we have LLM access
        if "simple_llm_reply" not in self.cfg:
            return {
                "success": False,
                "error": "LLM not configured. Add simple_llm_reply to cfg."
            }
        
        prompt = f"""
Write a Python plugin for an AI agent.

Requirements:
- Return ONLY Python code (no explanations, no markdown)
- Define exactly this function: def execute(args): ...
- The plugin name is: {name}
- Plugin description: {description}
- Keep it simple and focused
- Do NOT use dangerous imports (os, subprocess, socket, etc.)
- Do NOT use filesystem access
- Do NOT use network calls
- Use type hints if possible
- Handle errors gracefully
- Return meaningful results

Example format:
```python
def execute(args):
    # Your code here
    return f"Result: {{args}}"
```

Plugin code:
"""
        
        messages = [
            {
                "role": "system",
                "content": system_prompt or (
                    "You are a careful Python code generator. "
                    "Return ONLY valid Python code. "
                    "Never include explanations or markdown."
                )
            },
            {"role": "user", "content": prompt}
        ]
        
        try:
            reply = self.cfg["simple_llm_reply"](messages)
            
            # Extract code from response
            code = self._extract_code(reply)
            
            if not code:
                return {
                    "success": False,
                    "error": "No valid Python code generated",
                    "raw_response": reply
                }
            
            return {
                "success": True,
                "code": code,
                "name": name,
                "description": description
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _extract_code(self, text: str) -> str:
        """Extract Python code from text."""
        text = str(text).strip()
        
        # Try to find code between ```python ``` markers
        match = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Try to find code between ``` markers
        match = re.search(r"```(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # If no markers, return the whole text (if it looks like code)
        if text.startswith("def ") or text.startswith("class ") or "import " in text:
            return text
        
        return ""
    
    def validate_skill_code(self, code: str, strict: bool = True) -> Tuple[bool, List[str]]:
        """
        Validate plugin code for safety.
        
        Args:
            code: Python code to validate
            strict: Whether to use strict validation
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues: List[str] = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, [f"Syntax error: {e}"]
        
        has_execute = False
        
        for node in ast.walk(tree):
            # Check for execute function
            if isinstance(node, ast.FunctionDef) and node.name == "execute":
                has_execute = True
            
            # Check imports
            if strict and isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in BLOCKED_MODULES:
                        issues.append(f"Blocked import: {alias.name}")
            
            if strict and isinstance(node, ast.ImportFrom):
                module = node.module or ""
                root = module.split(".")[0]
                if root in BLOCKED_MODULES:
                    issues.append(f"Blocked import from: {module}")
            
            # Check function calls
            if strict and isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in BLOCKED_CALLS:
                        issues.append(f"Blocked call: {node.func.id}")
                elif isinstance(node.func, ast.Attribute):
                    attr_name = node.func.attr
                    if attr_name in BLOCKED_ATTRS:
                        issues.append(f"Blocked attribute access: {attr_name}")
            
            # Check attribute access
            if strict and isinstance(node, ast.Attribute):
                if node.attr in BLOCKED_ATTRS:
                    issues.append(f"Blocked attribute: {node.attr}")
        
        if not has_execute:
            issues.append("Missing required function: execute(args)")
        
        return len(issues) == 0, issues
    
    def generate_test_code(self, name: str, plugin_code: str,
                           system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate test code for a plugin using LLM.
        
        Args:
            name: Name of the plugin
            plugin_code: The plugin code to test
            system_prompt: Optional system prompt for the LLM
            
        Returns:
            Dictionary with generated test code or error
        """
        if "simple_llm_reply" not in self.cfg:
            return {
                "success": False,
                "error": "LLM not configured. Add simple_llm_reply to cfg."
            }
        
        prompt = f"""
Write Python test code for this plugin.

Plugin name: {name}

Plugin code:
{plugin_code}

Requirements:
- Return ONLY Python code (no explanations, no markdown)
- Define functions starting with test_
- Import nothing (assume execute() is available)
- Use simple assert statements
- Test edge cases
- Keep tests focused and practical

Example format:
```python
def test_basic():
    result = execute("test")
    assert result == "expected"

def test_edge_case():
    result = execute("")
    assert result is not None
```

Test code:
"""
        
        messages = [
            {
                "role": "system",
                "content": system_prompt or (
                    "You are a careful test code generator. "
                    "Return ONLY valid Python test code."
                )
            },
            {"role": "user", "content": prompt}
        ]
        
        try:
            reply = self.cfg["simple_llm_reply"](messages)
            code = self._extract_code(reply)
            
            if not code:
                return {
                    "success": False,
                    "error": "No valid test code generated",
                    "raw_response": reply
                }
            
            return {"success": True, "code": code}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def run_test_code(self, plugin_code: str, test_code: str) -> Dict[str, Any]:
        """
        Run test code against plugin code.
        
        Args:
            plugin_code: The plugin code to test
            test_code: The test code to run
            
        Returns:
            Dictionary with test results
        """
        namespace: Dict[str, Any] = {}
        
        try:
            # Execute plugin code
            exec(plugin_code, namespace)
        except Exception as e:
            return {
                "success": False,
                "error": f"Plugin code failed: {e}",
                "tests_run": 0,
                "passed": 0,
                "failed": 0
            }
        
        try:
            # Execute test code
            exec(test_code, namespace)
        except Exception as e:
            return {
                "success": False,
                "error": f"Test code failed: {e}",
                "tests_run": 0,
                "passed": 0,
                "failed": 0
            }
        
        # Run all test_* functions
        tests_run = 0
        passed = 0
        failed = 0
        failures: List[Dict[str, Any]] = []
        
        for name, obj in list(namespace.items()):
            if name.startswith("test_") and callable(obj):
                try:
                    obj()
                    passed += 1
                    tests_run += 1
                except AssertionError as e:
                    failed += 1
                    tests_run += 1
                    failures.append({"test": name, "error": str(e)})
                except Exception as e:
                    failed += 1
                    tests_run += 1
                    failures.append({"test": name, "error": str(e)})
        
        if tests_run == 0:
            return {
                "success": False,
                "error": "No test_* functions found",
                "tests_run": 0,
                "passed": 0,
                "failed": 0
            }
        
        return {
            "success": True,
            "tests_run": tests_run,
            "passed": passed,
            "failed": failed,
            "failures": failures
        }
    
    def create_skill(self, name: str, description: str, 
                     auto_install: bool = False,
                     system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new skill from a description.
        
        Args:
            name: Name of the skill
            description: Description of the skill
            auto_install: Whether to automatically install
            system_prompt: Optional system prompt for LLM
            
        Returns:
            Dictionary with creation result
        """
        # Generate code
        gen_result = self.generate_skill_code(name, description, system_prompt)
        if not gen_result["success"]:
            return gen_result
        
        code = gen_result["code"]
        
        # Validate code
        is_valid, issues = self.validate_skill_code(code, strict=True)
        if not is_valid:
            return {
                "success": False,
                "error": "Validation failed",
                "issues": issues,
                "code": code
            }
        
        # Generate tests
        test_result = self.generate_test_code(name, code, system_prompt)
        if not test_result["success"]:
            return {
                "success": False,
                "error": "Failed to generate tests",
                "code": code,
                "test_error": test_result.get("error")
            }
        
        test_code = test_result["code"]
        
        # Run tests
        test_run = self.run_test_code(code, test_code)
        if not test_run["success"]:
            return {
                "success": False,
                "error": "Tests failed",
                "code": code,
                "test_code": test_code,
                "test_results": test_run
            }
        
        # If tests passed or auto_install is True
        if auto_install or test_run["passed"] > 0:
            # Save plugin
            plugin_path = self.save_plugin(name, code)
            
            # Save test
            test_path = self.test_dir / f"test_{name}.py"
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(test_code)
            
            # Reload plugins
            self.load_plugins()
            
            return {
                "success": True,
                "message": "Skill created and installed",
                "name": name,
                "plugin_path": str(plugin_path),
                "test_path": str(test_path),
                "test_results": test_run,
                "code": code,
                "test_code": test_code
            }
        else:
            return {
                "success": False,
                "error": "Tests failed, skill not installed",
                "code": code,
                "test_code": test_code,
                "test_results": test_run
            }
    
    def save_plugin(self, name: str, code: str) -> Path:
        """
        Save a plugin to the plugin directory.
        
        Args:
            name: Name of the plugin
            code: Plugin code
            
        Returns:
            Path to the saved plugin file
        """
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
        if not safe_name:
            raise ValueError("Invalid plugin name")
        
        path = self.plugin_dir / f"{safe_name}.py"
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        
        return path
    
    def delete_plugin(self, name: str) -> Dict[str, Any]:
        """
        Delete a plugin.
        
        Args:
            name: Name of the plugin to delete
            
        Returns:
            Dictionary with deletion result
        """
        if name not in self.plugins:
            return {"success": False, "error": f"Plugin '{name}' not found"}
        
        try:
            path = self.plugin_dir / f"{name}.py"
            if path.exists():
                path.unlink()
            
            # Remove from plugins dict
            if name in self.plugins:
                del self.plugins[name]
            
            return {"success": True, "message": f"Plugin '{name}' deleted"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_plugin_code(self, name: str) -> Dict[str, Any]:
        """
        Get the code of a plugin.
        
        Args:
            name: Name of the plugin
            
        Returns:
            Dictionary with plugin code or error
        """
        if name not in self.plugins:
            return {"success": False, "error": f"Plugin '{name}' not found"}
        
        try:
            path = self.plugins[name]["path"]
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            
            return {"success": True, "name": name, "code": code, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def self_test_plugin(self, name: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate and run tests for an existing plugin.
        
        Args:
            name: Name of the plugin to test
            system_prompt: Optional system prompt for LLM
            
        Returns:
            Dictionary with test results
        """
        if name not in self.plugins:
            return {"success": False, "error": f"Plugin '{name}' not found"}
        
        # Get plugin code
        plugin_result = self.get_plugin_code(name)
        if not plugin_result["success"]:
            return plugin_result
        
        plugin_code = plugin_result["code"]
        
        # Generate tests
        test_result = self.generate_test_code(name, plugin_code, system_prompt)
        if not test_result["success"]:
            return test_result
        
        test_code = test_result["code"]
        
        # Run tests
        test_run = self.run_test_code(plugin_code, test_code)
        
        # Save test file
        test_path = self.test_dir / f"test_{name}.py"
        with open(test_path, "w", encoding="utf-8") as f:
            f.write(test_code)
        
        return {
            "success": True,
            "plugin": name,
            "test_code": test_code,
            "test_path": str(test_path),
            "results": test_run
        }
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """List all generated skills."""
        skills = []
        
        for skill_file in self.skill_dir.glob("*.py"):
            try:
                with open(skill_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                skills.append({
                    "name": skill_file.stem,
                    "path": str(skill_file),
                    "size": skill_file.stat().st_size
                })
            except Exception:
                pass
        
        return skills


def create_skills_manager(plugin_dir: str = "plugins", skill_dir: str = "generated_skills",
                         test_dir: str = "tests", cfg: Optional[Dict[str, Any]] = None) -> SkillsManager:
    """
    Factory function to create a SkillsManager instance.
    
    Args:
        plugin_dir: Directory for plugins
        skill_dir: Directory for generated skills
        test_dir: Directory for tests
        cfg: Configuration dictionary
        
    Returns:
        SkillsManager instance
    """
    return SkillsManager(plugin_dir, skill_dir, test_dir, cfg)
