"""
Data Tools Plugin for Complete Self System

Provides data processing, analysis, and transformation utilities
"""

import json
import csv
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import Counter


def parse_json(args: Dict[str, Any]) -> str:
    """Parse and validate JSON data"""
    data = args.get('data', '')
    
    if not data:
        return "No JSON data provided"
    
    try:
        parsed = json.loads(data)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError as e:
        return f"JSON parsing failed: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"


def parse_csv(args: Dict[str, Any]) -> str:
    """Parse CSV data and return as JSON"""
    data = args.get('data', '')
    delimiter = args.get('delimiter', ',')
    has_header = args.get('header', True)
    
    if not data:
        return "No CSV data provided"
    
    try:
        lines = data.strip().splitlines()
        reader = csv.reader(lines, delimiter=delimiter)
        
        if has_header:
            headers = next(reader)
            result = [dict(zip(headers, row)) for row in reader]
        else:
            result = [row for row in reader]
        
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"CSV parsing failed: {str(e)}"


def filter_data(args: Dict[str, Any]) -> str:
    """Filter data based on conditions"""
    data = args.get('data', '')
    conditions = args.get('conditions', {})
    
    if not data:
        return "No data provided"
    
    try:
        parsed = json.loads(data)
        if not isinstance(parsed, list):
            return "Data must be a JSON array"
        
        filtered = []
        for item in parsed:
            match = True
            for key, condition in conditions.items():
                if key not in item:
                    match = False
                    break
                
                # Simple condition checking
                if isinstance(condition, dict):
                    op = condition.get('op', 'eq')
                    value = condition.get('value')
                    item_value = item[key]
                    
                    if op == 'eq':
                        if item_value != value:
                            match = False
                            break
                    elif op == 'ne':
                        if item_value == value:
                            match = False
                            break
                    elif op == 'gt':
                        if not (item_value > value):
                            match = False
                            break
                    elif op == 'lt':
                        if not (item_value < value):
                            match = False
                            break
                    elif op == 'contains':
                        if value not in str(item_value):
                            match = False
                            break
                else:
                    # Direct equality
                    if item.get(key) != condition:
                        match = False
                        break
            
            if match:
                filtered.append(item)
        
        return json.dumps(filtered, indent=2)
    except Exception as e:
        return f"Filtering failed: {str(e)}"


def transform_data(args: Dict[str, Any]) -> str:
    """Transform data using mapping rules"""
    data = args.get('data', '')
    mapping = args.get('mapping', {})
    
    if not data:
        return "No data provided"
    
    try:
        parsed = json.loads(data)
        if not isinstance(parsed, list):
            return "Data must be a JSON array"
        
        transformed = []
        for item in parsed:
            new_item = {}
            for new_key, rule in mapping.items():
                if isinstance(rule, str):
                    # Direct copy
                    new_item[new_key] = item.get(rule)
                elif isinstance(rule, dict):
                    # Transformation rule
                    source = rule.get('source')
                    transform_type = rule.get('type', 'copy')
                    
                    if source not in item:
                        continue
                    
                    value = item[source]
                    if transform_type == 'uppercase':
                        new_item[new_key] = str(value).upper()
                    elif transform_type == 'lowercase':
                        new_item[new_key] = str(value).lower()
                    elif transform_type == 'length':
                        new_item[new_key] = len(str(value))
                    elif transform_type == 'prefix':
                        prefix = rule.get('prefix', '')
                        new_item[new_key] = f"{prefix}{value}"
                    elif transform_type == 'suffix':
                        suffix = rule.get('suffix', '')
                        new_item[new_key] = f"{value}{suffix}"
                    else:
                        new_item[new_key] = value
            
            transformed.append(new_item)
        
        return json.dumps(transformed, indent=2)
    except Exception as e:
        return f"Transformation failed: {str(e)}"


def aggregate_data(args: Dict[str, Any]) -> str:
    """Aggregate data with various operations"""
    data = args.get('data', '')
    group_by = args.get('group_by', '')
    aggregate = args.get('aggregate', {})
    
    if not data:
        return "No data provided"
    
    try:
        parsed = json.loads(data)
        if not isinstance(parsed, list):
            return "Data must be a JSON array"
        
        if not group_by:
            # Simple aggregation on entire dataset
            result = {}
            for op, field in aggregate.items():
                values = [item.get(field) for item in parsed if field in item]
                if op == 'sum':
                    result[field] = sum(float(v) for v in values if v is not None)
                elif op == 'avg':
                    result[field] = sum(float(v) for v in values if v is not None) / len(values) if values else 0
                elif op == 'count':
                    result[field] = len(values)
                elif op == 'max':
                    result[field] = max(values) if values else None
                elif op == 'min':
                    result[field] = min(values) if values else None
                elif op == 'collect':
                    result[field] = list(set(values))
            return json.dumps(result, indent=2)
        else:
            # Group by aggregation
            groups = {}
            for item in parsed:
                key = item.get(group_by)
                if key not in groups:
                    groups[key] = []
                groups[key].append(item)
            
            result = {}
            for key, items in groups.items():
                group_result = {}
                for op, field in aggregate.items():
                    values = [item.get(field) for item in items if field in item]
                    if op == 'sum':
                        group_result[field] = sum(float(v) for v in values if v is not None)
                    elif op == 'avg':
                        group_result[field] = sum(float(v) for v in values if v is not None) / len(values) if values else 0
                    elif op == 'count':
                        group_result[field] = len(values)
                    elif op == 'max':
                        group_result[field] = max(values) if values else None
                    elif op == 'min':
                        group_result[field] = min(values) if values else None
                    elif op == 'collect':
                        group_result[field] = list(set(values))
                result[key] = group_result
            
            return json.dumps(result, indent=2)
    except Exception as e:
        return f"Aggregation failed: {str(e)}"


def sort_data(args: Dict[str, Any]) -> str:
    """Sort data by one or more fields"""
    data = args.get('data', '')
    sort_by = args.get('sort_by', '')
    descending = args.get('descending', False)
    
    if not data:
        return "No data provided"
    
    try:
        parsed = json.loads(data)
        if not isinstance(parsed, list):
            return "Data must be a JSON array"
        
        if sort_by:
            fields = sort_by.split(',')
            parsed.sort(key=lambda x: tuple(x.get(f, '') for f in fields), reverse=descending)
        
        return json.dumps(parsed, indent=2)
    except Exception as e:
        return f"Sorting failed: {str(e)}"


def deduplicate_data(args: Dict[str, Any]) -> str:
    """Remove duplicate items from data"""
    data = args.get('data', '')
    key = args.get('key', None)
    
    if not data:
        return "No data provided"
    
    try:
        parsed = json.loads(data)
        if not isinstance(parsed, list):
            return "Data must be a JSON array"
        
        if key:
            # Deduplicate by key
            seen = set()
            unique = []
            for item in parsed:
                value = item.get(key)
                if value not in seen:
                    seen.add(value)
                    unique.append(item)
            return json.dumps(unique, indent=2)
        else:
            # Deduplicate by entire object
            seen = set()
            unique = []
            for item in parsed:
                item_str = json.dumps(item, sort_keys=True)
                if item_str not in seen:
                    seen.add(item_str)
                    unique.append(item)
            return json.dumps(unique, indent=2)
    except Exception as e:
        return f"Deduplication failed: {str(e)}"


def extract_pattern(args: Dict[str, Any]) -> str:
    """Extract data matching a regex pattern"""
    data = args.get('data', '')
    pattern = args.get('pattern', '')
    
    if not data or not pattern:
        return "Data and pattern are required"
    
    try:
        matches = re.findall(pattern, data)
        return json.dumps(matches, indent=2)
    except Exception as e:
        return f"Pattern extraction failed: {str(e)}"


PLUGIN_NAME = "data_tools"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Data processing, analysis, and transformation utilities"

AVAILABLE_FUNCTIONS = {
    'parse_json': {
        'description': 'Parse and validate JSON data',
        'parameters': {
            'data': {'type': 'string', 'required': True, 'description': 'JSON data to parse'}
        },
        'handler': parse_json
    },
    'parse_csv': {
        'description': 'Parse CSV data and return as JSON',
        'parameters': {
            'data': {'type': 'string', 'required': True, 'description': 'CSV data to parse'},
            'delimiter': {'type': 'string', 'required': False, 'description': 'CSV delimiter (default: ,)', 'default': ','},
            'header': {'type': 'boolean', 'required': False, 'description': 'First row is header (default: true)', 'default': True}
        },
        'handler': parse_csv
    },
    'filter_data': {
        'description': 'Filter data based on conditions',
        'parameters': {
            'data': {'type': 'string', 'required': True, 'description': 'JSON data to filter'},
            'conditions': {'type': 'object', 'required': False, 'description': 'Filter conditions', 'default': {}}
        },
        'handler': filter_data
    },
    'transform_data': {
        'description': 'Transform data using mapping rules',
        'parameters': {
            'data': {'type': 'string', 'required': True, 'description': 'JSON data to transform'},
            'mapping': {'type': 'object', 'required': False, 'description': 'Transformation mapping', 'default': {}}
        },
        'handler': transform_data
    },
    'aggregate_data': {
        'description': 'Aggregate data with various operations',
        'parameters': {
            'data': {'type': 'string', 'required': True, 'description': 'JSON data to aggregate'},
            'group_by': {'type': 'string', 'required': False, 'description': 'Field to group by'},
            'aggregate': {'type': 'object', 'required': False, 'description': 'Aggregation operations', 'default': {}}
        },
        'handler': aggregate_data
    },
    'sort_data': {
        'description': 'Sort data by one or more fields',
        'parameters': {
            'data': {'type': 'string', 'required': True, 'description': 'JSON data to sort'},
            'sort_by': {'type': 'string', 'required': False, 'description': 'Field(s) to sort by'},
            'descending': {'type': 'boolean', 'required': False, 'description': 'Sort in descending order (default: false)', 'default': False}
        },
        'handler': sort_data
    },
    'deduplicate_data': {
        'description': 'Remove duplicate items from data',
        'parameters': {
            'data': {'type': 'string', 'required': True, 'description': 'JSON data to deduplicate'},
            'key': {'type': 'string', 'required': False, 'description': 'Key to deduplicate by'}
        },
        'handler': deduplicate_data
    },
    'extract_pattern': {
        'description': 'Extract data matching a regex pattern',
        'parameters': {
            'data': {'type': 'string', 'required': True, 'description': 'Text to search in'},
            'pattern': {'type': 'string', 'required': True, 'description': 'Regex pattern to match'}
        },
        'handler': extract_pattern
    }
}


def get_plugin_info() -> Dict[str, Any]:
    return {'name': PLUGIN_NAME, 'version': PLUGIN_VERSION, 'description': PLUGIN_DESCRIPTION, 'functions': AVAILABLE_FUNCTIONS}
