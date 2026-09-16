"""
Vector Store for Complete Self System
ویکٹر اسٹور
"""

import json
import math
import uuid
import hashlib
import re
from typing import List, Dict, Any, Optional
from .db import Database
from .llm import get_llm_client


class VectorStore:
    """Vector storage with SQLite backend"""
    
    def __init__(self, db):
        self.db = db
        self.llm = get_llm_client()
        self.backend = "sqlite"
    
    def get_embedding(self, text):
        embedding = self.llm.get_embedding(text)
        if embedding:
            return embedding
        return self._fallback_embed(text)
    
    def _fallback_embed(self, text, dim=256):
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
    
    @staticmethod
    def cosine_similarity(a, b):
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
    
    def add_memory(self, text, kind="note", metadata=None):
        text = str(text or "").strip()
        if not text:
            return None
        embedding = self.get_embedding(text)
        dim = len(embedding)
        metadata = metadata or {}
        metadata["kind"] = kind
        return self.db.add_memory(text=text, kind=kind, metadata=metadata, embedding=embedding, dim=dim)
    
    def search_memory(self, query, limit=5, threshold=0.08):
        query = str(query or "").strip()
        if not query:
            return []
        qvec = self.get_embedding(query)
        rows = self.db.get_memories_by_dim(len(qvec))
        scored = []
        for row in rows:
            try:
                vec = json.loads(row.get("embedding", "[]"))
            except Exception:
                continue
            if not vec:
                continue
            score = self.cosine_similarity(qvec, vec)
            if score >= threshold:
                scored.append({"score": score, "text": row.get("text", ""), "kind": row.get("kind", ""), "metadata": json.loads(row.get("metadata", "{}")), "id": row.get("id", "")})
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]
    
    def remember_fact(self, key, value):
        text = f"{key} = {value}"
        return self.add_memory(text, kind="fact", metadata={"key": key, "value": value})
    
    def remember_note(self, text, tags=""):
        return self.add_memory(text, kind="note", metadata={"tags": tags})
    
    def remember_knowledge(self, question, answer):
        text = f"Q: {question}\nA: {answer}"
        return self.add_memory(text, kind="knowledge", metadata={"question": question})
    
    def cleanup_memories(self):
        self.db.cleanup_memories()