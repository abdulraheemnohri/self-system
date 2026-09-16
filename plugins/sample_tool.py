#!/usr/bin/env python3
"""
Sample Plugin for Complete Self System

This is a sample plugin that demonstrates the plugin interface.
All plugins must define an `execute(args)` function.

Usage:
    /run sample_tool hello world
    
Result:
    Sample plugin received: hello world
    
Additional functions:
    /run sample_tool {"action": "reverse", "text": "hello"} -> "olleh"
    /run sample_tool {"action": "uppercase", "text": "hello"} -> "HELLO"
    /run sample_tool {"action": "lowercase", "text": "HELLO"} -> "hello"
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
