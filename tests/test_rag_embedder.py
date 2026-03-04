"""Tests for RAG embedder."""

import time

from redis_agent_control_plane.rag.embedder import Embedder, EmbeddingsCache


def test_embeddings_cache():
    """Test embeddings cache."""
    cache = EmbeddingsCache(ttl=1)

    # Test cache miss
    assert cache.get("test") is None

    # Test cache set and get
    import numpy as np

    embedding = np.array([1.0, 2.0, 3.0])
    cache.set("test", embedding)
    cached = cache.get("test")
    assert cached is not None
    assert np.array_equal(cached, embedding)

    # Test cache expiration
    time.sleep(1.1)
    assert cache.get("test") is None

    # Test cache size
    cache.set("test1", embedding)
    cache.set("test2", embedding)
    assert cache.size() == 2

    # Test cache clear
    cache.clear()
    assert cache.size() == 0


def test_embedder_initialization():
    """Test embedder initialization."""
    embedder = Embedder()

    assert embedder.model_name == "sentence-transformers/all-MiniLM-L6-v2"
    assert embedder.dimensions == 384
    assert embedder.cache is not None


def test_embedder_embed_single():
    """Test embedding a single text."""
    embedder = Embedder()

    text = "This is a test document about Redis."
    embedding = embedder.embed(text)

    assert isinstance(embedding, list)
    assert len(embedding) == 384
    assert all(isinstance(x, float) for x in embedding)


def test_embedder_embed_caching():
    """Test that embeddings are cached."""
    embedder = Embedder()

    text = "This is a test document about Redis."

    # First call - should generate embedding
    embedding1 = embedder.embed(text)
    assert embedder.cache.size() == 1

    # Second call - should use cache
    embedding2 = embedder.embed(text)
    assert embedding1 == embedding2
    assert embedder.cache.size() == 1


def test_embedder_embed_batch():
    """Test embedding a batch of texts."""
    embedder = Embedder()

    texts = [
        "This is a test document about Redis.",
        "Redis is an in-memory database.",
        "Active-Active replication is a feature of Redis Enterprise.",
    ]

    embeddings = embedder.embed_batch(texts, batch_size=2)

    assert len(embeddings) == 3
    assert all(len(emb) == 384 for emb in embeddings)
    assert embedder.cache.size() == 3


def test_embedder_embed_batch_with_cache():
    """Test batch embedding with partial cache hits."""
    embedder = Embedder()

    texts = [
        "This is a test document about Redis.",
        "Redis is an in-memory database.",
        "Active-Active replication is a feature of Redis Enterprise.",
    ]

    # First batch - all new
    embeddings1 = embedder.embed_batch(texts[:2])
    assert embedder.cache.size() == 2

    # Second batch - one cached, one new
    embeddings2 = embedder.embed_batch([texts[0], texts[2]])
    assert embedder.cache.size() == 3

    # Verify cached embedding is the same
    assert embeddings1[0] == embeddings2[0]


def test_embedder_different_texts_different_embeddings():
    """Test that different texts produce different embeddings."""
    embedder = Embedder()

    text1 = "Redis is a database."
    text2 = "Python is a programming language."

    embedding1 = embedder.embed(text1)
    embedding2 = embedder.embed(text2)

    assert embedding1 != embedding2
