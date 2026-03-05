"""Runbook: YAML-based runbook definition with steps, validations, and doc refs.

This module defines the Runbook dataclass and YAML loader for structured
deployment workflows.
"""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class PrerequisiteCheck:
    """Prerequisite check definition."""

    check: str
    command: str
    error_message: str
    optional: bool = False


@dataclass
class DocReference:
    """Deterministic document reference."""

    path: str
    section: str


@dataclass
class RAGAssist:
    """RAG assist query configuration."""

    query: str
    filters: dict[str, str] = field(default_factory=dict)
    max_results: int = 5


@dataclass
class StepValidation:
    """Step validation configuration."""

    command: str
    expect: str
    retry: int = 1
    retry_delay: int = 0


@dataclass
class RunbookStep:
    """Runbook step definition."""

    id: str
    name: str
    description: str
    doc_refs: list[DocReference] = field(default_factory=list)
    rag_assist: RAGAssist | None = None
    tool: str | None = None
    command: str | None = None
    validation: StepValidation | None = None


@dataclass
class RollbackStep:
    """Rollback step definition."""

    command: str


@dataclass
class PostValidation:
    """Post-deployment validation."""

    check: str
    command: str
    expect: str


@dataclass
class Runbook:
    """Runbook definition for deployment workflows.

    A runbook contains ordered steps, prerequisites, validations, and rollback
    procedures for a specific deployment variant.

    Attributes:
        id: Unique runbook identifier (e.g., "runbook.re.k8s.clustered")
        name: Human-readable name
        description: Detailed description
        version: Runbook version
        prerequisites: List of prerequisite checks
        steps: Ordered list of deployment steps
        post_validations: Post-deployment validation checks
        rollback: Rollback steps (optional)
    """

    id: str
    name: str
    description: str
    version: str
    prerequisites: list[PrerequisiteCheck] = field(default_factory=list)
    steps: list[RunbookStep] = field(default_factory=list)
    post_validations: list[PostValidation] = field(default_factory=list)
    rollback: list[RollbackStep] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "Runbook":
        """Load runbook from YAML file.

        Args:
            yaml_path: Path to YAML file

        Returns:
            Runbook instance

        Raises:
            FileNotFoundError: If YAML file not found
            ValueError: If YAML is invalid or missing required fields
        """
        if not yaml_path.exists():
            raise FileNotFoundError(f"Runbook file not found: {yaml_path}")

        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "runbook" not in data:
            raise ValueError(f"Invalid runbook YAML: missing 'runbook' key in {yaml_path}")

        runbook_data = data["runbook"]

        # Parse prerequisites
        prerequisites = [
            PrerequisiteCheck(**prereq) for prereq in runbook_data.get("prerequisites", [])
        ]

        # Parse steps
        steps = []
        for step_data in runbook_data.get("steps", []):
            doc_refs = [DocReference(**ref) for ref in step_data.get("doc_refs", [])]
            rag_assist = RAGAssist(**step_data["rag_assist"]) if "rag_assist" in step_data else None
            validation = (
                StepValidation(**step_data["validation"]) if "validation" in step_data else None
            )
            steps.append(
                RunbookStep(
                    id=step_data["id"],
                    name=step_data["name"],
                    description=step_data["description"],
                    doc_refs=doc_refs,
                    rag_assist=rag_assist,
                    tool=step_data.get("tool"),
                    command=step_data.get("command"),
                    validation=validation,
                )
            )

        # Parse post-validations
        post_validations = [
            PostValidation(**val) for val in runbook_data.get("post_validations", [])
        ]

        # Parse rollback
        rollback = [RollbackStep(**step) for step in runbook_data.get("rollback", [])]

        return cls(
            id=runbook_data["id"],
            name=runbook_data["name"],
            description=runbook_data["description"],
            version=runbook_data["version"],
            prerequisites=prerequisites,
            steps=steps,
            post_validations=post_validations,
            rollback=rollback,
        )
