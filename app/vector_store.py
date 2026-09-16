"""
Vector Store for Complete Self System
ویکٹر اسٹور برائے خود کار نظام
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
                result = self.client.search(collection_name=self.collection_name, query_vector=qvec, limit=limit, with_payload=True)
                for record in result:
                    payload = record.payload
                    if kind and payload.get('kind') != kind:
                        continue
                    results.append({'id': str(record.id), 'text': payload.get('text', ''), 'score': float(record.score), 'metadata': {k: v for k, v in payload.items() if k != 'text'}})
            except:
                results = []
        if not results or self.backend == 'sqlite':
            sqlite_results = self._sqlite_search(query, limit, kind, qvec)
            existing_ids = {r['id'] for r in results}
            for r in sqlite_results:
                if r['id'] not in existing_ids:
                    results.append(r)
            results.sort(key=lambda x: x['score'], reverse=True)
            results = results[:limit]
        return results
    
    def _sqlite_search(self, query, limit, kind, qvec):
        rows = db.get_memories_by_dim(len(qvec))
        scored = []
        for row in rows:
            try:
                vec = json.loads(row.get('embedding', '[]'))
            except:
                continue
            if kind and row.get('kind') != kind:
                continue
            score = cosine_similarity(qvec, vec)
            if score >= 0.08:
                metadata = json.loads(row.get('metadata', '{}'))
                scored.append({'id': row.get('id'), 'text': row.get('text', ''), 'score': score, 'metadata': metadata})
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored[:limit]
    
    def delete(self, memory_id: str) -> bool:
        deleted = False
        cursor = db._execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        deleted = cursor.rowcount > 0
        if self.backend == 'chroma' and self.collection:
            try:
                self.collection.delete(ids=[memory_id])
            except:
                pass
        elif self.backend == 'qdrant':
            try:
                from qdrant_client.http import models
                self.client.delete(collection_name=self.collection_name, points_selector=models.PointIdsList(points=[memory_id]))
            except:
                pass
        return deleted
    
    def get_stats(self) -> Dict[str, Any]:
        stats = {'backend': self.backend, 'dimension': self.dimension, 'sqlite_count': 0}
        rows = db._query("SELECT COUNT(*) as count FROM memories")
        stats['sqlite_count'] = rows[0]['count'] if rows else 0
        if self.backend == 'chroma' and self.collection:
            try:
                stats['chroma_count'] = self.collection.count()
            except:
                stats['chroma_count'] = 0
        elif self.backend == 'qdrant':
            try:
                result = self.client.get_collection(self.collection_name)
                stats['qdrant_count'] = result.vectors_count
            except:
                stats['qdrant_count'] = 0
        return stats


def cosine_similarity(a, b):
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


vector_store = VectorStore()