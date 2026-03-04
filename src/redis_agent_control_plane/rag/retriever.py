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
        use_index: bool = True,
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
            use_index: If True, use FT.SEARCH (default: True). If False, use brute-force.

        Returns:
            List of search results with metadata
        """
        # Generate query embedding
        query_embedding = np.array(self.embedder.embed(query), dtype=np.float32)

        # Use FT.SEARCH if available and requested
        if use_index:
            try:
                return self._search_with_index(
                    query_embedding=query_embedding,
                    top_k=top_k,
                    distance_threshold=distance_threshold,
                    product_area=product_area,
                    category=category,
                    return_fields=return_fields,
                )
            except Exception as e:
                print(f"FT.SEARCH failed, falling back to brute-force: {e}")
                # Fall through to brute-force search

        # Brute-force search (fallback or if use_index=False)
        return self._search_brute_force(
            query_embedding=query_embedding,
            top_k=top_k,
            distance_threshold=distance_threshold,
            product_area=product_area,
            category=category,
        )

    def _search_with_index(
        self,
        query_embedding: np.ndarray,  # type: ignore
        top_k: int,
        distance_threshold: float,
        product_area: str | None,
        category: str | None,
        return_fields: list[str] | None,
    ) -> list[dict[str, Any]]:
        """Search using FT.SEARCH with vector similarity (optimized).

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            distance_threshold: Maximum cosine distance
            product_area: Filter by product area
            category: Filter by category
            return_fields: Fields to return

        Returns:
            List of search results with metadata
        """
        # Build filter query
        filter_parts = []
        if product_area:
            filter_parts.append(f"@product_area:{{{product_area}}}")
        if category:
            filter_parts.append(f"@category:{{{category}}}")

        # Combine filters with AND
        filter_query = " ".join(filter_parts) if filter_parts else "*"

        # Convert embedding to bytes for Redis
        embedding_bytes = query_embedding.astype(np.float32).tobytes()

        # Build FT.SEARCH command with KNN vector search
        # FT.SEARCH {index} {query} RETURN {fields} SORTBY {field} LIMIT 0 {top_k}
        # For vector search: (query)=>[KNN {top_k} @embedding $vec AS vector_distance]
        knn_query = f"({filter_query})=>[KNN {top_k * 2} @embedding $vec AS vector_distance]"
        cmd = [
            "FT.SEARCH",
            self.index_name,
            knn_query,  # Get 2x for filtering
            "PARAMS",
            "2",
            "vec",
            embedding_bytes,
            "RETURN",
            "11",  # Number of fields to return
            "chunk_id",
            "content",
            "doc_path",
            "doc_url",
            "title",
            "section_heading",
            "toc_path",
            "category",
            "product_area",
            "vector_distance",
            "chunk_index",
            "SORTBY",
            "vector_distance",
            "ASC",
            "LIMIT",
            "0",
            str(top_k * 2),  # Get 2x results for distance filtering
            "DIALECT",
            "2",
        ]

        # Execute search
        response = self.client.execute_command(*cmd)  # type: ignore

        # Parse response
        # Response format: [num_results, key1, [field1, value1, ...], key2, [...]]
        results: list[dict[str, Any]] = []
        if not response or response[0] == 0:  # type: ignore
            return results

        # Skip num_results (response[0]), iterate over key-value pairs
        for i in range(1, len(response), 2):  # type: ignore
            # key = response[i]  # Not needed
            fields = response[i + 1]  # type: ignore

            # Parse fields into dict
            result: dict[str, Any] = {}
            for j in range(0, len(fields), 2):  # type: ignore
                field_name_raw = fields[j]  # type: ignore
                field_name = (
                    field_name_raw.decode("utf-8")
                    if isinstance(field_name_raw, bytes)
                    else str(field_name_raw)
                )
                field_value = fields[j + 1]  # type: ignore
                if isinstance(field_value, bytes):
                    field_value = field_value.decode("utf-8")
                result[field_name] = field_value

            # Convert vector_distance to float
            if "vector_distance" in result:
                result["vector_distance"] = float(result["vector_distance"])

            # Filter by distance threshold
            if result.get("vector_distance", 1.0) <= distance_threshold:
                results.append(result)

        # Return top-k results (already sorted by distance)
        return results[:top_k]

    def _search_brute_force(
        self,
        query_embedding: np.ndarray,  # type: ignore
        top_k: int,
        distance_threshold: float,
        product_area: str | None,
        category: str | None,
    ) -> list[dict[str, Any]]:
        """Search using brute-force similarity computation (fallback).

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            distance_threshold: Maximum cosine distance
            product_area: Filter by product area
            category: Filter by category

        Returns:
            List of search results with metadata
        """
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
        use_index: bool = True,
    ) -> list[dict[str, Any]]:
        """Search with custom filters.

        Args:
            query: Search query
            filters: Dictionary of filters
                (e.g., {"product_area": "redis_software", "category": "operate"})
            top_k: Number of results to return (default: 5)
            distance_threshold: Maximum cosine distance (default: 0.30)
            return_fields: Fields to return
            use_index: If True, use FT.SEARCH (default: True)

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
            use_index=use_index,
        )

    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        vector_weight: float = 0.7,
        text_weight: float = 0.3,
        rrf_k: int = 60,
        distance_threshold: float = 0.30,
        product_area: str | None = None,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        """Hybrid search combining vector similarity and BM25 text search using RRF.

        Args:
            query: Search query
            top_k: Number of results to return (default: 5)
            vector_weight: Weight for vector search results (default: 0.7)
            text_weight: Weight for text search results (default: 0.3)
            rrf_k: RRF constant (default: 60)
            distance_threshold: Maximum cosine distance for vector search (default: 0.30)
            product_area: Filter by product area
            category: Filter by category

        Returns:
            List of search results with hybrid scores
        """
        # Generate query embedding for vector search
        query_embedding = np.array(self.embedder.embed(query), dtype=np.float32)

        # Build filter query
        filter_parts = []
        if product_area:
            filter_parts.append(f"@product_area:{{{product_area}}}")
        if category:
            filter_parts.append(f"@category:{{{category}}}")
        filter_query = " ".join(filter_parts) if filter_parts else "*"

        # 1. Vector search (KNN)
        embedding_bytes = query_embedding.astype(np.float32).tobytes()
        vector_cmd = [
            "FT.SEARCH",
            self.index_name,
            f"({filter_query})=>[KNN {top_k * 3} @embedding $vec AS vector_distance]",
            "PARAMS",
            "2",
            "vec",
            embedding_bytes,
            "RETURN",
            "11",
            "chunk_id",
            "content",
            "doc_path",
            "doc_url",
            "title",
            "section_heading",
            "toc_path",
            "category",
            "product_area",
            "vector_distance",
            "chunk_index",
            "SORTBY",
            "vector_distance",
            "ASC",
            "LIMIT",
            "0",
            str(top_k * 3),
            "DIALECT",
            "2",
        ]

        vector_response = self.client.execute_command(*vector_cmd)  # type: ignore
        vector_results = self._parse_search_response(vector_response)

        # 2. Text search (BM25)
        text_cmd = [
            "FT.SEARCH",
            self.index_name,
            f"({filter_query}) @content|title|section_heading:({query})",
            "RETURN",
            "10",
            "chunk_id",
            "content",
            "doc_path",
            "doc_url",
            "title",
            "section_heading",
            "toc_path",
            "category",
            "product_area",
            "chunk_index",
            "LIMIT",
            "0",
            str(top_k * 3),
            "DIALECT",
            "2",
        ]

        text_response = self.client.execute_command(*text_cmd)  # type: ignore
        text_results = self._parse_search_response(text_response)

        # 3. Combine with RRF (Reciprocal Rank Fusion)
        hybrid_scores: dict[str, dict[str, Any]] = {}

        # Add vector search results
        for rank, result in enumerate(vector_results, 1):
            chunk_id = result.get("chunk_id", "")
            if chunk_id:
                vector_score = vector_weight * (1.0 / (rank + rrf_k))
                hybrid_scores[chunk_id] = {
                    **result,
                    "vector_rank": rank,
                    "vector_score": vector_score,
                    "text_rank": None,
                    "text_score": 0.0,
                    "hybrid_score": vector_score,
                }

        # Add text search results
        for rank, result in enumerate(text_results, 1):
            chunk_id = result.get("chunk_id", "")
            if chunk_id:
                text_score = text_weight * (1.0 / (rank + rrf_k))
                if chunk_id in hybrid_scores:
                    # Update existing result
                    hybrid_scores[chunk_id]["text_rank"] = rank
                    hybrid_scores[chunk_id]["text_score"] = text_score
                    hybrid_scores[chunk_id]["hybrid_score"] += text_score
                else:
                    # Add new result
                    hybrid_scores[chunk_id] = {
                        **result,
                        "vector_rank": None,
                        "vector_score": 0.0,
                        "text_rank": rank,
                        "text_score": text_score,
                        "hybrid_score": text_score,
                    }

        # Sort by hybrid score (higher is better)
        sorted_results = sorted(
            hybrid_scores.values(), key=lambda x: x["hybrid_score"], reverse=True
        )

        # Return top-k results
        return sorted_results[:top_k]

    def _parse_search_response(self, response: Any) -> list[dict[str, Any]]:
        """Parse FT.SEARCH response into list of results.

        Args:
            response: Raw FT.SEARCH response

        Returns:
            List of parsed results
        """
        results: list[dict[str, Any]] = []
        if not response or response[0] == 0:  # type: ignore
            return results

        for i in range(1, len(response), 2):  # type: ignore
            fields = response[i + 1]  # type: ignore

            # Parse fields into dict
            result: dict[str, Any] = {}
            for j in range(0, len(fields), 2):  # type: ignore
                field_name_raw = fields[j]  # type: ignore
                field_name = (
                    field_name_raw.decode("utf-8")
                    if isinstance(field_name_raw, bytes)
                    else str(field_name_raw)
                )
                field_value = fields[j + 1]  # type: ignore
                if isinstance(field_value, bytes):
                    field_value = field_value.decode("utf-8")
                result[field_name] = field_value

            # Convert vector_distance to float if present
            if "vector_distance" in result:
                result["vector_distance"] = float(result["vector_distance"])

            results.append(result)

        return results

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
            # Sort by score (lower distance is better for vector, higher for hybrid)
            if "hybrid_score" in chunks[0]:
                sorted_chunks = sorted(
                    chunks, key=lambda x: x.get("hybrid_score", 0.0), reverse=True
                )
            else:
                sorted_chunks = sorted(chunks, key=lambda x: x.get("vector_distance", 1.0))
            deduplicated.extend(sorted_chunks[:max_per_doc])

        # Sort final results
        if deduplicated and "hybrid_score" in deduplicated[0]:
            deduplicated.sort(key=lambda x: x.get("hybrid_score", 0.0), reverse=True)
        else:
            deduplicated.sort(key=lambda x: x.get("vector_distance", 1.0))

        return deduplicated
