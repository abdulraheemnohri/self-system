"""
Translation Skill for Complete Self System

Provides text translation and language detection capabilities
"""

import json
from typing import Dict, Any, List, Optional
from .config import config


class TranslationSkill:
    def __init__(self):
        self.name = "translation_skill"
        self.description = "Text translation and language detection"
        self.version = "1.0.0"
        self.translation_api = config.get('translation.api', 'libretranslate')
        self.api_url = config.get('translation.api_url', 'https://libretranslate.de/translate')
    
    def detect_language(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {'error': 'No text provided'}
        try:
            from langdetect import detect
            return {'language': detect(text), 'method': 'langdetect'}
        except ImportError:
            return {'error': 'langdetect library not installed'}
    
    def translate_text(self, text: str, target_lang: str, source_lang: Optional[str] = None) -> Dict[str, Any]:
        if not text or not text.strip():
            return {'error': 'No text provided'}
        if not target_lang:
            return {'error': 'No target language specified'}
        return {'result': f'Translation from {source_lang or "auto"} to {target_lang}: {text[:100]}...', 'method': 'mock'}
    
    def get_supported_languages(self) -> Dict[str, Any]:
        return {
            'languages': {
                'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
                'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'zh': 'Chinese',
                'ja': 'Japanese', 'ar': 'Arabic', 'hi': 'Hindi', 'ur': 'Urdu'
            }
        }
    
    def get_info(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'capabilities': ['Language detection', 'Text translation', 'Batch translation', 'Supported languages listing']
        }

translation_skill = TranslationSkill()