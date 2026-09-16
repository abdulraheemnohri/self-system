"""
Sample Tool Plugin for Complete Self System

Demonstrates plugin architecture with text manipulation tools
"""

import json
from typing import Dict, Any


def reverse_text(args: Dict[str, Any]) -> str:
    text = args.get('text', '')
    return text[::-1]


def uppercase_text(args: Dict[str, Any]) -> str:
    text = args.get('text', '')
    return text.upper()


def lowercase_text(args: Dict[str, Any]) -> str:
    text = args.get('text', '')
    return text.lower()


def count_words(args: Dict[str, Any]) -> str:
    text = args.get('text', '')
    return str(len(text.split()))


def count_chars(args: Dict[str, Any]) -> str:
    text = args.get('text', '')
    return str(len(text))


PLUGIN_NAME = "sample_tool"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Sample text manipulation tools"

AVAILABLE_FUNCTIONS = {
    'reverse_text': {'description': 'Reverse the input text', 'parameters': {'text': {'type': 'string', 'required': True, 'description': 'Text to reverse'}}, 'handler': reverse_text},
    'uppercase_text': {'description': 'Convert text to uppercase', 'parameters': {'text': {'type': 'string', 'required': True, 'description': 'Text to convert'}}, 'handler': uppercase_text},
    'lowercase_text': {'description': 'Convert text to lowercase', 'parameters': {'text': {'type': 'string', 'required': True, 'description': 'Text to convert'}}, 'handler': lowercase_text},
    'count_words': {'description': 'Count words in text', 'parameters': {'text': {'type': 'string', 'required': True, 'description': 'Text to count'}}, 'handler': count_words},
    'count_chars': {'description': 'Count characters in text', 'parameters': {'text': {'type': 'string', 'required': True, 'description': 'Text to count'}}, 'handler': count_chars}
}


def get_plugin_info() -> Dict[str, Any]:
    return {'name': PLUGIN_NAME, 'version': PLUGIN_VERSION, 'description': PLUGIN_DESCRIPTION, 'functions': AVAILABLE_FUNCTIONS}
