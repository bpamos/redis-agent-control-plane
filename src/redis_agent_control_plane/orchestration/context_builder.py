"""Context Builder: Builds ContextPack from runbook steps with RAG enrichment.

This module provides the ContextBuilder class that integrates with RedisRetriever
to build structured context packs for agent consumption.
"""

from datetime import UTC, datetime
from typing import Any

from redis_agent_control_plane.orchestration.context_pack import ContextPack, RAGChunk
from redis_agent_control_plane.orchestration.deployment_spec import DeploymentSpec
from redis_agent_control_plane.orchestration.runbook import Runbook, RunbookStep
from redis_agent_control_plane.rag.retriever import RedisRetriever


class ContextBuilder:
    """Builds ContextPack from runbook steps with RAG enrichment.

    Integrates with RedisRetriever to provide bounded, filtered context
    enrichment while maintaining strict product area isolation.
    """

    def __init__(
        self,
        retriever: RedisRetriever | None = None,
        redis_url: str = "redis://localhost:6379",
        index_name: str = "redis_docs",
    ):
        """Initialize ContextBuilder.

        Args:
            retriever: RedisRetriever instance (default: create new one)
            redis_url: Redis connection URL (default: redis://localhost:6379)
            index_name: Name of the index (default: redis_docs)
        """
        self.retriever = retriever or RedisRetriever(redis_url=redis_url, index_name=index_name)
        self.index_name = index_name

    def build_context_pack(
        self,
        runbook: Runbook,
        step: RunbookStep,
        deployment_spec: DeploymentSpec,
        max_rag_chunks: int = 10,
        distance_threshold: float = 0.30,
        use_rag: bool = True,
    ) -> ContextPack:
        """Build ContextPack for a specific runbook step.

        Args:
            runbook: Runbook instance
            step: RunbookStep instance
            deployment_spec: DeploymentSpec instance
            max_rag_chunks: Maximum number of RAG chunks to include (default: 10)
            distance_threshold: Maximum cosine distance for RAG results (default: 0.30)
            use_rag: Whether to include RAG enrichment (default: True)

        Returns:
            ContextPack with deterministic doc refs and optional RAG chunks
        """
        # Extract deterministic doc refs from step
        deterministic_doc_refs = step.doc_refs

        # Initialize RAG chunks list
        rag_chunks: list[RAGChunk] = []
        chunk_ids: list[str] = []
        retrieval_method = "deterministic_only"

        # Perform RAG enrichment if enabled and step has rag_assist
        if use_rag and step.rag_assist:
            # Map deployment_spec.product to product_area filter
            product_area = self._map_product_to_product_area(deployment_spec.product)

            # Get category from rag_assist filters or default to "operate"
            category = step.rag_assist.filters.get("category", "operate")

            # Query RAG with filter-first pattern
            rag_results = self.retriever.search(
                query=step.rag_assist.query,
                top_k=max_rag_chunks,
                distance_threshold=distance_threshold,
                product_area=product_area,
                category=category,
                use_index=True,
            )

            # Convert results to RAGChunk objects
            rag_chunks = self._convert_to_rag_chunks(rag_results)
            chunk_ids = [chunk.chunk_id for chunk in rag_chunks]
            retrieval_method = "hybrid"

        # Build ContextPack
        return ContextPack(
            runbook_id=runbook.id,
            runbook_version=runbook.version,
            deployment_spec=deployment_spec,
            step_id=step.id,
            step_name=step.name,
            step_description=step.description,
            deterministic_doc_refs=deterministic_doc_refs,
            rag_chunks=rag_chunks,
            docs_commit_sha=None,  # TODO: Add git integration
            index_name=self.index_name,
            chunk_ids=chunk_ids,
            retrieval_timestamp=datetime.now(UTC).isoformat(),
            retrieval_method=retrieval_method,
        )

    def _map_product_to_product_area(self, product: str) -> str:
        """Map deployment_spec.product to product_area filter.

        Args:
            product: Product from DeploymentSpec (redis_enterprise, redis_cloud, redis_stack)

        Returns:
            Product area for RAG filtering (redis_software, redis_cloud, redis_stack)
        """
        # Map redis_enterprise -> redis_software
        if product == "redis_enterprise":
            return "redis_software"
        # redis_cloud and redis_stack map directly
        return product

    def _convert_to_rag_chunks(self, results: list[dict[str, Any]]) -> list[RAGChunk]:
        """Convert RedisRetriever results to RAGChunk objects.

        Args:
            results: List of search results from RedisRetriever

        Returns:
            List of RAGChunk objects with full provenance
        """
        rag_chunks = []
        for rank, result in enumerate(results, 1):
            rag_chunk = RAGChunk(
                content=result.get("content", ""),
                doc_path=result.get("doc_path", ""),
                doc_url=result.get("doc_url"),
                title=result.get("title", ""),
                section_heading=result.get("section_heading", ""),
                toc_path=result.get("toc_path", ""),
                category=result.get("category", ""),
                product_area=result.get("product_area", ""),
                chunk_id=result.get("chunk_id", ""),
                chunk_index=int(result.get("chunk_index", 0)),
                vector_distance=float(result.get("vector_distance", 0.0)),
                rank=rank,
                why_included="semantic_match",  # Default for vector search
            )
            rag_chunks.append(rag_chunk)
        return rag_chunks
