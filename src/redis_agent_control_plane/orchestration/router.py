"""RunbookRouter: Deterministic routing from DeploymentSpec to runbook_id.

This module provides deterministic, rules-based routing logic to select the
appropriate runbook for a given deployment specification.

Key principle: Routing is table/rules-based, NOT embedding-based, NOT LLM-based.
Same DeploymentSpec always routes to the same runbook_id.
"""

from pathlib import Path
from typing import Any

import yaml

from redis_agent_control_plane.orchestration.deployment_spec import DeploymentSpec
from redis_agent_control_plane.orchestration.runbook import Runbook


class RunbookNotFoundError(Exception):
    """Raised when no runbook is found for a deployment spec."""

    pass


class AmbiguousRouteError(Exception):
    """Raised when multiple runbooks match with same priority."""

    pass


class RunbookRouter:
    """Deterministic router for runbook selection.

    The router maps DeploymentSpec to runbook_id using deterministic rules.
    No embeddings, no LLM calls, no probabilistic behavior.

    Attributes:
        runbooks_dir: Path to runbooks directory
        _runbook_cache: Cache of loaded runbooks
        _registry: Loaded registry data (None if not using registry)
        _registry_path: Path to registry file
    """

    def __init__(self, runbooks_dir: Path | None = None, use_registry: bool = True) -> None:
        """Initialize router.

        Args:
            runbooks_dir: Path to runbooks directory (defaults to ./runbooks)
            use_registry: Whether to use registry-based routing (default: True)
        """
        if runbooks_dir is None:
            # Default to runbooks/ directory at repo root
            runbooks_dir = Path(__file__).parent.parent.parent.parent / "runbooks"

        self.runbooks_dir = runbooks_dir
        self._runbook_cache: dict[str, Runbook] = {}
        self._registry: dict[str, Any] | None = None
        self._registry_path = self.runbooks_dir / "_registry.yaml"

        # Load registry if enabled
        if use_registry and self._registry_path.exists():
            self._load_registry()

    def route(self, spec: DeploymentSpec) -> str:
        """Route deployment spec to runbook ID.

        This is a deterministic mapping: same spec always produces same runbook_id.

        If registry is loaded, uses registry-based routing.
        Otherwise, falls back to legacy to_runbook_id() method.

        Args:
            spec: Deployment specification

        Returns:
            Runbook ID (e.g., "runbook.redis_enterprise.kubernetes.clustered")

        Raises:
            RunbookNotFoundError: If no runbook exists for the spec
            AmbiguousRouteError: If multiple runbooks match with same priority
        """
        # Use registry-based routing if available
        if self._registry is not None:
            return self.route_with_registry(spec)

        # Fallback to legacy routing
        runbook_id = spec.to_runbook_id()

        # Validate runbook exists
        if not self.has_runbook(runbook_id):
            raise RunbookNotFoundError(
                f"No runbook found for: {runbook_id}\n"
                f"Spec: product={spec.product.value}, "
                f"platform={spec.platform.value}, "
                f"topology={spec.topology.value}"
            )

        return runbook_id

    def has_runbook(self, runbook_id: str) -> bool:
        """Check if runbook exists.

        Args:
            runbook_id: Runbook ID to check

        Returns:
            True if runbook exists, False otherwise
        """
        runbook_path = self._get_runbook_path(runbook_id)
        return runbook_path.exists()

    def load_runbook(self, runbook_id: str) -> Runbook:
        """Load runbook by ID.

        Args:
            runbook_id: Runbook ID to load

        Returns:
            Runbook instance

        Raises:
            RunbookNotFoundError: If runbook file not found
        """
        # Check cache first
        if runbook_id in self._runbook_cache:
            return self._runbook_cache[runbook_id]

        # Load from file
        runbook_path = self._get_runbook_path(runbook_id)
        if not runbook_path.exists():
            raise RunbookNotFoundError(f"Runbook file not found: {runbook_path}")

        runbook = Runbook.from_yaml(runbook_path)

        # Cache for future use
        self._runbook_cache[runbook_id] = runbook

        return runbook

    def _get_runbook_path(self, runbook_id: str) -> Path:
        """Get file path for runbook ID.

        Args:
            runbook_id: Runbook ID (e.g., "runbook.redis_enterprise.kubernetes.clustered")

        Returns:
            Path to runbook YAML file

        Example:
            runbook.redis_enterprise.kubernetes.clustered ->
            runbooks/redis_enterprise/kubernetes/clustered.yaml
        """
        # Parse runbook ID: runbook.{product}.{platform}.{topology}
        parts = runbook_id.split(".")
        if len(parts) != 4 or parts[0] != "runbook":
            raise ValueError(f"Invalid runbook ID format: {runbook_id}")

        _, product, platform, topology = parts

        # Build path: runbooks/{product}/{platform}/{topology}.yaml
        return self.runbooks_dir / product / platform / f"{topology}.yaml"

    def list_available_runbooks(self) -> list[str]:
        """List all available runbook IDs.

        Returns:
            List of runbook IDs
        """
        # Use registry if available
        if self._registry is not None:
            return [
                entry["id"]
                for entry in self._registry.get("runbooks", [])
                if entry.get("enabled", True)
            ]

        # Fallback to directory scan
        runbook_ids: list[str] = []

        if not self.runbooks_dir.exists():
            return runbook_ids

        # Scan runbooks directory for YAML files
        for yaml_file in self.runbooks_dir.rglob("*.yaml"):
            # Skip registry file
            if yaml_file.name == "_registry.yaml":
                continue

            # Convert path to runbook ID
            # e.g., redis_enterprise/kubernetes/clustered.yaml ->
            #       runbook.redis_enterprise.kubernetes.clustered
            rel_path = yaml_file.relative_to(self.runbooks_dir)
            parts = list(rel_path.parts[:-1]) + [rel_path.stem]
            runbook_id = "runbook." + ".".join(parts)
            runbook_ids.append(runbook_id)

        return sorted(runbook_ids)

    def _load_registry(self) -> None:
        """Load runbook registry from YAML file."""
        with open(self._registry_path) as f:
            self._registry = yaml.safe_load(f)

    def route_with_registry(self, spec: DeploymentSpec) -> str:
        """Route deployment spec using registry-based matching.

        Algorithm:
        1. Load all runbooks from registry
        2. Filter by enabled=true
        3. Match selectors against DeploymentSpec
        4. Sort by priority (descending)
        5. Return highest priority match
        6. Fail loudly if no match or ambiguous match

        Args:
            spec: Deployment specification

        Returns:
            Runbook ID

        Raises:
            RunbookNotFoundError: If no runbook matches
            AmbiguousRouteError: If multiple runbooks match with same priority
        """
        if self._registry is None:
            raise RuntimeError("Registry not loaded")

        # Step 1 & 2: Get enabled runbooks
        runbooks = [
            entry for entry in self._registry.get("runbooks", []) if entry.get("enabled", True)
        ]

        # Step 3: Match selectors
        matches = []
        for entry in runbooks:
            if self._matches_selectors(spec, entry.get("selectors", {})):
                matches.append(entry)

        # Check for no matches
        if not matches:
            raise RunbookNotFoundError(
                f"No runbook found for spec:\n"
                f"  product={spec.product.value}\n"
                f"  platform={spec.platform.value}\n"
                f"  topology={spec.topology.value}\n"
                f"  cloud_provider={spec.cloud_provider.value if spec.cloud_provider else 'None'}"
            )

        # Step 4: Sort by priority (descending)
        matches.sort(key=lambda x: x.get("priority", 0), reverse=True)

        # Step 5: Check for ambiguous matches (same priority)
        highest_priority = matches[0].get("priority", 0)
        top_matches = [m for m in matches if m.get("priority", 0) == highest_priority]

        if len(top_matches) > 1:
            runbook_ids = [m["id"] for m in top_matches]
            raise AmbiguousRouteError(
                f"Multiple runbooks match with same priority ({highest_priority}):\n"
                f"  {', '.join(runbook_ids)}\n"
                f"Spec: product={spec.product.value}, "
                f"platform={spec.platform.value}, "
                f"topology={spec.topology.value}"
            )

        # Step 6: Return highest priority match
        runbook_id: str = matches[0]["id"]
        return runbook_id

    def _matches_selectors(self, spec: DeploymentSpec, selectors: dict[str, Any]) -> bool:
        """Check if deployment spec matches all selectors.

        Args:
            spec: Deployment specification
            selectors: Selector criteria from registry

        Returns:
            True if all selectors match, False otherwise
        """
        for key, value in selectors.items():
            # Handle nested selectors (e.g., "scale.nodes")
            if "." in key:
                # Future: implement nested selector matching
                continue

            # Match top-level fields
            if key == "product":
                if spec.product.value != value:
                    return False
            elif key == "platform":
                if spec.platform.value != value:
                    return False
            elif key == "topology":
                if spec.topology.value != value:
                    return False
            elif key == "cloud_provider":
                if spec.cloud_provider is None:
                    return False
                if spec.cloud_provider.value != value:
                    return False

        return True
