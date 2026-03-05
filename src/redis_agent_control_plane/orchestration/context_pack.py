"""Context Pack: Structured context for agent consumption.

This module defines the ContextPack and RAGChunk dataclasses for combining
deterministic doc refs (from runbook YAML) with RAG-retrieved chunks (bounded,
filtered results) for each runbook step.
"""

import json
from dataclasses import asdict, dataclass, field
from typing import Any

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

    def to_dict(self) -> dict[str, Any]:
        """Convert RAGChunk to dictionary.

        Returns:
            Dictionary representation of the RAGChunk.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RAGChunk":
        """Create RAGChunk from dictionary.

        Args:
            data: Dictionary containing RAGChunk fields.

        Returns:
            RAGChunk instance.
        """
        return cls(**data)


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

    # Schema versioning
    plan_version: str = "1.0.0"  # ContextPack schema version
    spec_version: str = "1.0.0"  # DeploymentSpec schema version

    def to_dict(self) -> dict[str, Any]:
        """Convert ContextPack to dictionary.

        Returns:
            Dictionary representation of the ContextPack with all nested objects converted.
        """
        result = {
            "runbook_id": self.runbook_id,
            "runbook_version": self.runbook_version,
            "deployment_spec": self.deployment_spec.to_dict(),
            "step_id": self.step_id,
            "step_name": self.step_name,
            "step_description": self.step_description,
            "deterministic_doc_refs": [
                {"path": ref.path, "section": ref.section} for ref in self.deterministic_doc_refs
            ],
            "rag_chunks": [chunk.to_dict() for chunk in self.rag_chunks],
            "docs_commit_sha": self.docs_commit_sha,
            "index_name": self.index_name,
            "chunk_ids": self.chunk_ids,
            "retrieval_timestamp": self.retrieval_timestamp,
            "retrieval_method": self.retrieval_method,
            "plan_version": self.plan_version,
            "spec_version": self.spec_version,
        }
        return result

    def to_json(self, indent: int = 2) -> str:
        """Convert ContextPack to JSON string.

        Args:
            indent: Number of spaces for indentation (default: 2).

        Returns:
            JSON string representation of the ContextPack.
        """
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContextPack":
        """Create ContextPack from dictionary.

        Args:
            data: Dictionary containing ContextPack fields.

        Returns:
            ContextPack instance.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        # Reconstruct nested objects
        deployment_spec = DeploymentSpec.from_dict(data["deployment_spec"])
        deterministic_doc_refs = [
            DocReference(path=ref["path"], section=ref["section"])
            for ref in data["deterministic_doc_refs"]
        ]
        rag_chunks = [RAGChunk.from_dict(chunk) for chunk in data["rag_chunks"]]

        return cls(
            runbook_id=data["runbook_id"],
            runbook_version=data["runbook_version"],
            deployment_spec=deployment_spec,
            step_id=data["step_id"],
            step_name=data["step_name"],
            step_description=data["step_description"],
            deterministic_doc_refs=deterministic_doc_refs,
            rag_chunks=rag_chunks,
            docs_commit_sha=data.get("docs_commit_sha"),
            index_name=data.get("index_name", "redis_docs"),
            chunk_ids=data.get("chunk_ids", []),
            retrieval_timestamp=data.get("retrieval_timestamp", ""),
            retrieval_method=data.get("retrieval_method", "hybrid"),
            plan_version=data.get("plan_version", "1.0.0"),
            spec_version=data.get("spec_version", "1.0.0"),
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ContextPack":
        """Create ContextPack from JSON string.

        Args:
            json_str: JSON string containing ContextPack data.

        Returns:
            ContextPack instance.

        Raises:
            ValueError: If JSON is invalid or required fields are missing.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
