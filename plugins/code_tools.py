"""
Code Tools Plugin for Complete Self System

Provides code analysis, generation, and manipulation utilities
"""

import json
import ast
import re
from typing import Dict, Any, List, Optional, Tuple


def analyze_code(args: Dict[str, Any]) -> str:
    """Analyze Python code structure"""
    code = args.get('code', '')
    
    if not code:
        return "No code provided"
    
    try:
        tree = ast.parse(code)
        analysis = {
            'functions': [],
            'classes': [],
            'imports': [],
            'variables': [],
            'line_count': len(code.splitlines()),
            'char_count': len(code)
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                analysis['functions'].append({
                    'name': node.name,
                    'line': node.lineno,
                    'args': [arg.arg for arg in node.args.args]
                })
            elif isinstance(node, ast.ClassDef):
                analysis['classes'].append({
                    'name': node.name,
                    'line': node.lineno,
                    'methods': [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                })
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    analysis['imports'].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                analysis['imports'].append(f"{node.module}.{','.join(a.name for a in node.names)}")
        
        return json.dumps(analysis, indent=2)
    except SyntaxError as e:
        return f"Syntax error: {str(e)}"
    except Exception as e:
        return f"Analysis failed: {str(e)}"


def format_code(args: Dict[str, Any]) -> str:
    """Format Python code using autopep8 or black"""
    code = args.get('code', '')
    formatter = args.get('formatter', 'autopep8')
    
    if not code:
        return "No code provided"
    
    try:
        if formatter == 'black':
            try:
                import black
                mode = black.FileMode()
                formatted = black.format_str(code, mode=mode)
                return formatted
            except ImportError:
                return "Black not installed. Install with: pip install black"
        else:
            # autopep8
            try:
                import autopep8
                formatted = autopep8.fix_code(code)
                return formatted
            except ImportError:
                return "autopep8 not installed. Install with: pip install autopep8"
    except Exception as e:
        return f"Formatting failed: {str(e)}"


def lint_code(args: Dict[str, Any]) -> str:
    """Lint Python code for errors and style issues"""
    code = args.get('code', '')
    
    if not code:
        return "No code provided"
    
    try:
        tree = ast.parse(code)
        issues = []
        
        # Check for common issues
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == 'print':
                issues.append({'line': node.lineno, 'type': 'warning', 'message': 'Consider using logging instead of print'})
            elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                # Check for bare except
                if (isinstance(node.value.func, ast.Name) and 
                    node.value.func.id == 'except'):
                    issues.append({'line': node.lineno, 'type': 'error', 'message': 'Bare except clause found'})
        
        # Try to compile
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            issues.append({'line': e.lineno, 'type': 'error', 'message': str(e.msg)})
        
        return json.dumps(issues, indent=2)
    except SyntaxError as e:
        return json.dumps([{'line': e.lineno, 'type': 'error', 'message': str(e.msg)}], indent=2)
    except Exception as e:
        return f"Linting failed: {str(e)}"


def execute_code(args: Dict[str, Any]) -> str:
    """Execute Python code in a sandboxed environment"""
    code = args.get('code', '')
    timeout = int(args.get('timeout', 5))
    
    if not code:
        return "No code provided"
    
    try:
        # Create a restricted namespace
        safe_globals = {
            '__builtins__': {
                'print': print,
                'range': range,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'list': list,
                'dict': dict,
                'tuple': tuple,
                'set': set,
                'min': min,
                'max': max,
                'sum': sum,
                'abs': abs,
                'round': round,
                'sorted': sorted,
                'reversed': reversed,
                'enumerate': enumerate,
                'zip': zip,
                'filter': filter,
                'map': map,
                'bool': bool,
                'type': type,
                'isinstance': isinstance,
            }
        }
        
        # Set timeout
        import signal
        import sys
        
        class TimeoutError(Exception):
            pass
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Code execution timed out")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            exec(code, safe_globals)
            signal.alarm(0)
            return "Code executed successfully"
        except TimeoutError:
            signal.alarm(0)
            return "Code execution timed out"
        except Exception as e:
            signal.alarm(0)
            return f"Code execution failed: {str(e)}"
    except Exception as e:
        return f"Execution failed: {str(e)}"


def generate_docstring(args: Dict[str, Any]) -> str:
    """Generate a docstring for a function"""
    function_name = args.get('name', '')
    description = args.get('description', '')
    params = args.get('params', {})
    returns = args.get('returns', '')
    
    if not function_name:
        return "No function name provided"
    
    docstring = f'"""\n{description}\n\nArgs:'
    for param, param_desc in params.items():
        docstring += f'\n    {param}: {param_desc}'
    
    if returns:
        docstring += f'\n\nReturns:\n    {returns}'
    
    docstring += '\n"""'
    return docstring


def refactor_variable_names(args: Dict[str, Any]) -> str:
    """Refactor variable names to follow PEP 8 conventions"""
    code = args.get('code', '')
    
    if not code:
        return "No code provided"
    
    try:
        # Simple refactoring - convert camelCase to snake_case
        def camel_to_snake(name):
            pattern = re.compile(r'(?<!^)(?=[A-Z])')
            return pattern.sub('_', name).lower()
        
        tree = ast.parse(code)
        
        class NameTransformer(ast.NodeTransformer):
            def visit_Name(self, node):
                if isinstance(node.ctx, ast.Store):
                    # This is a variable assignment
                    if re.match(r'[a-z][A-Z]', node.id):
                        node.id = camel_to_snake(node.id)
                return node
        
        transformed_tree = NameTransformer().visit(tree)
        ast.fix_missing_locations(transformed_tree)
        
        return ast.unparse(transformed_tree)
    except Exception as e:
        return f"Refactoring failed: {str(e)}"


def count_code_metrics(args: Dict[str, Any]) -> str:
    """Count various code metrics"""
    code = args.get('code', '')
    
    if not code:
        return "No code provided"
    
    try:
        tree = ast.parse(code)
        
        metrics = {
            'lines': len(code.splitlines()),
            'functions': 0,
            'classes': 0,
            'imports': 0,
            'comments': len(re.findall(r'#.*', code)),
            'docstrings': 0,
            'complexity': 0
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics['functions'] += 1
                if ast.get_docstring(node):
                    metrics['docstrings'] += 1
            elif isinstance(node, ast.ClassDef):
                metrics['classes'] += 1
                if ast.get_docstring(node):
                    metrics['docstrings'] += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                metrics['imports'] += 1
        
        return json.dumps(metrics, indent=2)
    except Exception as e:
        return f"Metrics calculation failed: {str(e)}"


PLUGIN_NAME = "code_tools"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Code analysis, generation, and manipulation utilities"

AVAILABLE_FUNCTIONS = {
    'analyze_code': {
        'description': 'Analyze Python code structure',
        'parameters': {
            'code': {'type': 'string', 'required': True, 'description': 'Python code to analyze'}
        },
        'handler': analyze_code
    },
    'format_code': {
        'description': 'Format Python code',
        'parameters': {
            'code': {'type': 'string', 'required': True, 'description': 'Python code to format'},
            'formatter': {'type': 'string', 'required': False, 'description': 'Formatter to use (autopep8 or black)', 'default': 'autopep8'}
        },
        'handler': format_code
    },
    'lint_code': {
        'description': 'Lint Python code for errors and style issues',
        'parameters': {
            'code': {'type': 'string', 'required': True, 'description': 'Python code to lint'}
        },
        'handler': lint_code
    },
    'execute_code': {
        'description': 'Execute Python code in a sandbox',
        'parameters': {
            'code': {'type': 'string', 'required': True, 'description': 'Python code to execute'},
            'timeout': {'type': 'integer', 'required': False, 'description': 'Timeout in seconds (default: 5)', 'default': 5}
        },
        'handler': execute_code
    },
    'generate_docstring': {
        'description': 'Generate a docstring for a function',
        'parameters': {
            'name': {'type': 'string', 'required': True, 'description': 'Function name'},
            'description': {'type': 'string', 'required': False, 'description': 'Function description', 'default': ''},
            'params': {'type': 'object', 'required': False, 'description': 'Parameter descriptions', 'default': {}},
            'returns': {'type': 'string', 'required': False, 'description': 'Return value description', 'default': ''}
        },
        'handler': generate_docstring
    },
    'refactor_variable_names': {
        'description': 'Refactor variable names to snake_case',
        'parameters': {
            'code': {'type': 'string', 'required': True, 'description': 'Python code to refactor'}
        },
        'handler': refactor_variable_names
    },
    'count_code_metrics': {
        'description': 'Count various code metrics',
        'parameters': {
            'code': {'type': 'string', 'required': True, 'description': 'Python code to analyze'}
        },
        'handler': count_code_metrics
    }
}


def get_plugin_info() -> Dict[str, Any]:
    return {'name': PLUGIN_NAME, 'version': PLUGIN_VERSION, 'description': PLUGIN_DESCRIPTION, 'functions': AVAILABLE_FUNCTIONS}
