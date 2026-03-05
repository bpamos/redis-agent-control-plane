"""RunbookRouter: Deterministic routing from DeploymentSpec to runbook_id.

This module provides deterministic, rules-based routing logic to select the
appropriate runbook for a given deployment specification.

Key principle: Routing is table/rules-based, NOT embedding-based, NOT LLM-based.
Same DeploymentSpec always routes to the same runbook_id.
"""

from pathlib import Path

from redis_agent_control_plane.orchestration.deployment_spec import DeploymentSpec
from redis_agent_control_plane.orchestration.runbook import Runbook


class RunbookNotFoundError(Exception):
    """Raised when no runbook is found for a deployment spec."""

    pass


class RunbookRouter:
    """Deterministic router for runbook selection.

    The router maps DeploymentSpec to runbook_id using deterministic rules.
    No embeddings, no LLM calls, no probabilistic behavior.

    Attributes:
        runbooks_dir: Path to runbooks directory
        _runbook_cache: Cache of loaded runbooks
    """

    def __init__(self, runbooks_dir: Path | None = None) -> None:
        """Initialize router.

        Args:
            runbooks_dir: Path to runbooks directory (defaults to ./runbooks)
        """
        if runbooks_dir is None:
            # Default to runbooks/ directory at repo root
            runbooks_dir = Path(__file__).parent.parent.parent.parent / "runbooks"

        self.runbooks_dir = runbooks_dir
        self._runbook_cache: dict[str, Runbook] = {}

    def route(self, spec: DeploymentSpec) -> str:
        """Route deployment spec to runbook ID.

        This is a deterministic mapping: same spec always produces same runbook_id.

        Args:
            spec: Deployment specification

        Returns:
            Runbook ID (e.g., "runbook.redis_enterprise.kubernetes.clustered")

        Raises:
            RunbookNotFoundError: If no runbook exists for the spec
        """
        # Build runbook ID from spec (deterministic)
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
        runbook_ids: list[str] = []

        if not self.runbooks_dir.exists():
            return runbook_ids

        # Scan runbooks directory for YAML files
        for yaml_file in self.runbooks_dir.rglob("*.yaml"):
            # Convert path to runbook ID
            # e.g., redis_enterprise/kubernetes/clustered.yaml ->
            #       runbook.redis_enterprise.kubernetes.clustered
            rel_path = yaml_file.relative_to(self.runbooks_dir)
            parts = list(rel_path.parts[:-1]) + [rel_path.stem]
            runbook_id = "runbook." + ".".join(parts)
            runbook_ids.append(runbook_id)

        return sorted(runbook_ids)
