"""Embedding generation with caching for RAG pipeline."""

import hashlib
import time

import numpy as np  # type: ignore
from sentence_transformers import SentenceTransformer  # type: ignore


class EmbeddingsCache:
    """Simple in-memory cache for embeddings with TTL."""

    def __init__(self, ttl: int = 600):
        """Initialize cache.

        Args:
            ttl: Time-to-live in seconds (default: 600s = 10 minutes)
        """
        self.ttl = ttl
        self._cache: dict[str, tuple[np.ndarray, float]] = {}

    def _get_key(self, text: str) -> str:
        """Generate cache key from text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, text: str) -> np.ndarray | None:
        """Get embedding from cache if not expired.

        Args:
            text: Text to look up

        Returns:
            Cached embedding or None if not found/expired
        """
        key = self._get_key(text)
        if key not in self._cache:
            return None

        embedding, timestamp = self._cache[key]
        if time.time() - timestamp > self.ttl:
            # Expired, remove from cache
            del self._cache[key]
            return None

        return embedding

    def set(self, text: str, embedding: np.ndarray) -> None:
        """Store embedding in cache.

        Args:
            text: Text key
            embedding: Embedding to cache
        """
        key = self._get_key(text)
        self._cache[key] = (embedding, time.time())

    def clear(self) -> None:
        """Clear all cached embeddings."""
        self._cache.clear()

    def size(self) -> int:
        """Get number of cached embeddings."""
        return len(self._cache)


class Embedder:
    """Embedding generator using sentence-transformers."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        cache_ttl: int = 600,
    ):
        """Initialize embedder.

        Args:
            model_name: Name of sentence-transformers model (default: all-MiniLM-L6-v2)
            cache_ttl: Cache TTL in seconds (default: 600s)
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.cache = EmbeddingsCache(ttl=cache_ttl)

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding as list of floats
        """
        # Check cache first
        cached = self.cache.get(text)
        if cached is not None:
            return list(cached.tolist())

        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)

        # Cache it
        self.cache.set(text, embedding)

        return list(embedding.tolist())

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Generate embeddings for a batch of texts.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for encoding (default: 32)

        Returns:
            List of embeddings
        """
        embeddings: list[list[float]] = []
        uncached_texts: list[str] = []
        uncached_indices: list[int] = []

        # Check cache for each text
        for i, text in enumerate(texts):
            cached = self.cache.get(text)
            if cached is not None:
                embeddings.append(cached.tolist())
            else:
                embeddings.append([])  # Placeholder
                uncached_texts.append(text)
                uncached_indices.append(i)

        # Generate embeddings for uncached texts
        if uncached_texts:
            new_embeddings = self.model.encode(
                uncached_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
            )

            # Cache and insert new embeddings
            for i, (text, embedding) in enumerate(zip(uncached_texts, new_embeddings)):
                self.cache.set(text, embedding)
                embeddings[uncached_indices[i]] = embedding.tolist()

        return embeddings

    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        dim = self.model.get_sentence_embedding_dimension()
        return int(dim) if dim is not None else 384
