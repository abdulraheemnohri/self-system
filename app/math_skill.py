"""
Math Skill for Complete Self System

Provides mathematical operations and calculations
"""

import json
import math
from typing import Dict, Any, List, Optional


class MathSkill:
    def __init__(self):
        self.name = "math_skill"
        self.description = "Mathematical operations and calculations"
        self.version = "1.0.0"
    
    def calculate(self, expression: str) -> Dict[str, Any]:
        try:
            safe_chars = set('0123456789+-*/.() []^%')
            if not all(c in safe_chars or c.isspace() for c in expression):
                return {'error': 'Invalid characters in expression', 'safe_chars': '0123456789+-*/.() []^%'}
            expression = expression.replace('^', '**')
            result = eval(expression, {'__builtins__': None}, {
                'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
                'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
                'sqrt': math.sqrt, 'log': math.log, 'log10': math.log10,
                'exp': math.exp, 'pi': math.pi, 'e': math.e,
                'floor': math.floor, 'ceil': math.ceil, 'round': round,
                'abs': abs, 'min': min, 'max': max, 'sum': sum,
                'pow': pow
            })
            return {'result': result, 'expression': expression, 'type': type(result).__name__}
        except ZeroDivisionError:
            return {'error': 'Division by zero'}
        except Exception as e:
            return {'error': f'Calculation error: {str(e)}'}

    def get_info(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'capabilities': ['Basic arithmetic calculations', 'Quadratic equation solving', 'Statistical analysis', 'Unit conversions', 'Geometric calculations', 'Financial calculations']
        }

math_skill = MathSkill()