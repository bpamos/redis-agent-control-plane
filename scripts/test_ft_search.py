#!/usr/bin/env python3
"""Test FT.SEARCH index creation and vector search performance."""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

from redis_agent_control_plane.rag.embedder import Embedder
from redis_agent_control_plane.rag.indexer import RedisIndexer
from redis_agent_control_plane.rag.retriever import RedisRetriever


def main() -> None:
    """Test FT.SEARCH index and compare with brute-force search."""
    # Load environment variables
    load_dotenv()
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    print("=" * 80)
    print("FT.SEARCH Index Test")
    print("=" * 80)

    # Step 1: Create indexer and check if index exists
    print("\n[1/5] Checking index status...")
    indexer = RedisIndexer(redis_url=redis_url, index_name="redis_docs")

    # Get index info
    info = indexer.get_index_info()
    if "error" in info:
        print(f"  ⚠️  Index does not exist: {info['error']}")
        print("  Creating index...")
        indexer.create_index(overwrite=False)
        info = indexer.get_index_info()

    # Print index info
    if "num_docs" in info:
        print(f"  ✓ Index exists: {indexer.index_name}")
        print(f"  ✓ Documents: {info.get('num_docs', 'unknown')}")
        print(f"  ✓ Records: {info.get('num_records', 'unknown')}")
    else:
        print("  ✓ Index created successfully")

    # Step 2: Create retriever
    print("\n[2/5] Creating retriever...")
    embedder = Embedder()
    retriever = RedisRetriever(
        redis_url=redis_url, index_name="redis_docs", embedder=embedder
    )
    print("  ✓ Retriever ready")

    # Step 3: Test queries
    test_queries = [
        "How do I configure Active-Active replication?",
        "What are the eviction policies in Redis?",
        "How do I deploy Redis on Kubernetes?",
        "CONFIG SET maxmemory",
    ]

    print("\n[3/5] Testing FT.SEARCH (optimized)...")
    for i, query in enumerate(test_queries, 1):
        print(f"\n  Query {i}: '{query}'")
        start = time.time()
        results = retriever.search(query=query, top_k=3, use_index=True)
        elapsed = time.time() - start

        print(f"    ✓ Found {len(results)} results in {elapsed*1000:.1f}ms")
        if results:
            best = results[0]
            print(f"    ✓ Best match: {best.get('section_heading', 'N/A')}")
            print(f"    ✓ Distance: {best.get('vector_distance', 1.0):.3f}")

    # Step 4: Test brute-force search for comparison
    print("\n[4/5] Testing brute-force search (baseline)...")
    for i, query in enumerate(test_queries, 1):
        print(f"\n  Query {i}: '{query}'")
        start = time.time()
        results = retriever.search(query=query, top_k=3, use_index=False)
        elapsed = time.time() - start

        print(f"    ✓ Found {len(results)} results in {elapsed*1000:.1f}ms")
        if results:
            best = results[0]
            print(f"    ✓ Best match: {best.get('section_heading', 'N/A')}")
            print(f"    ✓ Distance: {best.get('vector_distance', 1.0):.3f}")

    # Step 5: Test filtered search
    print("\n[5/5] Testing filtered search...")
    query = "How do I configure replication?"
    print(f"  Query: '{query}' (filter: product_area=redis_software)")

    start = time.time()
    results = retriever.search(
        query=query, top_k=3, product_area="redis_software", use_index=True
    )
    elapsed = time.time() - start

    print(f"    ✓ Found {len(results)} results in {elapsed*1000:.1f}ms")
    if results:
        for i, result in enumerate(results, 1):
            print(f"    {i}. {result.get('section_heading', 'N/A')}")
            print(f"       Distance: {result.get('vector_distance', 1.0):.3f}")
            print(f"       Product: {result.get('product_area', 'N/A')}")

    print("\n" + "=" * 80)
    print("✅ FT.SEARCH Index Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()

