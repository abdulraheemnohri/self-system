#!/usr/bin/env python3
"""
Code Execution Tools for Complete Self System

Provides safe code execution:
- Sandboxed Python evaluation
- Syntax checking
- Code analysis
- Safe imports
"""

import ast
import json
import operator
import math
import time
import uuid
import hashlib
from typing import Dict, Any, List, Optional


# Safe built-in functions
SAFE_BUILTINS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "dict": dict,
    "dir": dir,
    "divmod": divmod,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "frozenset": frozenset,
    "getattr": getattr,
    "hasattr": hasattr,
    "hash": hash,
    "hex": hex,
    "int": int,
    "isinstance": isinstance,
    "issubclass": issubclass,
    "iter": iter,
    "len": len,
    "list": list,
    "map": map,
    "max": max,
    "min": min,
    "next": next,
    "oct": oct,
    "ord": ord,
    "pow": pow,
    "print": print,
    "range": range,
    "repr": repr,
    "reversed": reversed,
    "round": round,
    "set": set,
    "slice": slice,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "type": type,
    "zip": zip,
}

# Safe math functions
SAFE_MATH = {
    "pi": math.pi,
    "e": math.e,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "atan2": math.atan2,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "asinh": math.asinh,
    "acosh": math.acosh,
    "atanh": math.atanh,
    "sqrt": math.sqrt,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "expm1": math.expm1,
    "pow": math.pow,
    "fabs": math.fabs,
    "floor": math.floor,
    "ceil": math.ceil,
    "trunc": math.trunc,
    "fmod": math.fmod,
    "fsum": math.fsum,
    "gcd": math.gcd,
    "lcm": math.lcm,
    "comb": math.comb,
    "perm": math.perm,
    "factorial": math.factorial,
    "gamma": math.gamma,
    "erf": math.erf,
    "erfc": math.erfc,
    "degrees": math.degrees,
    "radians": math.radians,
    "hypot": math.hypot,
    "isnan": math.isnan,
    "isinf": math.isinf,
    "isfinite": math.isfinite,
    "copysign": math.copysign,
}

# Safe binary operators
SAFE_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.MatMult: operator.matmul,
}

# Safe unary operators
SAFE_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
    ast.Invert: operator.invert,
}

# Safe comparison operators
SAFE_COMPOPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Is: operator.is_,
    ast.IsNot: operator.is_not,
    ast.In: operator.contains,
    ast.NotIn: lambda a, b: not operator.contains(b, a),
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
    "__dict__",
    "__module__",
    "__reduce__",
    "__reduce_ex__",
    "__getstate__",
    "__setstate__",
}

# Blocked modules
BLOCKED_MODULES = {
    "os",
    "subprocess",
    "sys",
    "importlib",
    "builtins",
    "__builtins__",
    "socket",
    "shutil",
    "pickle",
    "marshal",
    "ctypes",
    "multiprocessing",
    "threading",
    "asyncio",
    "signal",
    "tempfile",
    "pathlib",
    "webbrowser",
    "urllib",
    "http",
    "ftplib",
    "smtplib",
    "poplib",
    "imaplib",
    "socketserver",
    "xmlrpc",
    "jsonrpc",
}


class CodeTools:
    """
    Safe code execution tools for the Complete Self System.
    
    Features:
    - Sandboxed Python evaluation
    - Syntax checking
    - Code analysis
    - Safe imports
    """
    
    def __init__(self, timeout: int = 5, max_complexity: int = 100):
        """
        Initialize CodeTools.
        
        Args:
            timeout: Maximum execution time in seconds
            max_complexity: Maximum AST complexity allowed
        """
        self.timeout = timeout
        self.max_complexity = max_complexity
    
    def _check_complexity(self, tree: ast.AST) -> int:
        """Calculate AST complexity."""
        complexity = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                complexity += 1
            elif isinstance(node, ast.Name):
                complexity += 0.5
            elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                complexity += 5
            elif isinstance(node, ast.For) or isinstance(node, ast.While):
                complexity += 3
            elif isinstance(node, ast.If):
                complexity += 2
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.ClassDef):
                complexity += 10
        
        return int(complexity)
    
    def check_syntax(self, code: str) -> Dict[str, Any]:
        """
        Check Python syntax.
        
        Args:
            code: Python code to check
            
        Returns:
            Dictionary with syntax check result
        """
        try:
            tree = ast.parse(str(code))
            complexity = self._check_complexity(tree)
            
            return {
                "success": True,
                "valid": True,
                "complexity": complexity,
                "max_complexity": self.max_complexity,
                "too_complex": complexity > self.max_complexity
            }
        except SyntaxError as e:
            return {
                "success": True,
                "valid": False,
                "error": str(e),
                "line": e.lineno,
                "offset": e.offset
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def validate_code(self, code: str) -> Dict[str, Any]:
        """
        Validate code for safety.
        
        Args:
            code: Python code to validate
            
        Returns:
            Dictionary with validation result
        """
        try:
            tree = ast.parse(str(code))
        except SyntaxError as e:
            return {"success": False, "error": f"Syntax error: {e}"}
        
        issues = []
        
        # Check for imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    if module in BLOCKED_MODULES:
                        issues.append(f"Blocked import: {alias.name}")
            
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
                root = module.split(".")[0]
                if root in BLOCKED_MODULES:
                    issues.append(f"Blocked import from: {module}")
            
            # Check for attribute access on blocked attributes
            if isinstance(node, ast.Attribute):
                if node.attr in BLOCKED_ATTRS:
                    issues.append(f"Blocked attribute: {node.attr}")
        
        # Check complexity
        complexity = self._check_complexity(tree)
        if complexity > self.max_complexity:
            issues.append(f"Code too complex: {complexity} > {self.max_complexity}")
        
        return {
            "success": len(issues) == 0,
            "issues": issues,
            "complexity": complexity
        }
    
    def execute_safe(self, code: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Execute Python code in a sandbox.
        
        Args:
            code: Python code to execute
            timeout: Maximum execution time
            
        Returns:
            Dictionary with execution result
        """
        # Validate code first
        validation = self.validate_code(code)
        if not validation.get("success"):
            return {
                "success": False,
                "error": "Validation failed",
                "issues": validation.get("issues", [])
            }
        
        # Check syntax
        syntax_check = self.check_syntax(code)
        if not syntax_check.get("valid"):
            return {
                "success": False,
                "error": "Syntax error",
                "details": syntax_check.get("error", "")
            }
        
        # Prepare safe globals
        safe_globals = {
            "__builtins__": SAFE_BUILTINS,
            "math": SAFE_MATH,
            "time": {"time": time.time, "sleep": time.sleep},
            "uuid": {"uuid4": uuid.uuid4},
            "hashlib": {"sha256": hashlib.sha256, "md5": hashlib.md5},
            "json": {"dumps": json.dumps, "loads": json.loads},
            "len": len,
            "range": range,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "print": print,
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "round": round,
        }
        
        try:
            # Compile the code
            compiled = compile(str(code), "<string>", "eval")
            
            # Execute with timeout
            import signal
            
            def handler(signum, frame):
                raise TimeoutError("Code execution timed out")
            
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(timeout or self.timeout)
            
            result = eval(compiled, safe_globals, {})
            
            signal.alarm(0)
            
            return {
                "success": True,
                "result": result,
                "type": type(result).__name__
            }
        except TimeoutError:
            return {"success": False, "error": "Execution timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            signal.alarm(0)
    
    def execute_expression(self, expression: str) -> Dict[str, Any]:
        """
        Execute a single expression safely.
        
        Args:
            expression: Expression to evaluate
            
        Returns:
            Dictionary with result
        """
        return self.execute_safe(expression)
    
    def analyze_code(self, code: str) -> Dict[str, Any]:
        """
        Analyze code structure.
        
        Args:
            code: Python code to analyze
            
        Returns:
            Dictionary with code analysis
        """
        try:
            tree = ast.parse(str(code))
        except SyntaxError as e:
            return {"success": False, "error": f"Syntax error: {e}"}
        
        analysis = {
            "functions": [],
            "classes": [],
            "imports": [],
            "variables": [],
            "complexity": 0,
            "lines": len(code.split("\n")),
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                analysis["functions"].append({
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "line": node.lineno
                })
            elif isinstance(node, ast.ClassDef):
                analysis["classes"].append({
                    "name": node.name,
                    "line": node.lineno
                })
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    analysis["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    analysis["imports"].append(f"{module}.{alias.name}")
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        analysis["variables"].append(target.id)
        
        analysis["complexity"] = self._check_complexity(tree)
        analysis["success"] = True
        
        return analysis


# Global instance
code_tools = CodeTools()


def create_code_tools(timeout: int = 5, max_complexity: int = 100) -> CodeTools:
    """
    Create a CodeTools instance.
    
    Args:
        timeout: Maximum execution time
        max_complexity: Maximum AST complexity
        
    Returns:
        CodeTools instance
    """
    return CodeTools(timeout, max_complexity)
