"""
File Tools Plugin for Complete Self System

Provides file system operations including read, write, search, and management
"""

import json
import os
import glob
from typing import Dict, Any, List
from pathlib import Path


def read_file(args: Dict[str, Any]) -> str:
    """Read content from a file"""
    path = args.get('path', '')
    offset = int(args.get('offset', 0))
    limit = args.get('limit')
    
    if not path:
        return "No file path provided"
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            if limit:
                content = content[offset:offset + int(limit)]
            elif offset:
                content = content[offset:]
        return content
    except FileNotFoundError:
        return f"File not found: {path}"
    except Exception as e:
        return f"Read failed: {str(e)}"


def write_file(args: Dict[str, Any]) -> str:
    """Write content to a file"""
    path = args.get('path', '')
    content = args.get('content', '')
    append = args.get('append', False)
    
    if not path:
        return "No file path provided"
    
    try:
        mode = 'a' if append else 'w'
        with open(path, mode, encoding='utf-8') as f:
            f.write(content)
        return f"File written: {path}"
    except Exception as e:
        return f"Write failed: {str(e)}"


def file_exists(args: Dict[str, Any]) -> str:
    """Check if a file exists"""
    path = args.get('path', '')
    
    if not path:
        return "No file path provided"
    
    return json.dumps({'path': path, 'exists': os.path.exists(path), 'is_file': os.path.isfile(path), 'is_dir': os.path.isdir(path)})


def get_file_info(args: Dict[str, Any]) -> str:
    """Get detailed information about a file"""
    path = args.get('path', '')
    
    if not path:
        return "No file path provided"
    
    try:
        stat = os.stat(path)
        info = {
            'path': path,
            'exists': True,
            'size': stat.st_size,
            'created': stat.st_ctime,
            'modified': stat.st_mtime,
            'accessed': stat.st_atime,
            'is_file': os.path.isfile(path),
            'is_dir': os.path.isdir(path),
            'permissions': oct(stat.st_mode)[-3:]
        }
        
        if os.path.isfile(path):
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            info['line_count'] = len(content.splitlines())
            info['first_100_chars'] = content[:100]
        
        return json.dumps(info, indent=2)
    except Exception as e:
        return f"File info failed: {str(e)}"


def list_files(args: Dict[str, Any]) -> str:
    """List files in a directory"""
    path = args.get('path', '.')
    pattern = args.get('pattern', '*')
    recursive = args.get('recursive', False)
    
    try:
        if recursive:
            files = list(Path(path).rglob(pattern))
        else:
            files = list(Path(path).glob(pattern))
        
        file_list = []
        for f in files:
            stat = f.stat()
            file_list.append({
                'name': str(f),
                'size': stat.st_size,
                'is_dir': f.is_dir()
            })
        
        return json.dumps(file_list, indent=2)
    except Exception as e:
        return f"List files failed: {str(e)}"


def search_in_files(args: Dict[str, Any]) -> str:
    """Search for text in files"""
    path = args.get('path', '.')
    pattern = args.get('pattern', '*')
    search_text = args.get('text', '')
    recursive = args.get('recursive', True)
    
    if not search_text:
        return "No search text provided"
    
    try:
        matches = []
        if recursive:
            files = list(Path(path).rglob(pattern))
        else:
            files = list(Path(path).glob(pattern))
        
        for file_path in files:
            if file_path.is_file():
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.splitlines()
                    for i, line in enumerate(lines, 1):
                        if search_text in line:
                            matches.append({
                                'file': str(file_path),
                                'line': i,
                                'content': line.strip()
                            })
        
        return json.dumps(matches, indent=2)
    except Exception as e:
        return f"Search failed: {str(e)}"


def copy_file(args: Dict[str, Any]) -> str:
    """Copy a file from source to destination"""
    source = args.get('source', '')
    destination = args.get('destination', '')
    
    if not source or not destination:
        return "Source and destination are required"
    
    try:
        import shutil
        shutil.copy2(source, destination)
        return f"File copied: {source} -> {destination}"
    except Exception as e:
        return f"Copy failed: {str(e)}"


def move_file(args: Dict[str, Any]) -> str:
    """Move a file from source to destination"""
    source = args.get('source', '')
    destination = args.get('destination', '')
    
    if not source or not destination:
        return "Source and destination are required"
    
    try:
        import shutil
        shutil.move(source, destination)
        return f"File moved: {source} -> {destination}"
    except Exception as e:
        return f"Move failed: {str(e)}"


def delete_file(args: Dict[str, Any]) -> str:
    """Delete a file"""
    path = args.get('path', '')
    
    if not path:
        return "No file path provided"
    
    try:
        os.remove(path)
        return f"File deleted: {path}"
    except Exception as e:
        return f"Delete failed: {str(e)}"


def create_directory(args: Dict[str, Any]) -> str:
    """Create a directory"""
    path = args.get('path', '')
    
    if not path:
        return "No directory path provided"
    
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return f"Directory created: {path}"
    except Exception as e:
        return f"Directory creation failed: {str(e)}"


PLUGIN_NAME = "file_tools"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "File system operations including read, write, search, and management"

AVAILABLE_FUNCTIONS = {
    'read_file': {
        'description': 'Read content from a file',
        'parameters': {
            'path': {'type': 'string', 'required': True, 'description': 'File path'},
            'offset': {'type': 'integer', 'required': False, 'description': 'Starting offset (default: 0)', 'default': 0},
            'limit': {'type': 'integer', 'required': False, 'description': 'Number of characters to read'}
        },
        'handler': read_file
    },
    'write_file': {
        'description': 'Write content to a file',
        'parameters': {
            'path': {'type': 'string', 'required': True, 'description': 'File path'},
            'content': {'type': 'string', 'required': True, 'description': 'Content to write'},
            'append': {'type': 'boolean', 'required': False, 'description': 'Append to file (default: false)', 'default': False}
        },
        'handler': write_file
    },
    'file_exists': {
        'description': 'Check if a file exists',
        'parameters': {
            'path': {'type': 'string', 'required': True, 'description': 'File path to check'}
        },
        'handler': file_exists
    },
    'get_file_info': {
        'description': 'Get detailed information about a file',
        'parameters': {
            'path': {'type': 'string', 'required': True, 'description': 'File path'}
        },
        'handler': get_file_info
    },
    'list_files': {
        'description': 'List files in a directory',
        'parameters': {
            'path': {'type': 'string', 'required': False, 'description': 'Directory path (default: .)', 'default': '.'},
            'pattern': {'type': 'string', 'required': False, 'description': 'File pattern (default: *)', 'default': '*'},
            'recursive': {'type': 'boolean', 'required': False, 'description': 'Recursive search (default: false)', 'default': False}
        },
        'handler': list_files
    },
    'search_in_files': {
        'description': 'Search for text in files',
        'parameters': {
            'path': {'type': 'string', 'required': False, 'description': 'Directory path (default: .)', 'default': '.'},
            'pattern': {'type': 'string', 'required': False, 'description': 'File pattern (default: *)', 'default': '*'},
            'text': {'type': 'string', 'required': True, 'description': 'Text to search for'},
            'recursive': {'type': 'boolean', 'required': False, 'description': 'Recursive search (default: true)', 'default': True}
        },
        'handler': search_in_files
    },
    'copy_file': {
        'description': 'Copy a file',
        'parameters': {
            'source': {'type': 'string', 'required': True, 'description': 'Source file path'},
            'destination': {'type': 'string', 'required': True, 'description': 'Destination file path'}
        },
        'handler': copy_file
    },
    'move_file': {
        'description': 'Move a file',
        'parameters': {
            'source': {'type': 'string', 'required': True, 'description': 'Source file path'},
            'destination': {'type': 'string', 'required': True, 'description': 'Destination file path'}
        },
        'handler': move_file
    },
    'delete_file': {
        'description': 'Delete a file',
        'parameters': {
            'path': {'type': 'string', 'required': True, 'description': 'File path to delete'}
        },
        'handler': delete_file
    },
    'create_directory': {
        'description': 'Create a directory',
        'parameters': {
            'path': {'type': 'string', 'required': True, 'description': 'Directory path'}
        },
        'handler': create_directory
    }
}


def get_plugin_info() -> Dict[str, Any]:
    return {'name': PLUGIN_NAME, 'version': PLUGIN_VERSION, 'description': PLUGIN_DESCRIPTION, 'functions': AVAILABLE_FUNCTIONS}
