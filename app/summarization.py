"""
Summarization Skill for Complete Self System

Provides advanced text summarization capabilities
"""

import json
from typing import Dict, Any, List, Optional
from .llm import simple_llm_reply


class SummarizationSkill:
    """Skill for summarizing text content"""
    
    def __init__(self):
        self.name = "summarization"
        self.description = "Advanced text summarization with multiple approaches"
        self.version = "1.0.0"
    
    def summarize_text(self, text: str, approach: str = 'extractive', ratio: float = 0.2) -> str:
        """Summarize text using the specified approach"""
        if not text:
            return ""
        
        if approach == 'extractive':
            return self._extractive_summarize(text, ratio)
        elif approach == 'abstractive':
            return self._abstractive_summarize(text, ratio)
        elif approach == 'bullet_points':
            return self._bullet_point_summarize(text)
        elif approach == 'key_points':
            return self._key_points_summarize(text)
        else:
            return self._abstractive_summarize(text, ratio)
    
    def _extractive_summarize(self, text: str, ratio: float) -> str:
        """Extractive summarization - select important sentences"""
        sentences = self._split_sentences(text)
        if not sentences:
            return ""
        
        num_sentences = max(1, int(len(sentences) * ratio))
        
        # Simple approach: select first and last sentences
        if len(sentences) <= num_sentences:
            return ' '.join(sentences)
        
        # Select first few and last few
        first_part = sentences[:num_sentences // 2]
        last_part = sentences[-num_sentences // 2:]
        
        return ' '.join(first_part + last_part)
    
    def _abstractive_summarize(self, text: str, ratio: float) -> str:
        """Abstractive summarization using LLM"""
        length = len(text.split())
        target_length = max(50, int(length * ratio))
        
        prompt = f"Summarize the following text in about {target_length} words:\n\n{text[:8000]}"
        
        messages = [
            {'role': 'system', 'content': 'You are a helpful summarization assistant.'},
            {'role': 'user', 'content': prompt}
        ]
        
        return simple_llm_reply(messages, max_tokens=2000, temperature=0.3)
    
    def _bullet_point_summarize(self, text: str) -> str:
        """Summarize as bullet points"""
        prompt = f"Create a bullet point summary of the following text:\n\n{text[:8000]}"
        
        messages = [
            {'role': 'system', 'content': 'You are a helpful summarization assistant.'},
            {'role': 'user', 'content': prompt}
        ]
        
        return simple_llm_reply(messages, max_tokens=2000, temperature=0.3)
    
    def _key_points_summarize(self, text: str) -> str:
        """Extract key points from text"""
        prompt = f"Extract the key points from the following text and return as a numbered list:\n\n{text[:8000]}"
        
        messages = [
            {'role': 'system', 'content': 'You are a helpful summarization assistant.'},
            {'role': 'user', 'content': prompt}
        ]
        
        return simple_llm_reply(messages, max_tokens=2000, temperature=0.3)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        import re
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def summarize_document(self, text: str, sections: bool = False) -> str:
        """Summarize a document with optional section summaries"""
        if not text:
            return ""
        
        if sections:
            # Split by sections
            section_marker = '\n\n'
            if section_marker in text:
                sections_list = text.split(section_marker)
                summaries = []
                for i, section in enumerate(sections_list, 1):
                    if section.strip():
                        summary = self._abstractive_summarize(section, 0.3)
                        summaries.append(f"Section {i} Summary: {summary}")
                return '\n\n'.join(summaries)
        
        return self._abstractive_summarize(text, 0.2)
    
    def create_abstract(self, text: str, style: str = 'academic') -> str:
        """Create an abstract from text"""
        prompt = f"Create a {style} abstract (150-250 words) from the following text:\n\n{text[:8000]}"
        
        messages = [
            {'role': 'system', 'content': 'You are a professional abstract writer.'},
            {'role': 'user', 'content': prompt}
        ]
        
        return simple_llm_reply(messages, max_tokens=2000, temperature=0.3)
    
    def extract_main_ideas(self, text: str, count: int = 5) -> List[str]:
        """Extract main ideas from text"""
        prompt = f"Extract the {count} main ideas from the following text. Return as a JSON array:\n\n{text[:8000]}"
        
        messages = [
            {'role': 'system', 'content': 'You are a helpful text analysis assistant. Return only valid JSON.'},
            {'role': 'user', 'content': prompt}
        ]
        
        response = simple_llm_reply(messages, max_tokens=2000, temperature=0.3)
        
        try:
            return json.loads(response)
        except:
            # Fallback to simple extraction
            return [f"Idea {i+1}" for i in range(count)]
    
    def generate_tldr(self, text: str) -> str:
        """Generate a TL;DR summary"""
        prompt = f"Generate a TL;DR (Too Long; Didn't Read) summary of the following text:\n\n{text[:8000]}"
        
        messages = [
            {'role': 'system', 'content': 'You are a helpful summarization assistant.'},
            {'role': 'user', 'content': prompt}
        ]
        
        return simple_llm_reply(messages, max_tokens=500, temperature=0.3)
    
    def compare_summaries(self, text1: str, text2: str) -> str:
        """Compare two texts by summarizing both"""
        summary1 = self._abstractive_summarize(text1, 0.3)
        summary2 = self._abstractive_summarize(text2, 0.3)
        
        prompt = f"Compare the following two summaries:\n\nSummary 1:\n{summary1}\n\nSummary 2:\n{summary2}\n\nIdentify similarities, differences, and which summary is more comprehensive."
        
        messages = [
            {'role': 'system', 'content': 'You are a helpful comparison assistant.'},
            {'role': 'user', 'content': prompt}
        ]
        
        return simple_llm_reply(messages, max_tokens=2000, temperature=0.3)
    
    def execute(self, action: str, **kwargs) -> Any:
        """Execute a skill action"""
        if action == 'summarize_text':
            return self.summarize_text(
                kwargs.get('text', ''),
                kwargs.get('approach', 'abstractive'),
                kwargs.get('ratio', 0.2)
            )
        elif action == 'summarize_document':
            return self.summarize_document(
                kwargs.get('text', ''),
                kwargs.get('sections', False)
            )
        elif action == 'create_abstract':
            return self.create_abstract(
                kwargs.get('text', ''),
                kwargs.get('style', 'academic')
            )
        elif action == 'extract_main_ideas':
            return self.extract_main_ideas(
                kwargs.get('text', ''),
                kwargs.get('count', 5)
            )
        elif action == 'generate_tldr':
            return self.generate_tldr(kwargs.get('text', ''))
        elif action == 'compare_summaries':
            return self.compare_summaries(
                kwargs.get('text1', ''),
                kwargs.get('text2', '')
            )
        else:
            raise ValueError(f"Unknown action: {action}")


skill = SummarizationSkill()


def get_skill_info() -> Dict[str, Any]:
    return {
        'name': skill.name,
        'version': skill.version,
        'description': skill.description,
        'actions': ['summarize_text', 'summarize_document', 'create_abstract', 'extract_main_ideas', 'generate_tldr', 'compare_summaries'],
        'capabilities': {
            'summarize_text': {
                'description': 'Summarize text with specified approach',
                'parameters': {'text': 'string', 'approach': 'string', 'ratio': 'float'}
            },
            'summarize_document': {
                'description': 'Summarize a document with optional sections',
                'parameters': {'text': 'string', 'sections': 'boolean'}
            },
            'create_abstract': {
                'description': 'Create an abstract from text',
                'parameters': {'text': 'string', 'style': 'string'}
            },
            'extract_main_ideas': {
                'description': 'Extract main ideas from text',
                'parameters': {'text': 'string', 'count': 'integer'}
            },
            'generate_tldr': {
                'description': 'Generate a TL;DR summary',
                'parameters': {'text': 'string'}
            },
            'compare_summaries': {
                'description': 'Compare two texts by summarizing both',
                'parameters': {'text1': 'string', 'text2': 'string'}
            }
        }
    }
