"""Unit tests for ContextBuilder and ContextPack."""

from unittest.mock import MagicMock

import pytest

from redis_agent_control_plane.orchestration.context_builder import ContextBuilder
from redis_agent_control_plane.orchestration.deployment_spec import (
    DeploymentSpec,
    NetworkingConfig,
    NetworkingType,
    Platform,
    Product,
    ScaleConfig,
    Topology,
)
from redis_agent_control_plane.orchestration.runbook import (
    DocReference,
    RAGAssist,
    Runbook,
    RunbookStep,
)


@pytest.fixture
def sample_deployment_spec():
    """Create a sample DeploymentSpec for testing."""
    return DeploymentSpec(
        product=Product.REDIS_ENTERPRISE,
        platform=Platform.KUBERNETES,
        topology=Topology.CLUSTERED,
        networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
        scale=ScaleConfig(nodes=3, shards=2, replicas=1),
    )


@pytest.fixture
def sample_runbook_step():
    """Create a sample RunbookStep for testing."""
    return RunbookStep(
        id="step_1",
        name="Install Redis Enterprise Operator",
        description="Install the Redis Enterprise Operator using kubectl",
        doc_refs=[
            DocReference(
                path="docs/operate/kubernetes/deployment/quick-start.md",
                section="Install the operator",
            )
        ],
        rag_assist=RAGAssist(
            query="How do I install Redis Enterprise Operator on Kubernetes?",
            filters={"category": "operate"},
            max_results=5,
        ),
    )


@pytest.fixture
def sample_runbook():
    """Create a sample Runbook for testing."""
    return Runbook(
        id="runbook.redis_enterprise.kubernetes.clustered",
        name="Redis Enterprise on Kubernetes - 3-Node Cluster",
        version="2.0.0",
        description="Deploy a 3-node Redis Enterprise cluster on Kubernetes",
        prerequisites=[],
        steps=[],
        post_validations=[],
        rollback=[],
    )


@pytest.fixture
def mock_retriever():
    """Create a mock RedisRetriever for testing."""
    retriever = MagicMock()
    retriever.search.return_value = [
        {
            "chunk_id": "redis_docs:chunk:1",
            "content": "To install the Redis Enterprise Operator...",
            "doc_path": "docs/operate/kubernetes/deployment/quick-start.md",
            "doc_url": "https://redis.io/docs/operate/kubernetes/deployment/quick-start/",
            "title": "Quick Start Guide",
            "section_heading": "Install the operator",
            "toc_path": "Operate > Kubernetes > Deployment > Quick Start",
            "category": "operate",
            "product_area": "redis_software",
            "vector_distance": 0.15,
            "chunk_index": 0,
        },
        {
            "chunk_id": "redis_docs:chunk:2",
            "content": "The operator manages Redis Enterprise clusters...",
            "doc_path": "docs/operate/kubernetes/architecture/operator.md",
            "doc_url": "https://redis.io/docs/operate/kubernetes/architecture/operator/",
            "title": "Operator Architecture",
            "section_heading": "Overview",
            "toc_path": "Operate > Kubernetes > Architecture > Operator",
            "category": "operate",
            "product_area": "redis_software",
            "vector_distance": 0.22,
            "chunk_index": 1,
        },
    ]
    return retriever


def test_context_builder_initialization():
    """Test ContextBuilder initialization."""
    builder = ContextBuilder()
    assert builder.retriever is not None
    assert builder.index_name == "redis_docs"


def test_build_context_pack_deterministic_only(
    sample_runbook, sample_runbook_step, sample_deployment_spec, mock_retriever
):
    """Test building ContextPack with deterministic doc refs only (no RAG)."""
    builder = ContextBuilder(retriever=mock_retriever)

    # Build context pack without RAG
    context_pack = builder.build_context_pack(
        runbook=sample_runbook,
        step=sample_runbook_step,
        deployment_spec=sample_deployment_spec,
        use_rag=False,
    )

    # Verify basic fields
    assert context_pack.runbook_id == sample_runbook.id
    assert context_pack.runbook_version == sample_runbook.version
    assert context_pack.step_id == sample_runbook_step.id
    assert context_pack.step_name == sample_runbook_step.name
    assert context_pack.step_description == sample_runbook_step.description

    # Verify deterministic doc refs are included
    assert len(context_pack.deterministic_doc_refs) == 1
    assert context_pack.deterministic_doc_refs[0].path == (
        "docs/operate/kubernetes/deployment/quick-start.md"
    )

    # Verify no RAG chunks
    assert len(context_pack.rag_chunks) == 0
    assert context_pack.retrieval_method == "deterministic_only"

    # Verify retriever was not called
    mock_retriever.search.assert_not_called()


def test_build_context_pack_with_rag(
    sample_runbook, sample_runbook_step, sample_deployment_spec, mock_retriever
):
    """Test building ContextPack with RAG enrichment."""
    builder = ContextBuilder(retriever=mock_retriever)

    # Build context pack with RAG
    context_pack = builder.build_context_pack(
        runbook=sample_runbook,
        step=sample_runbook_step,
        deployment_spec=sample_deployment_spec,
        use_rag=True,
        max_rag_chunks=10,
        distance_threshold=0.30,
    )

    # Verify deterministic doc refs are still included
    assert len(context_pack.deterministic_doc_refs) == 1

    # Verify RAG chunks are included
    assert len(context_pack.rag_chunks) == 2
    assert context_pack.retrieval_method == "hybrid"

    # Verify RAG chunk provenance
    assert context_pack.rag_chunks[0].chunk_id == "redis_docs:chunk:1"
    assert context_pack.rag_chunks[0].content == "To install the Redis Enterprise Operator..."
    assert context_pack.rag_chunks[0].product_area == "redis_software"
    assert context_pack.rag_chunks[0].category == "operate"
    assert context_pack.rag_chunks[0].rank == 1
    assert context_pack.rag_chunks[0].vector_distance == 0.15

    # Verify chunk_ids are tracked
    assert len(context_pack.chunk_ids) == 2
    assert context_pack.chunk_ids[0] == "redis_docs:chunk:1"

    # Verify retriever was called with correct filters
    mock_retriever.search.assert_called_once_with(
        query="How do I install Redis Enterprise Operator on Kubernetes?",
        top_k=10,
        distance_threshold=0.30,
        product_area="redis_software",  # redis_enterprise -> redis_software
        category="operate",
        use_index=True,
    )


def test_product_area_mapping(mock_retriever):
    """Test product to product_area mapping."""
    builder = ContextBuilder(retriever=mock_retriever)

    # Test redis_enterprise -> redis_software
    assert builder._map_product_to_product_area("redis_enterprise") == "redis_software"

    # Test redis_cloud -> redis_cloud
    assert builder._map_product_to_product_area("redis_cloud") == "redis_cloud"

    # Test redis_stack -> redis_stack
    assert builder._map_product_to_product_area("redis_stack") == "redis_stack"


def test_bounded_results(
    sample_runbook, sample_runbook_step, sample_deployment_spec, mock_retriever
):
    """Test that max_rag_chunks limit is enforced."""
    # Create mock retriever with many results
    mock_retriever.search.return_value = [
        {
            "chunk_id": f"redis_docs:chunk:{i}",
            "content": f"Content {i}",
            "doc_path": "docs/test.md",
            "doc_url": "https://redis.io/docs/test/",
            "title": "Test",
            "section_heading": "Section",
            "toc_path": "Test",
            "category": "operate",
            "product_area": "redis_software",
            "vector_distance": 0.1 + (i * 0.01),
            "chunk_index": i,
        }
        for i in range(20)
    ]

    builder = ContextBuilder(retriever=mock_retriever)

    # Build context pack with max_rag_chunks=5
    builder.build_context_pack(
        runbook=sample_runbook,
        step=sample_runbook_step,
        deployment_spec=sample_deployment_spec,
        use_rag=True,
        max_rag_chunks=5,
    )

    # Verify only 5 chunks are included (bounded by max_rag_chunks)
    # Note: The retriever is called with top_k=5, so it returns 5 results
    mock_retriever.search.assert_called_once()
    call_args = mock_retriever.search.call_args
    assert call_args.kwargs["top_k"] == 5


def test_product_area_isolation_redis_enterprise(
    sample_runbook, sample_runbook_step, mock_retriever
):
    """Test product area isolation for Redis Enterprise."""
    builder = ContextBuilder(retriever=mock_retriever)

    # Create Redis Enterprise deployment spec
    deployment_spec = DeploymentSpec(
        product=Product.REDIS_ENTERPRISE,
        platform=Platform.KUBERNETES,
        topology=Topology.CLUSTERED,
        networking=NetworkingConfig(type=NetworkingType.PRIVATE, tls_enabled=True),
        scale=ScaleConfig(nodes=3, shards=2, replicas=1),
    )

    # Build context pack
    builder.build_context_pack(
        runbook=sample_runbook,
        step=sample_runbook_step,
        deployment_spec=deployment_spec,
        use_rag=True,
    )

    # Verify retriever was called with product_area="redis_software"
    mock_retriever.search.assert_called_once()
    call_args = mock_retriever.search.call_args
    assert call_args.kwargs["product_area"] == "redis_software"


def test_product_area_isolation_redis_cloud(sample_runbook, sample_runbook_step, mock_retriever):
    """Test product area isolation for Redis Cloud."""
    builder = ContextBuilder(retriever=mock_retriever)

    # Create Redis Cloud deployment spec
    deployment_spec = DeploymentSpec(
        product=Product.REDIS_CLOUD,
        platform=Platform.AWS,
        topology=Topology.SINGLE_NODE,
        networking=NetworkingConfig(type=NetworkingType.PUBLIC, tls_enabled=True),
        scale=ScaleConfig(nodes=1, shards=1, replicas=0),
    )

    # Build context pack
    builder.build_context_pack(
        runbook=sample_runbook,
        step=sample_runbook_step,
        deployment_spec=deployment_spec,
        use_rag=True,
    )

    # Verify retriever was called with product_area="redis_cloud"
    mock_retriever.search.assert_called_once()
    call_args = mock_retriever.search.call_args
    assert call_args.kwargs["product_area"] == "redis_cloud"


def test_provenance_tracking(
    sample_runbook, sample_runbook_step, sample_deployment_spec, mock_retriever
):
    """Test that provenance is tracked for all chunks."""
    builder = ContextBuilder(retriever=mock_retriever)

    # Build context pack
    context_pack = builder.build_context_pack(
        runbook=sample_runbook,
        step=sample_runbook_step,
        deployment_spec=sample_deployment_spec,
        use_rag=True,
    )

    # Verify provenance fields
    assert context_pack.index_name == "redis_docs"
    assert len(context_pack.chunk_ids) == 2
    assert context_pack.retrieval_timestamp != ""
    assert context_pack.retrieval_method == "hybrid"

    # Verify each chunk has full provenance
    for chunk in context_pack.rag_chunks:
        assert chunk.chunk_id != ""
        assert chunk.doc_path != ""
        assert chunk.product_area != ""
        assert chunk.category != ""
        assert chunk.rank > 0


def test_step_without_rag_assist(sample_runbook, sample_deployment_spec, mock_retriever):
    """Test building ContextPack for step without rag_assist."""
    builder = ContextBuilder(retriever=mock_retriever)

    # Create step without rag_assist
    step = RunbookStep(
        id="step_2",
        name="Manual Configuration",
        description="Manually configure the cluster",
        doc_refs=[
            DocReference(
                path="docs/operate/kubernetes/configuration.md",
                section="Configuration",
            )
        ],
        rag_assist=None,  # No RAG assist
    )

    # Build context pack
    context_pack = builder.build_context_pack(
        runbook=sample_runbook,
        step=step,
        deployment_spec=sample_deployment_spec,
        use_rag=True,  # Even with use_rag=True, no RAG if step has no rag_assist
    )

    # Verify deterministic doc refs are included
    assert len(context_pack.deterministic_doc_refs) == 1

    # Verify no RAG chunks (step has no rag_assist)
    assert len(context_pack.rag_chunks) == 0
    assert context_pack.retrieval_method == "deterministic_only"

    # Verify retriever was not called
    mock_retriever.search.assert_not_called()


def test_context_pack_serialization(
    sample_runbook, sample_runbook_step, sample_deployment_spec, mock_retriever
):
    """Test ContextPack serialization to dict and JSON."""
    builder = ContextBuilder(retriever=mock_retriever)

    # Build context pack
    context_pack = builder.build_context_pack(
        runbook=sample_runbook,
        step=sample_runbook_step,
        deployment_spec=sample_deployment_spec,
        use_rag=True,
    )

    # Test to_dict()
    data = context_pack.to_dict()
    assert isinstance(data, dict)
    assert data["runbook_id"] == sample_runbook.id
    assert data["step_id"] == sample_runbook_step.id
    assert data["plan_version"] == "1.0.0"
    assert data["spec_version"] == "1.0.0"
    assert "deployment_spec" in data
    assert isinstance(data["deployment_spec"], dict)
    assert isinstance(data["deterministic_doc_refs"], list)
    assert isinstance(data["rag_chunks"], list)

    # Test to_json()
    json_str = context_pack.to_json()
    assert isinstance(json_str, str)
    assert "runbook_id" in json_str
    assert "plan_version" in json_str


def test_context_pack_deserialization(
    sample_runbook, sample_runbook_step, sample_deployment_spec, mock_retriever
):
    """Test ContextPack deserialization from dict and JSON."""
    builder = ContextBuilder(retriever=mock_retriever)

    # Build context pack
    original = builder.build_context_pack(
        runbook=sample_runbook,
        step=sample_runbook_step,
        deployment_spec=sample_deployment_spec,
        use_rag=True,
    )

    # Serialize to dict
    data = original.to_dict()

    # Deserialize from dict
    from redis_agent_control_plane.orchestration.context_pack import ContextPack

    restored = ContextPack.from_dict(data)

    # Verify fields match
    assert restored.runbook_id == original.runbook_id
    assert restored.runbook_version == original.runbook_version
    assert restored.step_id == original.step_id
    assert restored.step_name == original.step_name
    assert restored.plan_version == original.plan_version
    assert restored.spec_version == original.spec_version
    assert len(restored.deterministic_doc_refs) == len(original.deterministic_doc_refs)
    assert len(restored.rag_chunks) == len(original.rag_chunks)

    # Test from_json()
    json_str = original.to_json()
    restored_from_json = ContextPack.from_json(json_str)
    assert restored_from_json.runbook_id == original.runbook_id


def test_deployment_spec_serialization(sample_deployment_spec):
    """Test DeploymentSpec serialization and deserialization."""
    # Serialize to dict
    data = sample_deployment_spec.to_dict()
    assert isinstance(data, dict)
    assert data["product"] == "redis_enterprise"
    assert data["platform"] == "kubernetes"
    assert data["topology"] == "clustered"
    assert "networking" in data
    assert "scale" in data

    # Deserialize from dict
    from redis_agent_control_plane.orchestration.deployment_spec import DeploymentSpec

    restored = DeploymentSpec.from_dict(data)
    assert restored.product == sample_deployment_spec.product
    assert restored.platform == sample_deployment_spec.platform
    assert restored.topology == sample_deployment_spec.topology
    assert restored.networking.type == sample_deployment_spec.networking.type
    assert restored.scale.nodes == sample_deployment_spec.scale.nodes


def test_rag_chunk_serialization():
    """Test RAGChunk serialization and deserialization."""
    from redis_agent_control_plane.orchestration.context_pack import RAGChunk

    # Create a RAGChunk
    chunk = RAGChunk(
        content="Test content",
        doc_path="docs/test.md",
        doc_url="https://redis.io/docs/test/",
        title="Test Document",
        section_heading="Test Section",
        toc_path="Test > Section",
        category="operate",
        product_area="redis_software",
        chunk_id="redis_docs:chunk:test",
        chunk_index=0,
        vector_distance=0.15,
        rank=1,
        why_included="semantic_match",
    )

    # Serialize to dict
    data = chunk.to_dict()
    assert isinstance(data, dict)
    assert data["content"] == "Test content"
    assert data["category"] == "operate"
    assert data["chunk_id"] == "redis_docs:chunk:test"

    # Deserialize from dict
    restored = RAGChunk.from_dict(data)
    assert restored.content == chunk.content
    assert restored.category == chunk.category
    assert restored.chunk_id == chunk.chunk_id


def test_context_pack_version_fields(
    sample_runbook, sample_runbook_step, sample_deployment_spec, mock_retriever
):
    """Test that ContextPack has version fields."""
    builder = ContextBuilder(retriever=mock_retriever)

    # Build context pack
    context_pack = builder.build_context_pack(
        runbook=sample_runbook,
        step=sample_runbook_step,
        deployment_spec=sample_deployment_spec,
        use_rag=False,
    )

    # Verify version fields exist
    assert hasattr(context_pack, "plan_version")
    assert hasattr(context_pack, "spec_version")
    assert context_pack.plan_version == "1.0.0"
    assert context_pack.spec_version == "1.0.0"

    # Verify version fields are in serialized output
    data = context_pack.to_dict()
    assert "plan_version" in data
    assert "spec_version" in data
    assert data["plan_version"] == "1.0.0"
    assert data["spec_version"] == "1.0.0"
