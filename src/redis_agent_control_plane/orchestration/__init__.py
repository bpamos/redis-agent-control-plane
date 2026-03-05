"""Orchestration module for deterministic runbook-based deployment workflows.

This module provides the deterministic layer above the RAG pipeline for reliable
Redis deployment workflows across multiple variants (VM, Kubernetes, Redis Cloud, etc.).

Key components:
- DeploymentSpec: Structured input contract for deployment intent
- Runbook: YAML-based runbook definition with steps, validations, and doc refs
- RunbookRouter: Deterministic routing from DeploymentSpec to runbook_id
- ContextPack: Structured context assembly for agent consumption (future)

Design principle: RAG is a supporting subsystem, not the primary planner.
The deterministic layer provides structured runbooks with ordered steps, validations,
and tool hooks, with RAG used as bounded context enrichment.
"""

from redis_agent_control_plane.orchestration.deployment_spec import DeploymentSpec
from redis_agent_control_plane.orchestration.router import RunbookRouter
from redis_agent_control_plane.orchestration.runbook import Runbook

__all__ = [
    "DeploymentSpec",
    "Runbook",
    "RunbookRouter",
]
