"""Unit tests for DeploymentSpec dataclass."""

import pytest

from redis_agent_control_plane.orchestration.deployment_spec import (
    CloudProvider,
    DeploymentSpec,
    NetworkingConfig,
    NetworkingType,
    Platform,
    Product,
    ScaleConfig,
    Topology,
)


def test_deployment_spec_creation():
    """Test creating a valid DeploymentSpec."""
    spec = DeploymentSpec(
        product=Product.REDIS_ENTERPRISE,
        platform=Platform.KUBERNETES,
        topology=Topology.CLUSTERED,
        networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
        scale=ScaleConfig(nodes=3, shards=2, replicas=1),
        cloud_provider=CloudProvider.AWS,
        requirements=["high_availability"],
    )

    assert spec.product == Product.REDIS_ENTERPRISE
    assert spec.platform == Platform.KUBERNETES
    assert spec.topology == Topology.CLUSTERED
    assert spec.cloud_provider == CloudProvider.AWS
    assert spec.networking.type == NetworkingType.PRIVATE
    assert spec.networking.tls_enabled is True
    assert spec.scale.nodes == 3
    assert spec.scale.shards == 2
    assert spec.scale.replicas == 1
    assert spec.requirements == ["high_availability"]


def test_deployment_spec_from_strings():
    """Test creating DeploymentSpec with string values (auto-converted to enums)."""
    spec = DeploymentSpec(
        product="redis_enterprise",
        platform="kubernetes",
        topology="clustered",
        networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
        scale=ScaleConfig(nodes=3, shards=2, replicas=1),
        cloud_provider="aws",
    )

    assert spec.product == Product.REDIS_ENTERPRISE
    assert spec.platform == Platform.KUBERNETES
    assert spec.topology == Topology.CLUSTERED
    assert spec.cloud_provider == CloudProvider.AWS


def test_deployment_spec_to_runbook_id():
    """Test generating runbook ID from DeploymentSpec."""
    spec = DeploymentSpec(
        product=Product.REDIS_ENTERPRISE,
        platform=Platform.KUBERNETES,
        topology=Topology.CLUSTERED,
        networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
        scale=ScaleConfig(nodes=3, shards=2, replicas=1),
    )

    runbook_id = spec.to_runbook_id()
    assert runbook_id == "runbook.redis_enterprise.kubernetes.clustered"


def test_deployment_spec_clustered_validation():
    """Test validation: clustered topology requires at least 3 nodes."""
    with pytest.raises(ValueError, match="Clustered topology requires at least 3 nodes"):
        DeploymentSpec(
            product=Product.REDIS_ENTERPRISE,
            platform=Platform.KUBERNETES,
            topology=Topology.CLUSTERED,
            networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
            scale=ScaleConfig(nodes=2, shards=1, replicas=1),  # Only 2 nodes - invalid
        )


def test_deployment_spec_active_active_validation():
    """Test validation: active-active topology requires at least 2 nodes."""
    with pytest.raises(ValueError, match="Active-Active topology requires at least 2 nodes"):
        DeploymentSpec(
            product=Product.REDIS_ENTERPRISE,
            platform=Platform.KUBERNETES,
            topology=Topology.ACTIVE_ACTIVE,
            networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
            scale=ScaleConfig(nodes=1, shards=1, replicas=1),  # Only 1 node - invalid
        )


def test_scale_config_validation():
    """Test ScaleConfig validation."""
    # Valid scale config
    scale = ScaleConfig(nodes=3, shards=2, replicas=1)
    assert scale.nodes == 3
    assert scale.shards == 2
    assert scale.replicas == 1

    # Invalid: nodes < 1
    with pytest.raises(ValueError, match="nodes must be >= 1"):
        ScaleConfig(nodes=0, shards=1, replicas=1)

    # Invalid: shards < 1
    with pytest.raises(ValueError, match="shards must be >= 1"):
        ScaleConfig(nodes=1, shards=0, replicas=1)

    # Invalid: replicas < 0
    with pytest.raises(ValueError, match="replicas must be >= 0"):
        ScaleConfig(nodes=1, shards=1, replicas=-1)


def test_deployment_spec_single_node():
    """Test single-node deployment spec."""
    spec = DeploymentSpec(
        product=Product.REDIS_ENTERPRISE,
        platform=Platform.VM,
        topology=Topology.SINGLE_NODE,
        networking=NetworkingConfig(type=NetworkingType.PUBLIC, tls_enabled=False),
        scale=ScaleConfig(nodes=1, shards=1, replicas=0),
    )

    assert spec.topology == Topology.SINGLE_NODE
    assert spec.scale.nodes == 1
    assert spec.to_runbook_id() == "runbook.redis_enterprise.vm.single_node"


def test_deployment_spec_redis_cloud():
    """Test Redis Cloud deployment spec."""
    spec = DeploymentSpec(
        product=Product.REDIS_CLOUD,
        platform=Platform.AWS,
        topology=Topology.CLUSTERED,
        networking=NetworkingConfig(type=NetworkingType.VPC_PEERING, tls_enabled=True),
        scale=ScaleConfig(nodes=3, shards=2, replicas=1),
        cloud_provider=CloudProvider.AWS,
    )

    assert spec.product == Product.REDIS_CLOUD
    assert spec.networking.type == NetworkingType.VPC_PEERING
    assert spec.to_runbook_id() == "runbook.redis_cloud.aws.clustered"
