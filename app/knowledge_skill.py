"""
Knowledge Skill for Complete Self System

Provides knowledge management, search, and retrieval capabilities
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from .db import db


class KnowledgeSkill:
    def __init__(self):
        self.name = "knowledge_skill"
        self.description = "Knowledge management, search, and retrieval"
        self.version = "1.0.0"
    
    def add_knowledge(self, title: str, content: str, category: str = "general", tags: Optional[List[str]] = None) -> Dict[str, Any]:
        if not title or not title.strip():
            return {'error': 'Title is required'}
        if not content or not content.strip():
            return {'error': 'Content is required'}
        try:
            knowledge_id = db.add_knowledge(title=title.strip(), content=content.strip(), category=category.strip() if category else "general", metadata={'tags': tags or [], 'created_by': 'knowledge_skill', 'timestamp': datetime.now().isoformat()})
            return {'success': True, 'knowledge_id': knowledge_id, 'title': title, 'category': category, 'timestamp': datetime.now().isoformat()}
        except Exception as e:
            return {'error': f'Failed to add knowledge: {str(e)}'}
    
    def search_knowledge(self, query: str, limit: int = 10) -> Dict[str, Any]:
        if not query or not query.strip():
            return {'error': 'Query is required'}
        try:
            results = db.search_knowledge(query, limit=limit)
            return {'results': results, 'count': len(results), 'query': query}
        except Exception as e:
            return {'error': f'Search failed: {str(e)}'}
    
    def get_info(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'capabilities': ['Add and manage knowledge entries', 'Search knowledge', 'List and filter knowledge', 'Get knowledge statistics']
        }

knowledge_skill = KnowledgeSkill()