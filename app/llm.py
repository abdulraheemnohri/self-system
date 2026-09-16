"""
LLM Client for Complete Self System

Handles all LLM interactions including chat and embeddings
"""

import time
import requests
from typing import List, Dict, Any, Optional
from .config import config


class LLMClient:
    def __init__(self):
        self.base_url = config.get('provider.base_url', 'http://localhost:11434/v1')
        self.api_key = config.get('provider.api_key', '')
        self.model = config.get('provider.model', 'llama3.1')
        self.timeout = 120
        self.max_retries = 3
        self.retry_delay = 1
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            if 'openai' in self.base_url or 'openrouter' in self.base_url:
                headers['Authorization'] = f'Bearer {self.api_key}'
            elif self.api_key != 'ollama':
                headers['Authorization'] = f'Bearer {self.api_key}'
        return headers
    
    def _make_request(self, endpoint: str, payload: Dict[str, Any], max_tokens: int = 4096, temperature: float = 0.7) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}{endpoint}"
        request_payload = {'model': self.model, 'max_tokens': max_tokens, 'temperature': temperature, **payload}
        headers = self._get_headers()
        for attempt in range(self.max_retries):
            try:
                response = requests.post(url, headers=headers, json=request_payload, timeout=self.timeout)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                elif response.status_code == 401:
                    raise ValueError(f"Authentication failed. Status: {response.status_code}")
                else:
                    raise ValueError(f"API request failed. Status: {response.status_code}")
            except requests.exceptions.Timeout:
                if attempt == self.max_retries - 1:
                    raise ValueError(f"Request timed out after {self.timeout} seconds")
                time.sleep(self.retry_delay * (attempt + 1))
        return None
    
    def chat(self, messages: List[Dict[str, Any]], max_tokens: int = 4096, temperature: float = 0.7, stream: bool = False) -> Optional[str]:
        response = self._make_request('/chat/completions', {'messages': messages, 'stream': stream}, max_tokens, temperature)
        if response and 'choices' in response:
            return response['choices'][0]['message']['content']
        return None
    
    def embed(self, text: str, model: Optional[str] = None) -> List[float]:
        use_api_embeddings = config.get('provider.use_api_embeddings', True)
        if not use_api_embeddings:
            return self._local_embed(text)
        embedding_model = model or config.get('provider.embedding_model', 'text-embedding-3-small')
        if 'ollama' in self.base_url:
            return self._ollama_embed(text, embedding_model)
        response = self._make_request('/embeddings', {'model': embedding_model, 'input': text})
        if response and 'data' in response:
            return response['data'][0]['embedding']
        return self._local_embed(text)
    
    def _ollama_embed(self, text: str, model: str) -> List[float]:
        try:
            url = f"{self.base_url}/embeddings"
            payload = {'model': model, 'prompt': text}
            headers = self._get_headers()
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
            if response.status_code == 200:
                return response.json().get('embedding', [])
        except:
            pass
        return self._local_embed(text)
    
    def _local_embed(self, text: str) -> List[float]:
        try:
            from sentence_transformers import SentenceTransformer
            model_name = 'all-MiniLM-L6-v2'
            if not hasattr(self, '_embedding_model'):
                self._embedding_model = SentenceTransformer(model_name)
            embedding = self._embedding_model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except ImportError:
            import hashlib
            h = hashlib.sha256(text.encode('utf-8')).hexdigest()
            return [float((int(h[i:i+2], 16) / 255.0) * 2 - 1) for i in range(0, 32, 2)]
        except Exception:
            return [0.0] * 384
    
    def check_health(self) -> Dict[str, Any]:
        try:
            test_messages = [{'role': 'user', 'content': 'Say OK'}]
            response = self.chat(test_messages, max_tokens=5, temperature=0)
            if response and 'OK' in response:
                return {'healthy': True, 'model': self.model, 'base_url': self.base_url}
            return {'healthy': False, 'error': f"Unexpected response: {response}", 'model': self.model, 'base_url': self.base_url}
        except Exception as e:
            return {'healthy': False, 'error': str(e), 'model': self.model, 'base_url': self.base_url}


llm_client = LLMClient()

def simple_llm_reply(messages: List[Dict[str, Any]], max_tokens: int = 4096, temperature: float = 0.7) -> str:
    return llm_client.chat(messages, max_tokens, temperature) or ""

def embed_text(text: str) -> List[float]:
    return llm_client.embed(text)
