"""
Data Processing Skill for Complete Self System

Provides advanced data processing including cleaning, transformation, and analysis
"""

import json
import csv
import re
from typing import Dict, Any, List, Optional
from collections import Counter, defaultdict
from .llm import simple_llm_reply


class DataProcessingSkill:
    """Skill for processing and analyzing data"""
    
    def __init__(self):
        self.name = "data_processing"
        self.description = "Advanced data processing including cleaning, transformation, and analysis"
        self.version = "1.0.0"
    
    def clean_data(self, data: str, format: str = 'json') -> Dict[str, Any]:
        """Clean and normalize data"""
        if format == 'json':
            try:
                parsed = json.loads(data)
                return self._clean_json(parsed)
            except json.JSONDecodeError:
                return {'error': 'Invalid JSON data'}
        elif format == 'csv':
            try:
                lines = data.strip().splitlines()
                reader = csv.reader(lines)
                headers = next(reader) if lines else []
                rows = [dict(zip(headers, row)) for row in reader]
                return self._clean_json(rows)
            except Exception as e:
                return {'error': str(e)}
        else:
            return {'error': f'Unsupported format: {format}'}
    
    def _clean_json(self, data: Any) -> Dict[str, Any]:
        """Recursively clean JSON data"""
        if isinstance(data, dict):
            cleaned = {}
            for k, v in data.items():
                if v is None or v == '':
                    continue
                cleaned[str(k).strip()] = self._clean_json(v)
            return cleaned
        elif isinstance(data, list):
            return [self._clean_json(item) for item in data if item is not None]
        elif isinstance(data, str):
            return data.strip()
        else:
            return data
    
    def transform_data(self, data: str, transformation: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data based on rules"""
        try:
            parsed = json.loads(data)
            if not isinstance(parsed, list):
                parsed = [parsed]
            
            result = []
            for item in parsed:
                transformed = self._apply_transformation(item, transformation)
                result.append(transformed)
            
            return result
        except Exception as e:
            return {'error': str(e)}
    
    def _apply_transformation(self, item: Dict[str, Any], transformation: Dict[str, Any]) -> Dict[str, Any]:
        """Apply transformation rules to a data item"""
        result = {}
        
        for new_key, rule in transformation.items():
            if isinstance(rule, str):
                # Direct copy
                result[new_key] = item.get(rule)
            elif isinstance(rule, dict):
                source = rule.get('source')
                if source not in item:
                    continue
                
                value = item[source]
                transform_type = rule.get('type', 'copy')
                
                if transform_type == 'uppercase':
                    result[new_key] = str(value).upper()
                elif transform_type == 'lowercase':
                    result[new_key] = str(value).lower()
                elif transform_type == 'capitalize':
                    result[new_key] = str(value).capitalize()
                elif transform_type == 'length':
                    result[new_key] = len(str(value))
                elif transform_type == 'prefix':
                    prefix = rule.get('prefix', '')
                    result[new_key] = f"{prefix}{value}"
                elif transform_type == 'suffix':
                    suffix = rule.get('suffix', '')
                    result[new_key] = f"{value}{suffix}"
                elif transform_type == 'replace':
                    old = rule.get('old', '')
                    new = rule.get('new', '')
                    result[new_key] = str(value).replace(old, new)
                elif transform_type == 'extract':
                    pattern = rule.get('pattern', '')
                    matches = re.findall(pattern, str(value))
                    result[new_key] = matches[0] if matches else None
                else:
                    result[new_key] = value
        
        return result
    
    def analyze_data(self, data: str, analysis_type: str = 'statistics') -> Dict[str, Any]:
        """Analyze data with various analysis types"""
        try:
            parsed = json.loads(data)
            if not isinstance(parsed, list):
                return {'error': 'Data must be a JSON array'}
            
            if analysis_type == 'statistics':
                return self._analyze_statistics(parsed)
            elif analysis_type == 'distribution':
                field = analysis_type.get('field', '')
                return self._analyze_distribution(parsed, field)
            elif analysis_type == 'correlation':
                return self._analyze_correlation(parsed)
            else:
                return {'error': f'Unsupported analysis type: {analysis_type}'}
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate basic statistics for all numeric fields"""
        if not data:
            return {}
        
        numeric_fields = self._find_numeric_fields(data)
        stats = {}
        
        for field in numeric_fields:
            values = [item[field] for item in data if field in item and isinstance(item[field], (int, float))]
            if values:
                stats[field] = {
                    'count': len(values),
                    'min': min(values),
                    'max': max(values),
                    'mean': sum(values) / len(values),
                    'sum': sum(values)
                }
        
        return stats
    
    def _find_numeric_fields(self, data: List[Dict[str, Any]]) -> List[str]:
        """Find all numeric fields in the data"""
        numeric_fields = set()
        for item in data:
            for key, value in item.items():
                if isinstance(value, (int, float)):
                    numeric_fields.add(key)
        return list(numeric_fields)
    
    def _analyze_distribution(self, data: List[Dict[str, Any]], field: str) -> Dict[str, Any]:
        """Analyze the distribution of values in a field"""
        if not data or not field:
            return {}
        
        values = [item[field] for item in data if field in item]
        if not values:
            return {}
        
        counter = Counter(values)
        return {
            'field': field,
            'unique_values': len(counter),
            'total_count': len(values),
            'distribution': dict(counter.most_common())
        }
    
    def _analyze_correlation(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze correlations between numeric fields"""
        numeric_fields = self._find_numeric_fields(data)
        if len(numeric_fields) < 2:
            return {'error': 'Need at least 2 numeric fields for correlation analysis'}
        
        correlations = {}
        for i, field1 in enumerate(numeric_fields):
            for field2 in numeric_fields[i+1:]:
                pairs = [(item[field1], item[field2]) for item in data if field1 in item and field2 in item]
                if len(pairs) > 1:
                    correlation = self._calculate_pearson(pairs)
                    correlations[f'{field1}_{field2}'] = correlation
        
        return correlations
    
    def _calculate_pearson(self, pairs: List[Tuple[float, float]]) -> float:
        """Calculate Pearson correlation coefficient"""
        n = len(pairs)
        if n < 2:
            return 0.0
        
        x = [p[0] for p in pairs]
        y = [p[1] for p in pairs]
        
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        covariance = sum((xi - mean_x) * (yi - mean_y) for xi, yi in pairs) / n
        std_x = (sum((xi - mean_x) ** 2 for xi in x) / n) ** 0.5
        std_y = (sum((yi - mean_y) ** 2 for yi in y) / n) ** 0.5
        
        if std_x == 0 or std_y == 0:
            return 0.0
        
        return covariance / (std_x * std_y)
    
    def generate_insights(self, data: str, question: str = '') -> str:
        """Generate insights from data using LLM"""
        try:
            parsed = json.loads(data)
            if not isinstance(parsed, list):
                parsed = [parsed]
            
            data_str = json.dumps(parsed[:10], indent=2)  # Limit to first 10 items
            prompt = f"Analyze the following data and provide insights:\n\n{data_str}\n\n"
            
            if question:
                prompt += f"Specific question: {question}\n"
            else:
                prompt += "Identify patterns, trends, anomalies, and key insights."
            
            messages = [
                {'role': 'system', 'content': 'You are a data analyst.'},
                {'role': 'user', 'content': prompt}
            ]
            
            return simple_llm_reply(messages, max_tokens=3000, temperature=0.3)
        except Exception as e:
            return f"Insight generation failed: {str(e)}"
    
    def validate_data(self, data: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against a schema"""
        try:
            parsed = json.loads(data)
            if not isinstance(parsed, list):
                parsed = [parsed]
            
            errors = []
            for i, item in enumerate(parsed):
                item_errors = self._validate_item(item, schema)
                if item_errors:
                    errors.append({'index': i, 'errors': item_errors})
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'total_items': len(parsed),
                'valid_items': len(parsed) - len(errors)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def _validate_item(self, item: Dict[str, Any], schema: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate a single data item against schema"""
        errors = []
        
        for field, field_schema in schema.items():
            if field not in item:
                if field_schema.get('required', False):
                    errors.append({
                        'field': field,
                        'error': 'Missing required field'
                    })
                continue
            
            value = item[field]
            expected_type = field_schema.get('type', 'any')
            
            if expected_type == 'string' and not isinstance(value, str):
                errors.append({'field': field, 'error': f'Expected string, got {type(value).__name__}'})
            elif expected_type == 'number' and not isinstance(value, (int, float)):
                errors.append({'field': field, 'error': f'Expected number, got {type(value).__name__}'})
            elif expected_type == 'boolean' and not isinstance(value, bool):
                errors.append({'field': field, 'error': f'Expected boolean, got {type(value).__name__}'})
            elif expected_type == 'array' and not isinstance(value, list):
                errors.append({'field': field, 'error': f'Expected array, got {type(value).__name__}'})
            elif expected_type == 'object' and not isinstance(value, dict):
                errors.append({'field': field, 'error': f'Expected object, got {type(value).__name__}'})
            
            # Check enum values
            if 'enum' in field_schema and value not in field_schema['enum']:
                errors.append({'field': field, 'error': f'Value not in allowed enum: {field_schema["enum"]}'})
            
            # Check min/max
            if 'min' in field_schema and isinstance(value, (int, float)) and value < field_schema['min']:
                errors.append({'field': field, 'error': f'Value below minimum: {field_schema["min"]}'})
            if 'max' in field_schema and isinstance(value, (int, float)) and value > field_schema['max']:
                errors.append({'field': field, 'error': f'Value above maximum: {field_schema["max"]}'})
        
        return errors
    
    def execute(self, action: str, **kwargs) -> Any:
        """Execute a skill action"""
        if action == 'clean_data':
            return self.clean_data(kwargs.get('data', ''), kwargs.get('format', 'json'))
        elif action == 'transform_data':
            return self.transform_data(kwargs.get('data', ''), kwargs.get('transformation', {}))
        elif action == 'analyze_data':
            return self.analyze_data(kwargs.get('data', ''), kwargs.get('analysis_type', 'statistics'))
        elif action == 'generate_insights':
            return self.generate_insights(kwargs.get('data', ''), kwargs.get('question', ''))
        elif action == 'validate_data':
            return self.validate_data(kwargs.get('data', ''), kwargs.get('schema', {}))
        else:
            raise ValueError(f"Unknown action: {action}")


skill = DataProcessingSkill()


def get_skill_info() -> Dict[str, Any]:
    return {
        'name': skill.name,
        'version': skill.version,
        'description': skill.description,
        'actions': ['clean_data', 'transform_data', 'analyze_data', 'generate_insights', 'validate_data'],
        'capabilities': {
            'clean_data': {
                'description': 'Clean and normalize data',
                'parameters': {'data': 'string', 'format': 'string'}
            },
            'transform_data': {
                'description': 'Transform data based on rules',
                'parameters': {'data': 'string', 'transformation': 'object'}
            },
            'analyze_data': {
                'description': 'Analyze data with various methods',
                'parameters': {'data': 'string', 'analysis_type': 'string'}
            },
            'generate_insights': {
                'description': 'Generate insights from data using LLM',
                'parameters': {'data': 'string', 'question': 'string'}
            },
            'validate_data': {
                'description': 'Validate data against a schema',
                'parameters': {'data': 'string', 'schema': 'object'}
            }
        }
    }
