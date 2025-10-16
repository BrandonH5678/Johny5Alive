#!/usr/bin/env python3
"""
Embedding Cache - Strategic Principle 9

Caches embeddings to avoid recomputation and optimize local LLM usage.
"""

from typing import Dict, Optional, List
import json
from pathlib import Path
import hashlib


class EmbeddingCache:
    """
    Strategic Principle 9: Local LLM Optimization

    Don't recompute what you've seen before.
    """

    def __init__(self, cache_dir: str = "cache/embeddings"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "cache.json"
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load cache from disk"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_cache(self):
        """Save cache to disk"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def _hash_text(self, text: str) -> str:
        """Generate hash of text"""
        return hashlib.sha256(text.encode()).hexdigest()

    def get(self, text: str) -> Optional[List[float]]:
        """
        Get cached embedding if available

        Args:
            text: Text to get embedding for

        Returns:
            Cached embedding or None
        """
        text_hash = self._hash_text(text)
        return self.cache.get(text_hash)

    def put(self, text: str, embedding: List[float]):
        """
        Store embedding in cache

        Args:
            text: Text being embedded
            embedding: Computed embedding vector
        """
        text_hash = self._hash_text(text)
        self.cache[text_hash] = embedding
        self._save_cache()

    def get_or_compute(self, text: str, compute_fn) -> List[float]:
        """
        Get cached embedding or compute if not cached

        Args:
            text: Text to embed
            compute_fn: Function to compute embedding if not cached

        Returns:
            Embedding vector
        """
        cached = self.get(text)
        if cached is not None:
            return cached

        # Compute and cache
        embedding = compute_fn(text)
        self.put(text, embedding)
        return embedding

    def clear(self):
        """Clear cache"""
        self.cache = {}
        self._save_cache()
