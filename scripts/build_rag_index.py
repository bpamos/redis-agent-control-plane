#!/usr/bin/env python3
"""End-to-end RAG pipeline: ingest → chunk → embed → index."""

import argparse
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from redis_agent_control_plane.rag.chunker import chunk_document
from redis_agent_control_plane.rag.embedder import Embedder
from redis_agent_control_plane.rag.indexer import RedisIndexer
from redis_agent_control_plane.rag.ingest import ingest_corpus


def main() -> int:
    """Main entry point for RAG pipeline."""
    parser = argparse.ArgumentParser(description="Build RAG index from Redis docs corpus")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("../docs/content"),
        help="Path to corpus directory (default: ../docs/content)",
    )
    parser.add_argument(
        "--redis-url",
        type=str,
        default=os.getenv("REDIS_URL", "redis://localhost:6379"),
        help="Redis connection URL (default: from REDIS_URL env var or redis://localhost:6379)",
    )
    parser.add_argument(
        "--index-name",
        type=str,
        default="redis_docs",
        help="Index name (default: redis_docs)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of documents to process (for testing)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing index",
    )

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("RAG Pipeline: Build Index")
    print(f"{'='*60}\n")

    # Step 1: Ingest documents
    print(f"[1/4] Ingesting documents from {args.source}...")
    start_time = time.time()

    try:
        documents = ingest_corpus(args.source)
    except (FileNotFoundError, NotADirectoryError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.limit:
        documents = documents[: args.limit]

    ingest_time = time.time() - start_time
    print(f"  ✓ Loaded {len(documents)} documents in {ingest_time:.2f}s")

    # Step 2: Chunk documents
    print("\n[2/4] Chunking documents...")
    start_time = time.time()

    all_chunks = []
    for doc in documents:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)

    chunk_time = time.time() - start_time
    print(f"  ✓ Created {len(all_chunks)} chunks in {chunk_time:.2f}s")
    print(f"  ✓ Avg chunks per doc: {len(all_chunks) / len(documents):.1f}")

    # Step 3: Generate embeddings
    print("\n[3/4] Generating embeddings...")
    start_time = time.time()

    embedder = Embedder()
    print(f"  ✓ Using model: {embedder.model_name}")
    print(f"  ✓ Embedding dimensions: {embedder.dimensions}")

    # Extract content from chunks
    chunk_contents = [chunk.content for chunk in all_chunks]

    # Generate embeddings in batches
    embeddings = embedder.embed_batch(chunk_contents, batch_size=32)

    embed_time = time.time() - start_time
    print(f"  ✓ Generated {len(embeddings)} embeddings in {embed_time:.2f}s")
    print(f"  ✓ Cache size: {embedder.cache.size()}")

    # Step 4: Index chunks
    print(f"\n[4/4] Indexing chunks in Redis ({args.redis_url})...")
    start_time = time.time()

    try:
        indexer = RedisIndexer(
            redis_url=args.redis_url,
            index_name=args.index_name,
            vector_dims=embedder.dimensions,
        )

        # Create index
        indexer.create_index(overwrite=args.overwrite)
        print(f"  ✓ Created index: {args.index_name}")

        # Index chunks
        indexer.index_chunks(all_chunks, embeddings)

        index_time = time.time() - start_time
        print(f"  ✓ Indexed {len(all_chunks)} chunks in {index_time:.2f}s")

    except Exception as e:
        print(f"Error indexing chunks: {e}", file=sys.stderr)
        return 1

    # Summary
    total_time = ingest_time + chunk_time + embed_time + index_time
    print(f"\n{'='*60}")
    print("Pipeline Summary")
    print(f"{'='*60}")
    print(f"Documents processed: {len(documents)}")
    print(f"Chunks created: {len(all_chunks)}")
    print(f"Embeddings generated: {len(embeddings)}")
    print(f"Index name: {args.index_name}")
    print(f"Total time: {total_time:.2f}s")
    print(f"{'='*60}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

