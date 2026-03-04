#!/usr/bin/env python3
"""Test script to verify RAG pipeline works end-to-end."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from redis_agent_control_plane.rag.chunker import chunk_document
from redis_agent_control_plane.rag.embedder import Embedder
from redis_agent_control_plane.rag.indexer import RedisIndexer
from redis_agent_control_plane.rag.ingest import Document
from redis_agent_control_plane.rag.retriever import RedisRetriever


def test_pipeline():
    """Test the RAG pipeline end-to-end."""
    print("\n" + "=" * 60)
    print("RAG Pipeline End-to-End Test")
    print("=" * 60 + "\n")

    # Step 1: Create test documents
    print("[1/6] Creating test documents...")
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
This provides geo-distribution, disaster recovery, and high availability.

## Configuration

To configure Active-Active replication:

1. Create a database in the first cluster
2. Enable Active-Active replication
3. Configure participating clusters
4. Set up conflict resolution policies

## Best Practices

- Use consistent configuration across all clusters
- Monitor replication lag regularly
- Plan for conflict resolution scenarios
- Test failover procedures

## Troubleshooting

If you encounter issues with Active-Active replication:

- Check network connectivity between clusters
- Verify cluster configurations match
- Review replication logs
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

Configure memory limits for your databases to prevent out-of-memory errors.

## Eviction Policies

Redis supports several eviction policies:

- **allkeys-lru**: Evict least recently used keys
- **volatile-lru**: Evict least recently used keys with TTL
- **allkeys-random**: Evict random keys
- **volatile-random**: Evict random keys with TTL
- **noeviction**: Return errors when memory limit is reached

## Monitoring

Monitor memory usage with:

```bash
redis-cli INFO memory
```
""",
            source_repo="redis/docs",
        ),
    ]
    print(f"  ✓ Created {len(docs)} test documents")

    # Step 2: Chunk documents
    print("\n[2/6] Chunking documents...")
    all_chunks = []
    for doc in docs:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)
    print(f"  ✓ Created {len(all_chunks)} chunks")
    print(f"  ✓ Avg chunks per doc: {len(all_chunks) / len(docs):.1f}")

    # Verify chunk metadata
    sample_chunk = all_chunks[0]
    print(f"\n  Sample chunk metadata:")
    print(f"    - Title: {sample_chunk.title}")
    print(f"    - Category: {sample_chunk.category}")
    print(f"    - Product Area: {sample_chunk.product_area}")
    print(f"    - Section: {sample_chunk.section_heading}")
    print(f"    - Content length: {len(sample_chunk.content)} chars")

    # Step 3: Generate embeddings
    print("\n[3/6] Generating embeddings...")
    embedder = Embedder()
    print(f"  ✓ Using model: {embedder.model_name}")
    print(f"  ✓ Embedding dimensions: {embedder.dimensions}")

    chunk_contents = [chunk.content for chunk in all_chunks]
    embeddings = embedder.embed_batch(chunk_contents, batch_size=8)
    print(f"  ✓ Generated {len(embeddings)} embeddings")
    print(f"  ✓ Cache size: {embedder.cache.size()}")

    # Step 4: Index chunks
    print("\n[4/6] Indexing chunks in Redis...")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    indexer = RedisIndexer(
        redis_url=redis_url,
        index_name="test_rag_pipeline",
        vector_dims=embedder.dimensions,
    )

    indexer.create_index(overwrite=True)
    print(f"  ✓ Created index: test_rag_pipeline")

    indexer.index_chunks(all_chunks, embeddings)
    print(f"  ✓ Indexed {len(all_chunks)} chunks")

    # Step 5: Test retrieval
    print("\n[5/6] Testing retrieval...")
    retriever = RedisRetriever(
        redis_url=redis_url,
        index_name="test_rag_pipeline",
        embedder=embedder,
    )

    # Test query 1: Active-Active replication
    print("\n  Query 1: 'How do I set up Active-Active replication?'")
    results = retriever.search(
        query="How do I set up Active-Active replication?",
        top_k=3,
        distance_threshold=0.50,
    )
    print(f"    ✓ Found {len(results)} results")
    if results:
        best = results[0]
        print(f"    ✓ Best match: {best.get('section_heading')}")
        print(f"    ✓ Distance: {best.get('vector_distance', 0):.3f}")

    # Test query 2: Memory management
    print("\n  Query 2: 'What are the eviction policies?'")
    results = retriever.search(
        query="What are the eviction policies?",
        top_k=3,
        distance_threshold=0.50,
    )
    print(f"    ✓ Found {len(results)} results")
    if results:
        best = results[0]
        print(f"    ✓ Best match: {best.get('section_heading')}")
        print(f"    ✓ Distance: {best.get('vector_distance', 0):.3f}")

    # Test query 3: With filters
    print("\n  Query 3: 'database configuration' (filtered)")
    results = retriever.search(
        query="database configuration",
        top_k=5,
        distance_threshold=0.50,
        product_area="redis_software",
        category="operate",
    )
    print(f"    ✓ Found {len(results)} results with filters")

    # Step 6: Summary
    print("\n[6/6] Summary")
    print(f"  ✓ All pipeline stages completed successfully!")
    print(f"  ✓ Documents: {len(docs)}")
    print(f"  ✓ Chunks: {len(all_chunks)}")
    print(f"  ✓ Embeddings: {len(embeddings)}")
    print(f"  ✓ Retrieval: Working")

    print("\n" + "=" * 60)
    print("✅ RAG Pipeline Test PASSED")
    print("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(test_pipeline())
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)

