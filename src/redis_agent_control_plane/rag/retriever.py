"""Filter-first retrieval for RAG pipeline using Redis 8.4+ native vector search."""

from typing import Any

import numpy as np  # type: ignore
from redis import Redis

from redis_agent_control_plane.rag.embedder import Embedder


class RedisRetriever:
    """Redis retriever with filter-first pattern using Redis 8.4+ native vector search."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        index_name: str = "redis_docs",
        embedder: Embedder | None = None,
    ):
        """Initialize Redis retriever.

        Args:
            redis_url: Redis connection URL (default: redis://localhost:6379)
            index_name: Name of the index (default: redis_docs)
            embedder: Embedder instance (default: create new one)
        """
        self.redis_url = redis_url
        self.index_name = index_name
        self.prefix = f"{index_name}:chunk:"

        # Create or use provided embedder
        self.embedder = embedder or Embedder()

        # Create Redis client (decode_responses=False to handle binary embeddings)
        self.client = Redis.from_url(redis_url, decode_responses=False)

    def search(
        self,
        query: str,
        top_k: int = 5,
        distance_threshold: float = 0.30,
        product_area: str | None = None,
        category: str | None = None,
        return_fields: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for relevant chunks using vector search with optional filters.

        Args:
            query: Search query
            top_k: Number of results to return (default: 5)
            distance_threshold: Maximum cosine distance (default: 0.30)
            product_area: Filter by product area
                (redis_software, redis_cloud, redis_stack, redis_oss)
            category: Filter by category (operate, integrate, develop)
            return_fields: Fields to return
                (default: content, doc_path, title, section_heading, toc_path)

        Returns:
            List of search results with metadata
        """
        # Generate query embedding
        query_embedding = np.array(self.embedder.embed(query), dtype=np.float32)

        # Get all chunk keys
        pattern = f"{self.prefix}*"
        cursor = 0
        all_keys = []
        while True:
            cursor, keys = self.client.scan(cursor, match=pattern, count=100)  # type: ignore
            all_keys.extend(keys)
            if cursor == 0:
                break

        # Compute similarities for all chunks
        results = []
        for key in all_keys:
            # Get chunk data
            chunk_data = self.client.hgetall(key)  # type: ignore

            # Decode string fields
            def decode_field(value: bytes | str | None) -> str:
                if value is None:
                    return ""
                if isinstance(value, bytes):
                    return value.decode("utf-8")
                return str(value)

            # Apply filters
            chunk_product_area = decode_field(chunk_data.get(b"product_area"))  # type: ignore
            chunk_category = decode_field(chunk_data.get(b"category"))  # type: ignore

            if product_area and chunk_product_area != product_area:
                continue
            if category and chunk_category != category:
                continue

            # Get embedding
            embedding_bytes = chunk_data.get(b"embedding")  # type: ignore
            if not embedding_bytes:
                continue

            # Convert bytes to numpy array
            chunk_embedding = np.frombuffer(embedding_bytes, dtype=np.float32)  # type: ignore

            # Compute cosine similarity
            similarity = np.dot(query_embedding, chunk_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
            )
            distance = 1.0 - similarity

            # Filter by distance threshold
            if distance <= distance_threshold:
                result = {
                    "chunk_id": decode_field(chunk_data.get(b"chunk_id")),  # type: ignore
                    "content": decode_field(chunk_data.get(b"content")),  # type: ignore
                    "doc_path": decode_field(chunk_data.get(b"doc_path")),  # type: ignore
                    "doc_url": decode_field(chunk_data.get(b"doc_url")),  # type: ignore
                    "title": decode_field(chunk_data.get(b"title")),  # type: ignore
                    "section_heading": decode_field(chunk_data.get(b"section_heading")),  # type: ignore
                    "toc_path": decode_field(chunk_data.get(b"toc_path")),  # type: ignore
                    "category": chunk_category,
                    "product_area": chunk_product_area,
                    "vector_distance": float(distance),
                }
                results.append(result)

        # Sort by distance (lower is better)
        results.sort(key=lambda x: float(x["vector_distance"]))  # type: ignore

        # Return top-k results
        return results[:top_k]

    def search_with_filters(
        self,
        query: str,
        filters: dict[str, str],
        top_k: int = 5,
        distance_threshold: float = 0.30,
        return_fields: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search with custom filters.

        Args:
            query: Search query
            filters: Dictionary of filters
                (e.g., {"product_area": "redis_software", "category": "operate"})
            top_k: Number of results to return (default: 5)
            distance_threshold: Maximum cosine distance (default: 0.30)
            return_fields: Fields to return

        Returns:
            List of search results with metadata
        """
        # Extract known filters
        product_area = filters.get("product_area")
        category = filters.get("category")

        return self.search(
            query=query,
            top_k=top_k,
            distance_threshold=distance_threshold,
            product_area=product_area,
            category=category,
            return_fields=return_fields,
        )

    def deduplicate_results(
        self,
        results: list[dict[str, Any]],
        max_per_doc: int = 1,
    ) -> list[dict[str, Any]]:
        """Deduplicate results by keeping top N chunks per document.

        Args:
            results: Search results
            max_per_doc: Maximum chunks to keep per document (default: 1)

        Returns:
            Deduplicated results
        """
        doc_chunks: dict[str, list[dict[str, Any]]] = {}

        # Group by doc_path
        for result in results:
            doc_path = result.get("doc_path", "")
            if doc_path not in doc_chunks:
                doc_chunks[doc_path] = []
            doc_chunks[doc_path].append(result)

        # Keep top N per document
        deduplicated = []
        for chunks in doc_chunks.values():
            # Sort by score (lower distance is better)
            sorted_chunks = sorted(chunks, key=lambda x: x.get("vector_distance", 1.0))
            deduplicated.extend(sorted_chunks[:max_per_doc])

        # Sort final results by score
        deduplicated.sort(key=lambda x: x.get("vector_distance", 1.0))

        return deduplicated
