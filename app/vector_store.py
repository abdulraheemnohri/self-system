"""
Vector Store for Complete Self System

Manages vector embeddings for memory and semantic search
"""

import uuid
import json
import math
from typing import List, Dict, Any, Optional
from .db import db
from .llm import embed_text
from .config import config


class VectorStore:
    def __init__(self):
        self.backend = config.get('memory.vector_backend', 'sqlite')
        self.collection = None
        self.dimension = 0
        if self.backend == 'chroma':
            self._init_chroma()
        elif self.backend == 'qdrant':
            self._init_qdrant()
    
    def _init_chroma(self):
        try:
            import chromadb
            client = chromadb.PersistentClient(path="storage/vector/chroma")
            self.collection = client.get_or_create_collection(name="self_system_memory", metadata={"hnsw:space": "cosine"})
            if self.collection.count() > 0:
                sample = self.collection.get(limit=1)
                if sample and 'embeddings' in sample:
                    self.dimension = len(sample['embeddings'][0])
        except:
            self.backend = 'sqlite'
    
    def _init_qdrant(self):
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            qdrant_url = config.get('memory.qdrant_url', 'http://localhost:6333')
            collection_name = config.get('memory.qdrant_collection', 'self_system')
            self.client = QdrantClient(url=qdrant_url)
            try:
                self.client.get_collection(collection_name)
            except:
                self.client.create_collection(collection_name=collection_name, vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE))
            self.collection_name = collection_name
        except:
            self.backend = 'sqlite'
    
    def _clean_metadata(self, metadata):
        return {str(k): str(v) for k, v in (metadata or {}).items()}
    
    def add(self, text: str, kind: str = "note", metadata: Optional[Dict] = None) -> Optional[str]:
        text = str(text or "").strip()
        if not text:
            return None
        memory_id = str(uuid.uuid4())
        embedding = embed_text(text)
        if not embedding:
            return None
        self.dimension = len(embedding)
        db.add_memory(text=text, kind=kind, embedding=embedding, dim=self.dimension, metadata=metadata)
        if self.backend == 'chroma' and self.collection:
            try:
                self.collection.add(ids=[memory_id], embeddings=[embedding], documents=[text], metadatas=[self._clean_metadata(metadata or {})])
            except:
                pass
        elif self.backend == 'qdrant':
            try:
                from qdrant_client.http import models
                self.client.upsert(collection_name=self.collection_name, points=models.Batch(ids=[memory_id], vectors=[embedding], payloads=[{'text': text, 'kind': kind, **self._clean_metadata(metadata or {})}]))
            except:
                pass
        return memory_id
    
    def search(self, query: str, limit: int = 5, kind: Optional[str] = None) -> List[Dict[str, Any]]:
        query = str(query or "").strip()
        if not query:
            return []
        qvec = embed_text(query)
        if not qvec:
            return []
        results = []
        if self.backend == 'chroma' and self.collection:
            try:
                result = self.collection.query(query_embeddings=[qvec], n_results=limit)
                ids = result.get('ids', [[]])[0]
                docs = result.get('documents', [[]])[0]
                distances = result.get('distances', [[]])[0]
                metas = result.get('metadatas', [[]])[0]
                for i, memory_id in enumerate(ids):
                    if i >= len(distances):
                        continue
                    score = max(0.0, 1.0 - float(distances[i]))
                    if kind and metas[i].get('kind') != kind:
                        continue
                    results.append({'id': memory_id, 'text': docs[i] if i < len(docs) else '', 'score': score, 'metadata': metas[i] if i < len(metas) else {}})
            except:
                results = []
        elif self.backend == 'qdrant':
            try:
                from qdrant_client.http import models
                result = self.client.search(collection_name=self.collection_name, query_vector=qvec, limit=limit)
                for item in result:
                    score = item.score
                    if kind and item.payload.get('kind') != kind:
                        continue
                    results.append({'id': item.id, 'text': item.payload.get('text', ''), 'score': score, 'metadata': item.payload})
            except:
                results = []
        if not results:
            memories = db.get_memories_by_dim(self.dimension, limit * 10)
            for mem in memories:
                if kind and mem.get('kind') != kind:
                    continue
                try:
                    emb = json.loads(mem['embedding'])
                    if len(emb) != len(qvec):
                        continue
                    score = self._cosine_similarity(emb, qvec)
                    results.append({'id': mem['id'], 'text': mem['text'], 'score': score, 'metadata': json.loads(mem['metadata']) if mem['metadata'] else {}})
                except:
                    continue
                if len(results) >= limit:
                    break
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        try:
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))
            if norm_a == 0 or norm_b == 0:
                return 0.0
            return max(0.0, min(1.0, dot / (norm_a * norm_b)))
        except:
            return 0.0
    
    def delete(self, memory_id: str) -> bool:
        try:
            if self.backend == 'chroma' and self.collection:
                self.collection.delete(ids=[memory_id])
            elif self.backend == 'qdrant':
                self.client.delete(collection_name=self.collection_name, points=[memory_id])
            return True
        except:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        stats = {'backend': self.backend, 'dimension': self.dimension}
        if self.backend == 'chroma' and self.collection:
            stats['count'] = self.collection.count()
        elif self.backend == 'qdrant':
            try:
                info = self.client.get_collection(self.collection_name)
                stats['count'] = info.vectors_count
            except:
                stats['count'] = 0
        else:
            stats['count'] = 0
        return stats


vector_store = VectorStore()
