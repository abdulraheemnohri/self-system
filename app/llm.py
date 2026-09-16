"""
LLM API Client for Complete Self System
LLM API کلائنٹ
"""

import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from .config import get_config


class LLMClient:
    """Client for interacting with LLM APIs"""
    
    def __init__(self):
        self.cfg = get_config()
    
    def get_base_url(self):
        return str(self.cfg.get("provider", "base_url") or "").strip().rstrip("/")
    
    def get_api_key(self):
        return str(self.cfg.get("provider", "api_key") or "").strip()
    
    def get_model(self):
        return str(self.cfg.get("provider", "model") or "gpt-4o-mini").strip()
    
    def get_embedding_model(self):
        return str(self.cfg.get("provider", "embedding_model") or "text-embedding-3-small").strip()
    
    def call_chat_api(self, messages, tools=None, temperature=None, max_tokens=None):
        base_url = self.get_base_url()
        if not base_url:
            return {"_error": "[API error] base_url is empty"}
        
        url = base_url
        if not url.endswith("/chat/completions"):
            url = url + "/chat/completions"
        
        payload = {"model": self.get_model(), "messages": messages}
        
        if temperature is None:
            temperature = float(self.cfg.get("agent", "temperature") or 0.2)
        payload["temperature"] = temperature
        
        if max_tokens is None:
            max_tokens = int(self.cfg.get("agent", "max_tokens") or 1200)
        payload["max_tokens"] = max_tokens
        
        if tools and self.cfg.get("agent", "enable_tool_calls", True):
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        headers = {"Content-Type": "application/json"}
        api_key = self.get_api_key()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        
        try:
            timeout = int(self.cfg.get("provider", "timeout") or 90)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                return json.loads(body)
        except urllib.error.HTTPError as exc:
            return {"_error": f"[API HTTP {exc.code}] {str(exc)}"}
        except Exception as exc:
            return {"_error": f"[API error] {exc}"}
    
    def get_embedding(self, text):
        base_url = self.get_base_url()
        model = self.get_embedding_model()
        api_key = self.get_api_key()
        
        if not base_url or not model:
            return None
        
        url = base_url + "/embeddings"
        payload = {"model": model, "input": str(text)[:8000]}
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        
        try:
            timeout = int(self.cfg.get("provider", "timeout") or 60)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                result = json.loads(body)
                return result["data"][0]["embedding"]
        except Exception:
            return None
    
    def simple_chat(self, messages, use_tools=False):
        result = self.call_chat_api(messages, tools=None if not use_tools else None)
        if "_error" in result:
            return result["_error"]
        if "choices" in result and len(result["choices"]) > 0:
            message = result["choices"][0]["message"]
            if isinstance(message, dict):
                return message.get("content", "") or ""
        return ""


llm_client = LLMClient()

def get_llm_client():
    return llm_client