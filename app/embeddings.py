"""
Embeddings Module for Complete Allostatic Self System
امبیڈنگز ماڈیول - ٹیکسٹ کو ویکٹر میں بدلنا

This module provides text embedding functionality.
"""

import json
import time
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from .config import get_config

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result from embedding generation"""
    text: str
    embedding: Optional[np.ndarray] = None
    dimension: int = 0
    model: str = ""
    time_taken: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "text": self.text,
            "embedding": self.embedding.tolist() if self.embedding is not None else None,
            "dimension": self.dimension,
            "model": self.model,
            "time_taken": self.time_taken
        }


class Embeddings:
    """Manages text embeddings"""
    
    def __init__(self):
        self.config = get_config()
        self.embedding_model = self.config.get_setting("llm.embedding_model", "nomic-embed-text")
        self.dimension = self._get_dimension()
        self._cache: Dict[str, np.ndarray] = {}
        self._last_used: Dict[str, float] = {}
