#!/usr/bin/env python3
"""
LLM Client for Complete Self System

Provides:
- LLM API client (OpenAI-compatible)
- Embedding generation
- Fallback embeddings
- API health checking
"""

import os
import json
import time
import hashlib
import math
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple


class Embedder:
    """
    Generate embeddings for text using API or fallback methods.
    
    Supports:
    - API-based embeddings (OpenAI, Ollama, etc.)
    - Fallback hash-based embeddings
    - Normalization
    """
    
    def __init__(self, cfg: Dict[str, Any]):
        """
        Initialize the Embedder.
        
        Args:
            cfg: Configuration dictionary
        """
        self.cfg = cfg
    
    def embed(self, text: str) -> List[float]:
        """
        Generate an embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        text = str(text or "")
        
        if self.cfg.get("provider.use_api_embeddings", True):
            api_embedding = self.api_embed(text)
            if api_embedding:
                return api_embedding
        
        return self.fallback_embed(text)
    
    def api_embed(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding using API.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None
        """
        base_url = str(self.cfg.get("provider.base_url", "")).strip().rstrip("/")
        model = str(self.cfg.get("provider.embedding_model", "")).strip()
        api_key = str(self.cfg.get("provider.api_key", "")).strip()
        
        if not base_url or not model:
            return None
        
        url = base_url
        if not url.endswith("/embeddings"):
            url = url + "/embeddings"
        
        payload = {
            "model": model,
            "input": text[:8000],
        }
        
        headers = {
            "Content-Type": "application/json",
        }
        
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        
        try:
            timeout = int(self.cfg.get("provider.timeout", 60))
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                result = json.loads(body)
                return result["data"][0]["embedding"]
        except Exception:
            return None
    
    def fallback_embed(self, text: str) -> List[float]:
        """
        Generate a fallback embedding using hash-based method.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        import re
        
        dim = int(self.cfg.get("memory.embedding_dim_fallback", 256))
        vec = [0.0] * dim
        
        tokens = re.findall(r"\w+", str(text).lower())
        if not tokens:
            return vec
        
        for i, token in enumerate(tokens):
            h = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            idx = h % dim
            vec[idx] += 1.0
            
            if i + 1 < len(tokens):
                bigram = token + "_" + tokens[i + 1]
                h2 = int(hashlib.sha256(bigram.encode("utf-8")).hexdigest(), 16)
                idx2 = h2 % dim
                vec[idx2] += 0.5
        
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        
        return vec


class LLMClient:
    """
    LLM API client for OpenAI-compatible APIs.
    
    Supports:
    - Chat completions
    - Tool calling
    - Embeddings
    - Health checking
    """
    
    def __init__(self, cfg: Dict[str, Any]):
        """
        Initialize the LLM client.
        
        Args:
            cfg: Configuration dictionary
        """
        self.cfg = cfg
        self.embedder = Embedder(cfg)
    
    def call_chat_api_raw(self, messages: List[Dict[str, Any]], 
                          tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Call the chat API with raw response.
        
        Args:
            messages: List of message dictionaries
            tools: Optional list of tool schemas
            
        Returns:
            API response dictionary
        """
        base_url = str(self.cfg.get("provider.base_url", "")).strip().rstrip("/")
        
        if not base_url:
            return {"_error": "[API error] base_url is empty."}
        
        url = base_url
        if not url.endswith("/chat/completions"):
            url = url + "/chat/completions"
        
        payload = {
            "model": self.cfg.get("provider.model", "gpt-4o-mini"),
            "messages": messages,
            "temperature": float(self.cfg.get("provider.temperature", 0.2)),
        }
        
        if self.cfg.get("provider.max_tokens"):
            payload["max_tokens"] = int(self.cfg.get("provider.max_tokens", 2000))
        
        if tools and self.cfg.get("agent.enable_tool_calls", True):
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        api_key = str(self.cfg.get("provider.api_key", "")).strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        
        try:
            timeout = int(self.cfg.get("provider.timeout", 90))
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
                result = json.loads(body)
                return result["choices"][0]["message"]
        
        except urllib.error.HTTPError as exc:
            try:
                err_body = exc.read().decode("utf-8", errors="ignore")
            except Exception:
                err_body = str(exc)
            return {"_error": f"[API HTTP {exc.code}] {err_body[:800]}"}
        
        except Exception as exc:
            return {"_error": f"[API error] {exc}"}
    
    def simple_llm_reply(self, messages: List[Dict[str, Any]]) -> str:
        """
        Get a simple LLM reply without tool calling.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            LLM response text
        """
        message = self.call_chat_api_raw(messages, tools=None)
        if "_error" in message:
            return message["_error"]
        return message.get("content", "") or ""
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate an embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        return self.embedder.embed(text)
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check if the LLM API is healthy.
        
        Returns:
            Health status dictionary
        """
        try:
            messages = [{"role": "user", "content": "Reply with OK."}]
            reply = self.simple_llm_reply(messages)
            
            if reply and "OK" in reply.upper():
                return {
                    "healthy": True,
                    "model": self.cfg.get("provider.model", "unknown"),
                    "base_url": self.cfg.get("provider.base_url", "unknown")
                }
            else:
                return {
                    "healthy": False,
                    "error": f"Unexpected response: {reply}",
                    "model": self.cfg.get("provider.model", "unknown"),
                    "base_url": self.cfg.get("provider.base_url", "unknown")
                }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "model": self.cfg.get("provider.model", "unknown"),
                "base_url": self.cfg.get("provider.base_url", "unknown")
            }


def call_chat_api_raw(cfg: Dict[str, Any], messages: List[Dict[str, Any]], 
                      tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Call the chat API with raw response (standalone function).
    
    Args:
        cfg: Configuration dictionary
        messages: List of message dictionaries
        tools: Optional list of tool schemas
        
    Returns:
        API response dictionary
    """
    client = LLMClient(cfg)
    return client.call_chat_api_raw(messages, tools)


def simple_llm_reply(cfg: Dict[str, Any], messages: List[Dict[str, Any]]) -> str:
    """
    Get a simple LLM reply (standalone function).
    
    Args:
        cfg: Configuration dictionary
        messages: List of message dictionaries
        
    Returns:
        LLM response text
    """
    client = LLMClient(cfg)
    return client.simple_llm_reply(messages)


def embed_text(cfg: Dict[str, Any], text: str) -> List[float]:
    """
    Generate an embedding for text (standalone function).
    
    Args:
        cfg: Configuration dictionary
        text: Text to embed
        
    Returns:
        Embedding vector
    """
    client = LLMClient(cfg)
    return client.embed_text(text)
