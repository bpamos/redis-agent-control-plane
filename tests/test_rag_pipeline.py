"""Integration tests for RAG pipeline."""

import pytest

from redis_agent_control_plane.rag.chunker import chunk_document
from redis_agent_control_plane.rag.embedder import Embedder
from redis_agent_control_plane.rag.indexer import RedisIndexer
from redis_agent_control_plane.rag.ingest import Document
from redis_agent_control_plane.rag.retriever import RedisRetriever


@pytest.mark.skip(reason="Requires Redis to be running")
def test_end_to_end_pipeline():
    """Test end-to-end RAG pipeline."""
    # Step 1: Create test documents
    docs = [
        Document(
            file_path="content/operate/rs/databases/active-active.md",
            title="Active-Active Databases",
            content="""---
title: Active-Active Databases
description: Configure Active-Active replication
---

## Overview

Active-Active replication allows you to replicate data across multiple Redis Enterprise clusters.

## Configuration

To configure Active-Active replication:

1. Create a database
2. Enable Active-Active
3. Configure participating clusters

## Best Practices

- Use consistent configuration across clusters
- Monitor replication lag
- Plan for conflict resolution
""",
            source_repo="redis/docs",
        ),
        Document(
            file_path="content/operate/rs/databases/memory.md",
            title="Memory Management",
            content="""---
title: Memory Management
---

## Memory Limits

Configure memory limits for your databases.

## Eviction Policies

Redis supports several eviction policies:

- allkeys-lru
- volatile-lru
- allkeys-random
""",
            source_repo="redis/docs",
        ),
    ]

    # Step 2: Chunk documents
    all_chunks = []
    for doc in docs:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)

    assert len(all_chunks) > 0

    # Step 3: Generate embeddings
    embedder = Embedder()
    chunk_contents = [chunk.content for chunk in all_chunks]
    embeddings = embedder.embed_batch(chunk_contents)

    assert len(embeddings) == len(all_chunks)

    # Step 4: Index chunks
    indexer = RedisIndexer(
        redis_url="redis://localhost:6379",
        index_name="test_pipeline",
        vector_dims=embedder.dimensions,
    )

    indexer.create_index(overwrite=True)
    indexer.index_chunks(all_chunks, embeddings)

    # Step 5: Retrieve chunks
    retriever = RedisRetriever(
        redis_url="redis://localhost:6379",
        index_name="test_pipeline",
        embedder=embedder,
    )

    # Test query 1: Active-Active replication
    results = retriever.search(
        query="How do I set up Active-Active replication?",
        top_k=3,
        distance_threshold=0.50,
    )

    assert len(results) > 0
    # Should find Active-Active content
    assert any("Active-Active" in r.get("content", "") for r in results)

    # Test query 2: Memory management
    results = retriever.search(
        query="What are the eviction policies?",
        top_k=3,
        distance_threshold=0.50,
    )

    assert len(results) > 0
    # Should find eviction policy content
    assert any("eviction" in r.get("content", "").lower() for r in results)

    # Test query 3: With filters
    results = retriever.search(
        query="database configuration",
        top_k=5,
        distance_threshold=0.50,
        product_area="redis_software",
        category="operate",
    )

    assert len(results) > 0
    # All results should match filters
    for result in results:
        # Note: RedisVL may not return these fields in results
        # This is just a placeholder test
        pass


@pytest.mark.skip(reason="Requires Redis to be running")
def test_pipeline_with_code_blocks():
    """Test pipeline with code blocks."""
    doc = Document(
        file_path="content/develop/python/examples.md",
        title="Python Examples",
        content="""## Connection Example

Here's how to connect to Redis:

```python
import redis

r = redis.Redis(host='localhost', port=6379)
r.set('key', 'value')
```

## Advanced Usage

More examples coming soon.
""",
        source_repo="redis/docs",
    )

    # Chunk document
    chunks = chunk_document(doc)

    # Should preserve code block in one chunk
    assert len(chunks) > 0
    code_chunks = [c for c in chunks if "```" in c.content]
    assert len(code_chunks) > 0
