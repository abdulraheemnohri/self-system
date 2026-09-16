"""
Math Tools Plugin

Provides mathematical computation and calculation tools.
"""

import math
import statistics
from typing import Dict, Any, List, Union


def calculate(expression: str) -> Dict[str, Any]:
    """
    Evaluate a mathematical expression.
    
    Args:
        expression: Mathematical expression as a string (e.g., "2 + 3 * 4")
    
    Returns:
        Dictionary with result and expression
    """
    try:
        # Safe evaluation of mathematical expressions
        result = eval(expression, {"__builtins__": {}}, {
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
            "sqrt": math.sqrt,
            "exp": math.exp,
            "log": math.log,
            "log10": math.log10,
            "log2": math.log2,
            "pow": math.pow,
            "fabs": math.fabs,
            "floor": math.floor,
            "ceil": math.ceil,
            "round": round,
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "pi": math.pi,
            "e": math.e,
            "tau": math.tau,
            "inf": math.inf,
            "nan": math.nan,
        })
        return {"result": result, "expression": expression, "success": True}
    except Exception as e:
        return {"error": str(e), "expression": expression, "success": False}


def calculate_advanced(expression: str, variables: Dict[str, float] = None) -> Dict[str, Any]:
    """
    Evaluate a mathematical expression with variables.
    """
    if variables is None:
        variables = {}
    
    try:
        safe_globals = {"__builtins__": {}}
        safe_locals = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "sqrt": math.sqrt,
            "exp": math.exp,
            "log": math.log,
            "log10": math.log10,
            "pi": math.pi,
            "e": math.e,
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": math.pow,
        }
        safe_locals.update(variables)
        
        result = eval(expression, safe_globals, safe_locals)
        return {"result": result, "expression": expression, "variables": variables, "success": True}
    except Exception as e:
        return {"error": str(e), "expression": expression, "success": False}


def statistics_mean(data: List[float]) -> Dict[str, Any]:
    """Calculate the mean (average) of a list of numbers."""
    try:
        result = statistics.mean(data)
        return {"result": result, "data": data, "operation": "mean", "success": True}
    except Exception as e:
        return {"error": str(e), "operation": "mean", "success": False}


def statistics_median(data: List[float]) -> Dict[str, Any]:
    """Calculate the median of a list of numbers."""
    try:
        result = statistics.median(data)
        return {"result": result, "data": data, "operation": "median", "success": True}
    except Exception as e:
        return {"error": str(e), "operation": "median", "success": False}


def statistics_stdev(data: List[float], sample: bool = True) -> Dict[str, Any]:
    """Calculate the standard deviation of a list of numbers."""
    try:
        if sample:
            result = statistics.stdev(data)
            op = "sample_stdev"
        else:
            result = statistics.pstdev(data)
            op = "population_stdev"
        return {"result": result, "data": data, "operation": op, "success": True}
    except Exception as e:
        return {"error": str(e), "operation": "stdev", "success": False}


def statistics_variance(data: List[float], sample: bool = True) -> Dict[str, Any]:
    """Calculate the variance of a list of numbers."""
    try:
        if sample:
            result = statistics.variance(data)
            op = "sample_variance"
        else:
            result = statistics.pvariance(data)
            op = "population_variance"
        return {"result": result, "data": data, "operation": op, "success": True}
    except Exception as e:
        return {"error": str(e), "operation": "variance", "success": False}


def statistics_summary(data: List[float]) -> Dict[str, Any]:
    """Calculate comprehensive statistics for a list of numbers."""
    try:
        if len(data) < 2:
            return {"error": "Need at least 2 data points for statistics", "success": False}
        
        result = {
            "count": len(data),
            "mean": statistics.mean(data),
            "median": statistics.median(data),
            "mode": statistics.multimode(data) if hasattr(statistics, 'multimode') else statistics.mode(data),
            "min": min(data),
            "max": max(data),
            "range": max(data) - min(data),
            "sample_stdev": statistics.stdev(data),
            "sample_variance": statistics.variance(data),
            "population_stdev": statistics.pstdev(data),
            "population_variance": statistics.pvariance(data),
        }
        return {"result": result, "data": data, "success": True}
    except Exception as e:
        return {"error": str(e), "operation": "statistics_summary", "success": False}


def trigonometry(value: float, function: str = "sin") -> Dict[str, Any]:
    """Calculate trigonometric functions."""
    func_map = {
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
    }
    
    if function not in func_map:
        return {"error": f"Unknown function: {function}", "success": False}
    
    try:
        result = func_map[function](value)
        return {"result": result, "value": value, "function": function, "success": True}
    except Exception as e:
        return {"error": str(e), "function": function, "success": False}


def convert_units(value: float, from_unit: str, to_unit: str) -> Dict[str, Any]:
    """Convert between common units."""
    length_conversions = {
        "m": 1.0,
        "km": 1000.0,
        "cm": 0.01,
        "mm": 0.001,
        "mi": 1609.34,
        "yd": 0.9144,
        "ft": 0.3048,
        "in": 0.0254,
    }
    
    temp_conversions = {
        "c_to_f": lambda c: c * 9/5 + 32,
        "f_to_c": lambda f: (f - 32) * 5/9,
        "c_to_k": lambda c: c + 273.15,
        "k_to_c": lambda k: k - 273.15,
        "f_to_k": lambda f: (f - 32) * 5/9 + 273.15,
        "k_to_f": lambda k: (k - 273.15) * 9/5 + 32,
    }
    
    key = f"{from_unit}_to_{to_unit}"
    if key in temp_conversions:
        try:
            result = temp_conversions[key](value)
            return {"result": result, "value": value, "from": from_unit, "to": to_unit, "success": True}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    if from_unit in length_conversions and to_unit in length_conversions:
        try:
            meters = value * length_conversions[from_unit]
            result = meters / length_conversions[to_unit]
            return {"result": result, "value": value, "from": from_unit, "to": to_unit, "success": True}
        except Exception as e:
            return {"error": str(e), "success": False}
    
    return {"error": f"Cannot convert from {from_unit} to {to_unit}", "success": False}


PLUGIN_METADATA = {
    "name": "math_tools",
    "version": "1.0.0",
    "description": "Mathematical computation and calculation tools",
    "author": "Self System",
    "functions": [
        {"name": "calculate", "description": "Evaluate mathematical expressions"},
        {"name": "calculate_advanced", "description": "Evaluate expressions with variables"},
        {"name": "statistics_mean", "description": "Calculate mean (average)"},
        {"name": "statistics_median", "description": "Calculate median"},
        {"name": "statistics_stdev", "description": "Calculate standard deviation"},
        {"name": "statistics_variance", "description": "Calculate variance"},
        {"name": "statistics_summary", "description": "Calculate comprehensive statistics"},
        {"name": "trigonometry", "description": "Calculate trigonometric functions"},
        {"name": "convert_units", "description": "Convert between units"},
    ],
}


def get_metadata() -> Dict[str, Any]:
    """Return plugin metadata."""
    return PLUGIN_METADATA
