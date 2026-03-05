"""Context Pack: Structured context for agent consumption.

This module defines the ContextPack and RAGChunk dataclasses for combining
deterministic doc refs (from runbook YAML) with RAG-retrieved chunks (bounded,
filtered results) for each runbook step.
"""

from dataclasses import dataclass, field

from redis_agent_control_plane.orchestration.deployment_spec import DeploymentSpec
from redis_agent_control_plane.orchestration.runbook import DocReference


@dataclass
class RAGChunk:
    """RAG-retrieved chunk with full provenance.

    Maps to fields returned by RedisRetriever.search():
    - chunk_id, content, doc_path, doc_url, title, section_heading,
      toc_path, category, product_area, vector_distance, chunk_index
    """

    # Content
    content: str

    # Document metadata
    doc_path: str
    doc_url: str | None = None
    title: str = ""
    section_heading: str = ""
    toc_path: str = ""

    # Categorization
    category: str = ""  # operate, integrate, develop
    product_area: str = ""  # redis_software, redis_cloud, redis_stack

    # Retrieval metadata
    chunk_id: str = ""
    chunk_index: int = 0
    vector_distance: float = 0.0
    rank: int = 0  # Position in results (1-based)
    why_included: str = "semantic_match"  # "semantic_match" | "keyword_match" | "hybrid"


@dataclass
class ContextPack:
    """Structured context for agent consumption.

    Combines deterministic doc refs (always included) with RAG-retrieved
    chunks (bounded results) for a specific runbook step.
    """

    # Runbook context
    runbook_id: str
    runbook_version: str
    deployment_spec: DeploymentSpec

    # Step context
    step_id: str
    step_name: str
    step_description: str

    # Deterministic references (ALWAYS included, from runbook YAML)
    deterministic_doc_refs: list[DocReference]

    # RAG-retrieved context (bounded results, optional)
    rag_chunks: list[RAGChunk]  # max 10-20 chunks

    # Provenance (where did this data come from?)
    docs_commit_sha: str | None = None
    index_name: str = "redis_docs"
    chunk_ids: list[str] = field(default_factory=list)
    retrieval_timestamp: str = ""
    retrieval_method: str = "hybrid"  # "vector" | "hybrid" | "deterministic_only"
