"""Tests for RAG indexer."""

import pytest

from redis_agent_control_plane.rag.chunker import Chunk
from redis_agent_control_plane.rag.indexer import RedisIndexer, create_index_schema


def test_create_index_schema():
    """Test index schema creation."""
    schema = create_index_schema(index_name="test_index", vector_dims=384)

    assert schema["index"]["name"] == "test_index"
    assert schema["index"]["prefix"] == "test_index:chunk:"
    assert len(schema["fields"]) == 13

    # Check for required fields
    field_names = [field["name"] for field in schema["fields"]]
    assert "source" in field_names
    assert "doc_path" in field_names
    assert "title" in field_names
    assert "category" in field_names
    assert "product_area" in field_names
    assert "content" in field_names
    assert "embedding" in field_names

    # Check vector field
    vector_field = next(f for f in schema["fields"] if f["name"] == "embedding")
    assert vector_field["type"] == "vector"
    assert vector_field["attrs"]["dims"] == 384
    assert vector_field["attrs"]["distance_metric"] == "cosine"


@pytest.mark.skip(reason="Requires Redis to be running")
def test_redis_indexer_initialization():
    """Test Redis indexer initialization."""
    indexer = RedisIndexer(
        redis_url="redis://localhost:6379",
        index_name="test_index",
        vector_dims=384,
    )

    assert indexer.index_name == "test_index"
    assert indexer.vector_dims == 384


@pytest.mark.skip(reason="Requires Redis to be running")
def test_redis_indexer_create_index():
    """Test creating Redis index."""
    indexer = RedisIndexer(
        redis_url="redis://localhost:6379",
        index_name="test_index",
        vector_dims=384,
    )

    # Create index
    indexer.create_index(overwrite=True)


@pytest.mark.skip(reason="Requires Redis to be running")
def test_redis_indexer_index_chunk():
    """Test indexing a single chunk."""
    indexer = RedisIndexer(
        redis_url="redis://localhost:6379",
        index_name="test_index",
        vector_dims=384,
    )

    # Create index
    indexer.create_index(overwrite=True)

    # Create test chunk
    chunk = Chunk(
        content="This is a test chunk about Redis.",
        source="redis/docs",
        doc_path="content/operate/rs/databases.md",
        doc_url="https://redis.io/docs/latest/operate/rs/databases/",
        title="Databases",
        category="operate",
        product_area="redis_software",
        section_heading="Overview",
        toc_path="operate > rs > databases > Overview",
        chunk_id="test_chunk_001",
        chunk_index=0,
        subchunk_index=0,
    )

    # Create test embedding
    embedding = [0.1] * 384

    # Index chunk
    indexer.index_chunk(chunk, embedding)


@pytest.mark.skip(reason="Requires Redis to be running")
def test_redis_indexer_index_chunks():
    """Test indexing multiple chunks."""
    indexer = RedisIndexer(
        redis_url="redis://localhost:6379",
        index_name="test_index",
        vector_dims=384,
    )

    # Create index
    indexer.create_index(overwrite=True)

    # Create test chunks
    chunks = [
        Chunk(
            content=f"This is test chunk {i} about Redis.",
            source="redis/docs",
            doc_path="content/operate/rs/databases.md",
            doc_url="https://redis.io/docs/latest/operate/rs/databases/",
            title="Databases",
            category="operate",
            product_area="redis_software",
            section_heading=f"Section {i}",
            toc_path=f"operate > rs > databases > Section {i}",
            chunk_id=f"test_chunk_{i:03d}",
            chunk_index=i,
            subchunk_index=0,
        )
        for i in range(5)
    ]

    # Create test embeddings
    embeddings = [[0.1 * i] * 384 for i in range(5)]

    # Index chunks
    indexer.index_chunks(chunks, embeddings)
