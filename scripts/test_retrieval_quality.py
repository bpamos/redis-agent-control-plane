#!/usr/bin/env python3
"""Test retrieval quality with sample queries."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from redis_agent_control_plane.rag.embedder import Embedder
from redis_agent_control_plane.rag.retriever import RedisRetriever


def test_retrieval_quality(index_name: str = "redis_docs"):
    """Test retrieval quality with sample queries."""
    print("\n" + "=" * 60)
    print("RAG Retrieval Quality Test")
    print("=" * 60 + "\n")

    # Get Redis URL from environment
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    print(f"Redis URL: {redis_url.split('@')[1] if '@' in redis_url else redis_url}")
    print(f"Index name: {index_name}\n")

    # Initialize retriever
    embedder = Embedder()
    retriever = RedisRetriever(
        redis_url=redis_url,
        index_name=index_name,
        embedder=embedder,
    )

    # Test queries
    test_queries = [
        "How do I configure Active-Active replication?",
        "What are the eviction policies in Redis?",
        "How do I deploy Redis on Kubernetes?",
        "What is the difference between Redis Cloud and Redis Software?",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"[Query {i}] {query}")
        print("-" * 60)

        results = retriever.search(
            query=query,
            top_k=3,
            distance_threshold=0.50,
        )

        if not results:
            print("  ⚠️  No results found\n")
            continue

        print(f"  ✓ Found {len(results)} results\n")

        for j, result in enumerate(results, 1):
            distance = result.get("vector_distance", 0)
            title = result.get("title", "Unknown")
            section = result.get("section_heading", "N/A")
            content = result.get("content", "")[:150]  # First 150 chars

            print(f"  Result {j}:")
            print(f"    Distance: {distance:.3f}")
            print(f"    Title: {title}")
            print(f"    Section: {section}")
            print(f"    Content: {content}...")
            print()

    print("=" * 60)
    print("✅ Retrieval quality test complete")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test retrieval quality")
    parser.add_argument(
        "--index-name",
        type=str,
        default="redis_docs",
        help="Index name (default: redis_docs)",
    )

    args = parser.parse_args()
    test_retrieval_quality(args.index_name)

