#!/usr/bin/env python3
"""Test hybrid search (vector + BM25) with RRF score combination."""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

from redis_agent_control_plane.rag.embedder import Embedder
from redis_agent_control_plane.rag.retriever import RedisRetriever


def main() -> None:
    """Test hybrid search and compare with vector-only search."""
    # Load environment variables
    load_dotenv()
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    print("=" * 80)
    print("Hybrid Search Test (Vector + BM25 with RRF)")
    print("=" * 80)

    # Create retriever
    print("\n[1/3] Creating retriever...")
    embedder = Embedder()
    retriever = RedisRetriever(
        redis_url=redis_url, index_name="redis_docs", embedder=embedder
    )
    print("  ✓ Retriever ready")

    # Test queries
    test_queries = [
        {
            "query": "CONFIG SET maxmemory",
            "type": "exact_command",
            "description": "Exact command search (should favor text match)",
        },
        {
            "query": "How do I configure memory limits in Redis?",
            "type": "semantic",
            "description": "Semantic query (should favor vector search)",
        },
        {
            "query": "maxmemory eviction policy",
            "type": "hybrid",
            "description": "Hybrid query (should combine both)",
        },
        {
            "query": "HSET key field value",
            "type": "exact_command",
            "description": "API method search (should favor text match)",
        },
    ]

    # Test hybrid search
    print("\n[2/3] Testing hybrid search...")
    for i, test in enumerate(test_queries, 1):
        print(f"\n  Query {i}: '{test['query']}'")
        print(f"  Type: {test['type']} - {test['description']}")

        start = time.time()
        results = retriever.hybrid_search(
            query=test["query"],
            top_k=3,
            vector_weight=0.7,
            text_weight=0.3,
            rrf_k=60,
        )
        elapsed = time.time() - start

        print(f"    ✓ Found {len(results)} results in {elapsed*1000:.1f}ms")
        if results:
            for j, result in enumerate(results, 1):
                print(f"    {j}. {result.get('section_heading', 'N/A')[:60]}")
                print(f"       Hybrid: {result.get('hybrid_score', 0):.4f} "
                      f"(V:{result.get('vector_score', 0):.4f} + "
                      f"T:{result.get('text_score', 0):.4f})")
                if result.get("vector_distance"):
                    print(f"       Vector distance: {result.get('vector_distance', 1.0):.3f}")

    # Compare with vector-only search
    print("\n[3/3] Comparing with vector-only search...")
    for i, test in enumerate(test_queries, 1):
        print(f"\n  Query {i}: '{test['query']}'")

        # Hybrid search
        start = time.time()
        hybrid_results = retriever.hybrid_search(query=test["query"], top_k=3)
        hybrid_time = time.time() - start

        # Vector-only search
        start = time.time()
        vector_results = retriever.search(query=test["query"], top_k=3, use_index=True)
        vector_time = time.time() - start

        print(f"    Hybrid: {len(hybrid_results)} results in {hybrid_time*1000:.1f}ms")
        print(f"    Vector: {len(vector_results)} results in {vector_time*1000:.1f}ms")

        # Compare top result
        if hybrid_results and vector_results:
            hybrid_top = hybrid_results[0].get("section_heading", "N/A")[:40]
            vector_top = vector_results[0].get("section_heading", "N/A")[:40]
            if hybrid_top != vector_top:
                print(f"    ⚠️  Different top results:")
                print(f"       Hybrid: {hybrid_top}")
                print(f"       Vector: {vector_top}")
            else:
                print(f"    ✓ Same top result: {hybrid_top}")

    print("\n" + "=" * 80)
    print("✅ Hybrid Search Test Complete")
    print("=" * 80)
    print("\nKey Observations:")
    print("- Hybrid search combines vector similarity and text matching")
    print("- RRF (Reciprocal Rank Fusion) balances both signals")
    print("- Exact command queries benefit from text search")
    print("- Semantic queries benefit from vector search")
    print("- Hybrid queries get best of both worlds")


if __name__ == "__main__":
    main()

