"""
Security Tools Plugin for Complete Self System

Provides security-related utilities including encryption, hashing, and validation
"""

import json
import hashlib
import base64
import secrets
import string
from typing import Dict, Any


def generate_hash(args: Dict[str, Any]) -> str:
    text = args.get('text', '')
    algorithm = args.get('algorithm', 'sha256')
    if not text:
        return "No text provided"
    try:
        if algorithm == 'md5':
            hasher = hashlib.md5()
        elif algorithm == 'sha1':
            hasher = hashlib.sha1()
        elif algorithm == 'sha256':
            hasher = hashlib.sha256()
        elif algorithm == 'sha512':
            hasher = hashlib.sha512()
        else:
            return f"Unsupported algorithm: {algorithm}"
        hasher.update(text.encode('utf-8'))
        return hasher.hexdigest()
    except Exception as e:
        return f"Hash generation failed: {str(e)}"


def generate_password(args: Dict[str, Any]) -> str:
    length = int(args.get('length', 16))
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(characters) for _ in range(length))
    return password


PLUGIN_NAME = "security_tools"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Security-related utilities including encryption, hashing, password generation, and validation"

AVAILABLE_FUNCTIONS = {
    'generate_hash': {
        'description': 'Generate a cryptographic hash of text',
        'parameters': {
            'text': {'type': 'string', 'required': True, 'description': 'Text to hash'},
            'algorithm': {'type': 'string', 'required': False, 'description': 'Hash algorithm (default: sha256)', 'default': 'sha256'}
        },
        'handler': generate_hash
    },
    'generate_password': {
        'description': 'Generate a secure random password',
        'parameters': {
            'length': {'type': 'integer', 'required': False, 'description': 'Password length (default: 16)', 'default': 16}
        },
        'handler': generate_password
    }
}

def get_plugin_info() -> Dict[str, Any]:
    return {'name': PLUGIN_NAME, 'version': PLUGIN_VERSION, 'description': PLUGIN_DESCRIPTION, 'functions': AVAILABLE_FUNCTIONS}