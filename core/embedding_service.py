"""
EmbeddingService - Handles text embedding generation for SupaBrain
Extracted from memory_engine.py as part of refactoring (TODO #191a Phase 2.1)
"""

import os
import logging
import numpy as np
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from typing import Optional

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text embeddings using SentenceTransformer"""
    
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None) -> None:
        """
        Initialize EmbeddingService
        
        Args:
            model_name: Name of the sentence-transformers model (defaults to env var)
            device: Device to run on ('cpu', 'cuda', etc.) (defaults to env var)
        """
        self.model: Optional[SentenceTransformer] = None
        self.model_name: str = model_name or os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.device: str = device or os.getenv("DEVICE", "cpu")
        
    def initialize(self) -> None:
        """Lazy-load the embedding model (call this before first use)"""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name} on {self.device}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            
    @lru_cache(maxsize=1000)
    def _cached_encode(self, text: str) -> tuple:
        """
        Cache wrapper for embedding generation (LRU cache requires hashable types)
        Returns tuple instead of numpy array for caching
        """
        if self.model is None:
            self.initialize()
        embedding = self.model.encode(text, convert_to_numpy=True)
        return tuple(embedding.tolist())
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for text (cached for performance)
        
        Args:
            text: Input text to embed
            
        Returns:
            numpy array with embedding vector
        """
        # Use cached version and convert back to numpy
        cached_tuple = self._cached_encode(text)
        return np.array(cached_tuple, dtype=np.float32)
    
    def generate_embeddings_batch(self, texts: list[str]) -> list[np.ndarray]:
        """
        Generate embeddings for multiple texts in one batch (faster than sequential)
        
        Args:
            texts: List of input texts to embed
            
        Returns:
            List of numpy arrays with embedding vectors
        """
        if self.model is None:
            self.initialize()
        # Batch encoding is significantly faster than encoding one-by-one
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return [emb for emb in embeddings]  # Convert to list of arrays
