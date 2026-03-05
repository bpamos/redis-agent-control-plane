"""DeploymentSpec: Structured input contract for deployment intent.

This module defines the DeploymentSpec dataclass that captures deployment intent
in a structured, validated format. The spec is used by the RunbookRouter to
deterministically select the appropriate runbook.
"""

from dataclasses import dataclass, field
from enum import StrEnum


class Product(StrEnum):
    """Redis product variants."""

    REDIS_ENTERPRISE = "redis_enterprise"
    REDIS_CLOUD = "redis_cloud"
    REDIS_STACK = "redis_stack"


class Platform(StrEnum):
    """Deployment platforms."""

    VM = "vm"
    KUBERNETES = "kubernetes"
    EKS = "eks"
    GKE = "gke"
    AKS = "aks"
    OPENSHIFT = "openshift"
    # For Redis Cloud, platform is the cloud provider
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class Topology(StrEnum):
    """Deployment topologies."""

    SINGLE_NODE = "single_node"
    CLUSTERED = "clustered"
    ACTIVE_ACTIVE = "active_active"
    # For Redis Cloud, VPC peering is a deployment variant
    VPC_PEERING = "vpc_peering"


class CloudProvider(StrEnum):
    """Cloud providers."""

    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    ON_PREM = "on_prem"


class NetworkingType(StrEnum):
    """Networking types."""

    PUBLIC = "public"
    PRIVATE = "private"
    VPC_PEERING = "vpc_peering"


@dataclass
class NetworkingConfig:
    """Networking configuration."""

    type: NetworkingType
    tls_enabled: bool = True


@dataclass
class ScaleConfig:
    """Scale configuration."""

    nodes: int = 1
    shards: int = 1
    replicas: int = 1

    def __post_init__(self) -> None:
        """Validate scale configuration."""
        if self.nodes < 1:
            raise ValueError("nodes must be >= 1")
        if self.shards < 1:
            raise ValueError("shards must be >= 1")
        if self.replicas < 0:
            raise ValueError("replicas must be >= 0")


@dataclass
class DeploymentSpec:
    """Structured input contract for deployment intent.

    This dataclass captures all the information needed to deterministically
    route to the appropriate runbook for a Redis deployment.

    Attributes:
        product: Redis product variant (enterprise, cloud, stack)
        platform: Deployment platform (vm, kubernetes, eks, etc.)
        topology: Deployment topology (single_node, clustered, active_active)
        cloud_provider: Cloud provider (optional, defaults to on_prem)
        networking: Networking configuration
        scale: Scale configuration (nodes, shards, replicas)
        requirements: Additional requirements (optional)
    """

    product: Product
    platform: Platform
    topology: Topology
    networking: NetworkingConfig
    scale: ScaleConfig
    cloud_provider: CloudProvider | None = None
    requirements: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate deployment spec after initialization."""
        # Convert string values to enums if needed
        if isinstance(self.product, str):
            self.product = Product(self.product)
        if isinstance(self.platform, str):
            self.platform = Platform(self.platform)
        if isinstance(self.topology, str):
            self.topology = Topology(self.topology)
        if self.cloud_provider and isinstance(self.cloud_provider, str):
            self.cloud_provider = CloudProvider(self.cloud_provider)

        # Validate topology constraints
        if self.topology == Topology.CLUSTERED and self.scale.nodes < 3:
            raise ValueError("Clustered topology requires at least 3 nodes")
        if self.topology == Topology.ACTIVE_ACTIVE and self.scale.nodes < 2:
            raise ValueError("Active-Active topology requires at least 2 nodes")

    def to_runbook_id(self) -> str:
        """Generate runbook ID from deployment spec.

        Returns:
            Runbook ID in format: runbook.{product}.{platform}.{topology}

        Example:
            >>> spec = DeploymentSpec(...)
            >>> spec.to_runbook_id()
            'runbook.redis_enterprise.kubernetes.clustered'
        """
        return f"runbook.{self.product.value}.{self.platform.value}.{self.topology.value}"
