"""Redis indexing with native Redis 8.4+ vector search."""

from typing import Any

import numpy as np  # type: ignore
from redis import Redis

from redis_agent_control_plane.rag.chunker import Chunk


def create_index_schema(index_name: str = "redis_docs", vector_dims: int = 384) -> dict[str, Any]:
    """Create Redis index schema for RAG pipeline.

    Args:
        index_name: Name of the index (default: redis_docs)
        vector_dims: Vector dimensions (default: 384 for all-MiniLM-L6-v2)

    Returns:
        Index schema dictionary
    """
    return {
        "index": {
            "name": index_name,
            "prefix": f"{index_name}:chunk:",
            "storage_type": "hash",
        },
        "fields": [
            # Metadata fields (for filtering)
            {"name": "source", "type": "tag", "attrs": {"sortable": False}},
            {"name": "doc_path", "type": "text", "attrs": {"sortable": False}},
            {"name": "doc_url", "type": "text", "attrs": {"sortable": False}},
            {"name": "title", "type": "text", "attrs": {"sortable": False}},
            {"name": "category", "type": "tag", "attrs": {"sortable": False}},
            {"name": "product_area", "type": "tag", "attrs": {"sortable": False}},
            {"name": "section_heading", "type": "text", "attrs": {"sortable": False}},
            {"name": "toc_path", "type": "text", "attrs": {"sortable": False}},
            {"name": "chunk_id", "type": "tag", "attrs": {"sortable": True}},
            {"name": "chunk_index", "type": "numeric", "attrs": {"sortable": True}},
            {"name": "subchunk_index", "type": "numeric", "attrs": {"sortable": True}},
            # Content field
            {"name": "content", "type": "text", "attrs": {"sortable": False}},
            # Vector field
            {
                "name": "embedding",
                "type": "vector",
                "attrs": {
                    "dims": vector_dims,
                    "distance_metric": "cosine",
                    "algorithm": "hnsw",
                    "datatype": "float32",
                },
            },
        ],
    }


class RedisIndexer:
    """Redis indexer for RAG chunks using Redis 8.4+ native vector search."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        index_name: str = "redis_docs",
        vector_dims: int = 384,
    ):
        """Initialize Redis indexer.

        Args:
            redis_url: Redis connection URL (default: redis://localhost:6379)
            index_name: Name of the index (default: redis_docs)
            vector_dims: Vector dimensions (default: 384)
        """
        self.redis_url = redis_url
        self.index_name = index_name
        self.vector_dims = vector_dims
        self.prefix = f"{index_name}:chunk:"

        # Create Redis client (decode_responses=False to handle binary embeddings)
        self.client = Redis.from_url(redis_url, decode_responses=False)

    def create_index(self, overwrite: bool = False) -> None:
        """Create the Redis index using native Redis 8.4+ commands.

        Args:
            overwrite: If True, drop existing index first (default: False)
        """
        if overwrite:
            # Delete all keys with this prefix
            pattern = f"{self.prefix}*"
            cursor = 0
            while True:
                cursor, keys = self.client.scan(cursor, match=pattern, count=100)  # type: ignore
                if keys:
                    self.client.delete(*keys)
                if cursor == 0:
                    break

        # Redis 8.4+ creates indexes automatically when using HSET with vector fields
        # No explicit index creation needed

    def index_chunk(self, chunk: Chunk, embedding: list[float]) -> None:
        """Index a single chunk with its embedding using Redis 8.4+ native commands.

        Args:
            chunk: Chunk to index
            embedding: Embedding vector
        """
        key = f"{self.prefix}{chunk.chunk_id}"

        # Convert embedding to bytes for Redis
        embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()

        # Store in Redis hash
        self.client.hset(
            key,
            mapping={
                "source": chunk.source,
                "doc_path": chunk.doc_path,
                "doc_url": chunk.doc_url,
                "title": chunk.title,
                "category": chunk.category,
                "product_area": chunk.product_area,
                "section_heading": chunk.section_heading,
                "toc_path": chunk.toc_path,
                "chunk_id": chunk.chunk_id,
                "chunk_index": str(chunk.chunk_index),
                "subchunk_index": str(chunk.subchunk_index),
                "content": chunk.content,
                "embedding": embedding_bytes,
            },
        )

    def index_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        """Index multiple chunks with their embeddings using Redis 8.4+ native commands.

        Args:
            chunks: List of chunks to index
            embeddings: List of embedding vectors
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match")

        # Use pipeline for batch operations
        pipe = self.client.pipeline()

        for chunk, embedding in zip(chunks, embeddings):
            key = f"{self.prefix}{chunk.chunk_id}"
            embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()

            pipe.hset(
                key,
                mapping={
                    "source": chunk.source,
                    "doc_path": chunk.doc_path,
                    "doc_url": chunk.doc_url,
                    "title": chunk.title,
                    "category": chunk.category,
                    "product_area": chunk.product_area,
                    "section_heading": chunk.section_heading,
                    "toc_path": chunk.toc_path,
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": str(chunk.chunk_index),
                    "subchunk_index": str(chunk.subchunk_index),
                    "content": chunk.content,
                    "embedding": embedding_bytes,
                },
            )

        # Execute all commands
        pipe.execute()
