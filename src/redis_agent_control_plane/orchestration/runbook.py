"""Runbook: YAML-based runbook definition with steps, validations, and doc refs.

This module defines the Runbook dataclass and YAML loader for structured
deployment workflows.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
    def _load_step_from_file(cls, step_ref: str, steps_dir: Path) -> dict[str, Any]:
        """Load step definition from YAML file.

        Args:
            step_ref: Step reference path (e.g., "redis_enterprise/kubernetes/install_operator")
            steps_dir: Base directory for step files

        Returns:
            Step data dictionary

        Raises:
            FileNotFoundError: If step file not found
            ValueError: If step YAML is invalid
        """
        step_path = steps_dir / f"{step_ref}.yaml"
        if not step_path.exists():
            raise FileNotFoundError(f"Step file not found: {step_path}")

        with open(step_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "step" not in data:
            raise ValueError(f"Invalid step YAML: missing 'step' key in {step_path}")

        step_data: dict[str, Any] = data["step"]
        return step_data

    @classmethod
    def _merge_parameters(
        cls, step_data: dict[str, Any], runbook_params: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Merge runbook parameters with step defaults.

        Args:
            step_data: Step definition data
            runbook_params: Parameters from runbook (overrides)

        Returns:
            Merged step data with parameter substitution
        """
        # Build parameter map: start with defaults, override with runbook params
        param_map = {}
        for param in step_data.get("parameters", []):
            param_map[param["name"]] = param.get("default", "")

        if runbook_params:
            param_map.update(runbook_params)

        # Substitute parameters in command and validation
        result = step_data.copy()
        if "command" in result and result["command"]:
            command = result["command"]
            for param_name, param_value in param_map.items():
                # Convert to string for substitution
                if isinstance(param_value, bool):
                    value_str = str(param_value).lower()
                else:
                    value_str = str(param_value)
                command = command.replace(f"${param_name.upper()}", value_str)
            result["command"] = command

        if "validation" in result and result["validation"]:
            validation = result["validation"].copy()
            for key in ["command", "expect"]:
                if key in validation and validation[key]:
                    value = validation[key]
                    for param_name, param_value in param_map.items():
                        if isinstance(param_value, bool):
                            value_str = str(param_value).lower()
                        else:
                            value_str = str(param_value)
                        value = value.replace(f"${param_name.upper()}", value_str)
                    validation[key] = value
            result["validation"] = validation

        return result

    @classmethod
    def from_yaml(cls, yaml_path: Path, steps_dir: Path | None = None) -> "Runbook":
        """Load runbook from YAML file.

        Args:
            yaml_path: Path to YAML file
            steps_dir: Base directory for step files (defaults to workspace root / "steps")

        Returns:
            Runbook instance

        Raises:
            FileNotFoundError: If YAML file not found
            ValueError: If YAML is invalid or missing required fields
        """
        if not yaml_path.exists():
            raise FileNotFoundError(f"Runbook file not found: {yaml_path}")

        # Default steps directory is workspace root / "steps"
        if steps_dir is None:
            # Find workspace root by looking for runbooks directory
            # Navigate up from runbook file until we find the parent of runbooks/
            current = yaml_path.parent
            while current.name != "runbooks" and current.parent != current:
                current = current.parent
            if current.name == "runbooks":
                steps_dir = current.parent / "steps"
            else:
                # Fallback: assume 3 levels up
                steps_dir = yaml_path.parent.parent.parent / "steps"

        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "runbook" not in data:
            raise ValueError(f"Invalid runbook YAML: missing 'runbook' key in {yaml_path}")

        runbook_data = data["runbook"]

        # Parse prerequisites
        prerequisites = [
            PrerequisiteCheck(**prereq) for prereq in runbook_data.get("prerequisites", [])
        ]

        # Parse steps (support both inline and step_ref)
        steps = []
        for step_data in runbook_data.get("steps", []):
            # Check if this is a step reference
            if "step_ref" in step_data:
                # Load step from file
                step_ref = step_data["step_ref"]
                loaded_step = cls._load_step_from_file(step_ref, steps_dir)
                # Merge parameters
                runbook_params = step_data.get("parameters", {})
                merged_step = cls._merge_parameters(loaded_step, runbook_params)
                step_data = merged_step

            # Parse step data (whether loaded or inline)
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
