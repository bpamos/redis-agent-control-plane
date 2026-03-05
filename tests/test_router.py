"""Unit tests for RunbookRouter with determinism validation."""

from pathlib import Path

import pytest

from redis_agent_control_plane.orchestration.deployment_spec import (
    DeploymentSpec,
    NetworkingConfig,
    NetworkingType,
    Platform,
    Product,
    ScaleConfig,
    Topology,
)
from redis_agent_control_plane.orchestration.router import (
    RunbookNotFoundError,
    RunbookRouter,
)


@pytest.fixture
def router():
    """Create a router instance for testing."""
    return RunbookRouter()


def test_router_initialization(router):
    """Test router initialization."""
    assert router.runbooks_dir is not None
    assert isinstance(router.runbooks_dir, Path)


def test_router_route_kubernetes_clustered(router):
    """Test routing to Kubernetes clustered runbook."""
    spec = DeploymentSpec(
        product=Product.REDIS_ENTERPRISE,
        platform=Platform.KUBERNETES,
        topology=Topology.CLUSTERED,
        networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
        scale=ScaleConfig(nodes=3, shards=2, replicas=1),
    )

    runbook_id = router.route(spec)
    assert runbook_id == "runbook.redis_enterprise.kubernetes.clustered"


def test_router_route_vm_single_node(router):
    """Test routing to VM single-node runbook."""
    spec = DeploymentSpec(
        product=Product.REDIS_ENTERPRISE,
        platform=Platform.VM,
        topology=Topology.SINGLE_NODE,
        networking=NetworkingConfig(type=NetworkingType.PUBLIC, tls_enabled=False),
        scale=ScaleConfig(nodes=1, shards=1, replicas=0),
    )

    runbook_id = router.route(spec)
    assert runbook_id == "runbook.redis_enterprise.vm.single_node"


def test_router_route_redis_cloud(router):
    """Test routing to Redis Cloud runbook."""
    spec = DeploymentSpec(
        product=Product.REDIS_CLOUD,
        platform=Platform.AWS,
        topology=Topology.VPC_PEERING,
        networking=NetworkingConfig(type=NetworkingType.VPC_PEERING, tls_enabled=True),
        scale=ScaleConfig(nodes=3, shards=2, replicas=1),
    )

    runbook_id = router.route(spec)
    assert runbook_id == "runbook.redis_cloud.aws.vpc_peering"


def test_router_determinism_100_iterations(router):
    """Test that routing is deterministic over 100 iterations.

    Same DeploymentSpec should always produce the same runbook_id.
    """
    spec = DeploymentSpec(
        product=Product.REDIS_ENTERPRISE,
        platform=Platform.KUBERNETES,
        topology=Topology.CLUSTERED,
        networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
        scale=ScaleConfig(nodes=3, shards=2, replicas=1),
    )

    # Route 100 times and collect results
    results = [router.route(spec) for _ in range(100)]

    # All results should be identical
    assert len(set(results)) == 1
    assert results[0] == "runbook.redis_enterprise.kubernetes.clustered"


def test_router_determinism_different_specs(router):
    """Test that different specs produce different runbook IDs."""
    spec1 = DeploymentSpec(
        product=Product.REDIS_ENTERPRISE,
        platform=Platform.KUBERNETES,
        topology=Topology.CLUSTERED,
        networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
        scale=ScaleConfig(nodes=3, shards=2, replicas=1),
    )

    spec2 = DeploymentSpec(
        product=Product.REDIS_ENTERPRISE,
        platform=Platform.VM,
        topology=Topology.SINGLE_NODE,
        networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
        scale=ScaleConfig(nodes=1, shards=1, replicas=0),
    )

    runbook_id1 = router.route(spec1)
    runbook_id2 = router.route(spec2)

    assert runbook_id1 != runbook_id2
    assert runbook_id1 == "runbook.redis_enterprise.kubernetes.clustered"
    assert runbook_id2 == "runbook.redis_enterprise.vm.single_node"


def test_router_runbook_not_found(router):
    """Test error handling when runbook doesn't exist."""
    spec = DeploymentSpec(
        product=Product.REDIS_STACK,
        platform=Platform.KUBERNETES,
        topology=Topology.CLUSTERED,
        networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
        scale=ScaleConfig(nodes=3, shards=2, replicas=1),
    )

    with pytest.raises(RunbookNotFoundError, match="No runbook found"):
        router.route(spec)


def test_router_has_runbook(router):
    """Test checking if runbook exists."""
    # Should exist
    assert router.has_runbook("runbook.redis_enterprise.kubernetes.clustered")

    # Should not exist
    assert not router.has_runbook("runbook.nonexistent.platform.topology")


def test_router_load_runbook(router):
    """Test loading a runbook by ID."""
    runbook = router.load_runbook("runbook.redis_enterprise.kubernetes.clustered")

    assert runbook.id == "runbook.redis_enterprise.kubernetes.clustered"
    assert len(runbook.steps) > 0


def test_router_load_runbook_not_found(router):
    """Test error handling when loading non-existent runbook."""
    with pytest.raises(RunbookNotFoundError, match="Runbook file not found"):
        router.load_runbook("runbook.nonexistent.platform.topology")


def test_router_list_available_runbooks(router):
    """Test listing all available runbooks."""
    runbooks = router.list_available_runbooks()

    assert isinstance(runbooks, list)
    assert len(runbooks) > 0
    assert "runbook.redis_enterprise.kubernetes.clustered" in runbooks
    assert all(rb.startswith("runbook.") for rb in runbooks)


# ============================================================================
# Registry-Based Routing Tests
# ============================================================================


@pytest.fixture
def router_with_registry():
    """Create a router instance with registry enabled."""
    return RunbookRouter(use_registry=True)


@pytest.fixture
def router_without_registry():
    """Create a router instance with registry disabled."""
    return RunbookRouter(use_registry=False)


def test_registry_loading(router_with_registry):
    """Test that registry is loaded on initialization."""
    assert router_with_registry._registry is not None
    assert "registry_version" in router_with_registry._registry
    assert "runbooks" in router_with_registry._registry


def test_registry_route_kubernetes_clustered(router_with_registry):
    """Test registry-based routing to Kubernetes clustered runbook."""
    spec = DeploymentSpec(
        product=Product.REDIS_ENTERPRISE,
        platform=Platform.KUBERNETES,
        topology=Topology.CLUSTERED,
        networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
        scale=ScaleConfig(nodes=3, shards=2, replicas=1),
    )

    runbook_id = router_with_registry.route(spec)
    assert runbook_id == "runbook.redis_enterprise.kubernetes.clustered"


def test_registry_route_vm_single_node(router_with_registry):
    """Test registry-based routing to VM single-node runbook."""
    spec = DeploymentSpec(
        product=Product.REDIS_ENTERPRISE,
        platform=Platform.VM,
        topology=Topology.SINGLE_NODE,
        networking=NetworkingConfig(type=NetworkingType.PUBLIC, tls_enabled=False),
        scale=ScaleConfig(nodes=1, shards=1, replicas=0),
    )

    runbook_id = router_with_registry.route(spec)
    assert runbook_id == "runbook.redis_enterprise.vm.single_node"


def test_registry_route_active_active(router_with_registry):
    """Test registry-based routing to Active-Active runbook."""
    spec = DeploymentSpec(
        product=Product.REDIS_ENTERPRISE,
        platform=Platform.KUBERNETES,
        topology=Topology.ACTIVE_ACTIVE,
        networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
        scale=ScaleConfig(nodes=2, shards=2, replicas=1),
    )

    runbook_id = router_with_registry.route(spec)
    assert runbook_id == "runbook.redis_enterprise.kubernetes.active_active"


def test_registry_route_not_found(router_with_registry):
    """Test error handling when no registry entry matches."""
    spec = DeploymentSpec(
        product=Product.REDIS_STACK,
        platform=Platform.KUBERNETES,
        topology=Topology.CLUSTERED,
        networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
        scale=ScaleConfig(nodes=3, shards=2, replicas=1),
    )

    with pytest.raises(RunbookNotFoundError, match="No runbook found"):
        router_with_registry.route(spec)


def test_registry_determinism(router_with_registry):
    """Test that registry-based routing is deterministic."""
    spec = DeploymentSpec(
        product=Product.REDIS_ENTERPRISE,
        platform=Platform.KUBERNETES,
        topology=Topology.CLUSTERED,
        networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
        scale=ScaleConfig(nodes=3, shards=2, replicas=1),
    )

    # Route 100 times and collect results
    results = [router_with_registry.route(spec) for _ in range(100)]

    # All results should be identical
    assert len(set(results)) == 1
    assert results[0] == "runbook.redis_enterprise.kubernetes.clustered"


def test_registry_list_available_runbooks(router_with_registry):
    """Test listing runbooks from registry."""
    runbooks = router_with_registry.list_available_runbooks()

    assert isinstance(runbooks, list)
    assert len(runbooks) == 10  # We have 10 runbooks in registry
    assert "runbook.redis_enterprise.kubernetes.clustered" in runbooks
    assert "runbook.redis_enterprise.vm.single_node" in runbooks


def test_backward_compatibility_without_registry(router_without_registry):
    """Test that routing still works without registry (backward compatibility)."""
    spec = DeploymentSpec(
        product=Product.REDIS_ENTERPRISE,
        platform=Platform.KUBERNETES,
        topology=Topology.CLUSTERED,
        networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
        scale=ScaleConfig(nodes=3, shards=2, replicas=1),
    )

    runbook_id = router_without_registry.route(spec)
    assert runbook_id == "runbook.redis_enterprise.kubernetes.clustered"


def test_registry_matches_selectors():
    """Test selector matching logic."""
    router = RunbookRouter(use_registry=True)

    spec = DeploymentSpec(
        product=Product.REDIS_ENTERPRISE,
        platform=Platform.KUBERNETES,
        topology=Topology.CLUSTERED,
        networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
        scale=ScaleConfig(nodes=3, shards=2, replicas=1),
    )

    # Test matching selectors
    selectors = {
        "product": "redis_enterprise",
        "platform": "kubernetes",
        "topology": "clustered",
    }
    assert router._matches_selectors(spec, selectors) is True

    # Test non-matching selectors
    selectors_wrong = {
        "product": "redis_cloud",
        "platform": "kubernetes",
        "topology": "clustered",
    }
    assert router._matches_selectors(spec, selectors_wrong) is False
