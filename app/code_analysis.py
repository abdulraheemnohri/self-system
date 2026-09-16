"""
Code Analysis Skill for Complete Self System

Provides advanced code analysis including security, performance, and quality checks
"""

import ast
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from .llm import simple_llm_reply


class CodeAnalysisSkill:
    """Skill for analyzing code quality, security, and performance"""
    
    def __init__(self):
        self.name = "code_analysis"
        self.description = "Advanced code analysis including security, performance, and quality checks"
        self.version = "1.0.0"
    
    def analyze_security(self, code: str) -> Dict[str, Any]:
        """Analyze code for security vulnerabilities"""
        issues = []
        
        # Check for SQL injection
        sql_patterns = [
            r'\.execute\(.*\+.*\)',
            r'\.execute\(.*\%.*\)',
            r'\.execute\(.*f"[^"]*"',
            r"\.execute\(.*f'[^']*'"
        ]
        for pattern in sql_patterns:
            if re.search(pattern, code):
                issues.append({
                    'type': 'security',
                    'severity': 'high',
                    'issue': 'Potential SQL injection vulnerability',
                    'description': 'String formatting in SQL queries can lead to injection'
                })
        
        # Check for hardcoded secrets
        secret_patterns = [
            r"password\s*=\s*['\"][^'\"]*['\"]",
            r"api_key\s*=\s*['\"][^'\"]*['\"]",
            r"secret\s*=\s*['\"][^'\"]*['\"]",
            r"token\s*=\s*['\"][^'\"]*['\"]"
        ]
        for pattern in secret_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append({
                    'type': 'security',
                    'severity': 'critical',
                    'issue': 'Hardcoded secret detected',
                    'description': 'Secrets should be stored in environment variables'
                })
        
        # Check for eval usage
        if re.search(r'\beval\s*\(', code):
            issues.append({
                'type': 'security',
                'severity': 'critical',
                'issue': 'Use of eval() function',
                'description': 'eval() can execute arbitrary code'
            })
        
        # Check for pickle usage
        if re.search(r'\bpickle\s*\.', code):
            issues.append({
                'type': 'security',
                'severity': 'high',
                'issue': 'Use of pickle module',
                'description': 'Pickle can execute arbitrary code during deserialization'
            })
        
        # Check for shell injection
        shell_patterns = [
            r'\.system\s*\(',
            r'\.popen\s*\(',
            r'os\.system\s*\(',
            r'subprocess\.run\s*\('
        ]
        for pattern in shell_patterns:
            if re.search(pattern, code):
                issues.append({
                    'type': 'security',
                    'severity': 'high',
                    'issue': 'Potential shell injection',
                    'description': 'Shell commands should use proper escaping'
                })
        
        return {
            'security_issues': issues,
            'security_score': max(0, 100 - len(issues) * 10)
        }
    
    def analyze_performance(self, code: str) -> Dict[str, Any]:
        """Analyze code for performance issues"""
        issues = []
        
        try:
            tree = ast.parse(code)
            
            # Check for nested loops
            loop_depth = 0
            max_depth = 0
            for node in ast.walk(tree):
                if isinstance(node, (ast.For, ast.While)):
                    loop_depth += 1
                    max_depth = max(max_depth, loop_depth)
                elif not isinstance(node, (ast.For, ast.While)):
                    if loop_depth > 0:
                        loop_depth -= 1
            
            if max_depth > 3:
                issues.append({
                    'type': 'performance',
                    'severity': 'medium',
                    'issue': 'Deeply nested loops',
                    'description': f'Maximum nesting depth: {max_depth}'
                })
            
            # Check for inefficient operations
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['range', 'len']:
                            # Check if used in a loop
                            parent = next(n for n in ast.walk(tree) if isinstance(n, (ast.For, ast.While)) and n.target.id == node.func.id, None)
                            if parent:
                                issues.append({
                                    'type': 'performance',
                                    'severity': 'low',
                                    'issue': 'Potential inefficient loop',
                                    'description': f'Consider using more efficient iteration for {node.func.id}'
                                })
            
            # Count function calls
            call_count = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Call))
            if call_count > 100:
                issues.append({
                    'type': 'performance',
                    'severity': 'low',
                    'issue': 'High number of function calls',
                    'description': f'Total function calls: {call_count}'
                })
        except:
            pass
        
        return {
            'performance_issues': issues,
            'performance_score': max(0, 100 - len(issues) * 5)
        }
    
    def analyze_quality(self, code: str) -> Dict[str, Any]:
        """Analyze code for quality issues"""
        issues = []
        
        try:
            tree = ast.parse(code)
            
            # Check for function length
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Count lines in function
                    start_line = node.lineno
                    end_line = node.end_lineno or start_line
                    length = end_line - start_line + 1
                    
                    if length > 50:
                        issues.append({
                            'type': 'quality',
                            'severity': 'medium',
                            'issue': 'Long function',
                            'description': f'Function {node.name} is {length} lines long',
                            'location': f'Line {start_line}'
                        })
                    
                    # Check for docstring
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        issues.append({
                            'type': 'quality',
                            'severity': 'low',
                            'issue': 'Missing docstring',
                            'description': f'Function {node.name} has no docstring',
                            'location': f'Line {start_line}'
                        })
            
            # Check for class length
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                    if len(methods) > 20:
                        issues.append({
                            'type': 'quality',
                            'severity': 'medium',
                            'issue': 'Large class',
                            'description': f'Class {node.name} has {len(methods)} methods',
                            'location': f'Line {node.lineno}'
                        })
        except:
            pass
        
        return {
            'quality_issues': issues,
            'quality_score': max(0, 100 - len(issues) * 2)
        }
    
    def generate_improvements(self, code: str) -> str:
        """Generate suggestions for code improvement using LLM"""
        prompt = f"Analyze the following Python code and suggest improvements for:\n"
        prompt += "1. Security vulnerabilities\n"
        prompt += "2. Performance optimizations\n"
        prompt += "3. Code quality improvements\n"
        prompt += "4. Best practices\n\n"
        prompt += f"Code:\n{code[:4000]}\n\n"
        prompt += "Provide specific, actionable suggestions."
        
        messages = [
            {'role': 'system', 'content': 'You are a senior Python developer and code reviewer.'},
            {'role': 'user', 'content': prompt}
        ]
        
        return simple_llm_reply(messages, max_tokens=3000, temperature=0.3)
    
    def calculate_complexity(self, code: str) -> Dict[str, Any]:
        """Calculate code complexity metrics"""
        try:
            tree = ast.parse(code)
            
            complexity = 0
            function_complexities = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_complexity = 1
                    # Count decision points
                    for child in ast.walk(node):
                        if isinstance(child, (ast.If, ast.While, ast.For, ast.And, ast.Or, ast.BoolOp)):
                            func_complexity += 1
                        elif isinstance(child, ast.ExceptHandler):
                            func_complexity += 1
                    
                    function_complexities.append({
                        'name': node.name,
                        'complexity': func_complexity,
                        'line': node.lineno
                    })
                    complexity += func_complexity
            
            return {
                'total_complexity': complexity,
                'average_complexity': sum(f['complexity'] for f in function_complexities) / len(function_complexities) if function_complexities else 0,
                'function_complexities': function_complexities
            }
        except Exception as e:
            return {'error': str(e)}
    
    def execute(self, action: str, **kwargs) -> Any:
        """Execute a skill action"""
        if action == 'analyze_security':
            return self.analyze_security(kwargs.get('code', ''))
        elif action == 'analyze_performance':
            return self.analyze_performance(kwargs.get('code', ''))
        elif action == 'analyze_quality':
            return self.analyze_quality(kwargs.get('code', ''))
        elif action == 'generate_improvements':
            return self.generate_improvements(kwargs.get('code', ''))
        elif action == 'calculate_complexity':
            return self.calculate_complexity(kwargs.get('code', ''))
        else:
            raise ValueError(f"Unknown action: {action}")


skill = CodeAnalysisSkill()


def get_skill_info() -> Dict[str, Any]:
    return {
        'name': skill.name,
        'version': skill.version,
        'description': skill.description,
        'actions': ['analyze_security', 'analyze_performance', 'analyze_quality', 'generate_improvements', 'calculate_complexity'],
        'capabilities': {
            'analyze_security': {
                'description': 'Analyze code for security vulnerabilities',
                'parameters': {'code': 'string'}
            },
            'analyze_performance': {
                'description': 'Analyze code for performance issues',
                'parameters': {'code': 'string'}
            },
            'analyze_quality': {
                'description': 'Analyze code for quality issues',
                'parameters': {'code': 'string'}
            },
            'generate_improvements': {
                'description': 'Generate improvement suggestions',
                'parameters': {'code': 'string'}
            },
            'calculate_complexity': {
                'description': 'Calculate code complexity metrics',
                'parameters': {'code': 'string'}
            }
        }
    }
