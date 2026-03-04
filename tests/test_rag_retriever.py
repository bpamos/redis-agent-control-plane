"""Tests for RAG retriever."""

import pytest

from redis_agent_control_plane.rag.retriever import RedisRetriever


@pytest.mark.skip(reason="Requires Redis to be running")
def test_redis_retriever_initialization():
    """Test Redis retriever initialization."""
    retriever = RedisRetriever(
        redis_url="redis://localhost:6379",
        index_name="test_index",
    )

    assert retriever.index_name == "test_index"
    assert retriever.embedder is not None


@pytest.mark.skip(reason="Requires Redis to be running")
def test_redis_retriever_search():
    """Test basic search."""
    retriever = RedisRetriever(
        redis_url="redis://localhost:6379",
        index_name="redis_docs",
    )

    results = retriever.search(
        query="How do I set up Active-Active replication?",
        top_k=5,
        distance_threshold=0.30,
    )

    assert isinstance(results, list)


@pytest.mark.skip(reason="Requires Redis to be running")
def test_redis_retriever_search_with_filters():
    """Test search with filters."""
    retriever = RedisRetriever(
        redis_url="redis://localhost:6379",
        index_name="redis_docs",
    )

    results = retriever.search(
        query="How do I configure databases?",
        top_k=5,
        distance_threshold=0.30,
        product_area="redis_software",
        category="operate",
    )

    assert isinstance(results, list)


@pytest.mark.skip(reason="Requires Redis to be running")
def test_redis_retriever_search_with_custom_filters():
    """Test search with custom filters."""
    retriever = RedisRetriever(
        redis_url="redis://localhost:6379",
        index_name="redis_docs",
    )

    results = retriever.search_with_filters(
        query="How do I configure databases?",
        filters={"product_area": "redis_software", "category": "operate"},
        top_k=5,
        distance_threshold=0.30,
    )

    assert isinstance(results, list)


def test_redis_retriever_deduplicate_results():
    """Test result deduplication."""
    retriever = RedisRetriever(
        redis_url="redis://localhost:6379",
        index_name="test_index",
    )

    # Create mock results
    results = [
        {"doc_path": "doc1.md", "vector_distance": 0.1, "content": "chunk1"},
        {"doc_path": "doc1.md", "vector_distance": 0.2, "content": "chunk2"},
        {"doc_path": "doc2.md", "vector_distance": 0.15, "content": "chunk3"},
        {"doc_path": "doc2.md", "vector_distance": 0.25, "content": "chunk4"},
    ]

    # Deduplicate - keep 1 per doc
    deduplicated = retriever.deduplicate_results(results, max_per_doc=1)

    assert len(deduplicated) == 2
    assert deduplicated[0]["doc_path"] == "doc1.md"
    assert deduplicated[0]["vector_distance"] == 0.1
    assert deduplicated[1]["doc_path"] == "doc2.md"
    assert deduplicated[1]["vector_distance"] == 0.15


def test_redis_retriever_deduplicate_results_max_2():
    """Test result deduplication with max 2 per doc."""
    retriever = RedisRetriever(
        redis_url="redis://localhost:6379",
        index_name="test_index",
    )

    # Create mock results
    results = [
        {"doc_path": "doc1.md", "vector_distance": 0.1, "content": "chunk1"},
        {"doc_path": "doc1.md", "vector_distance": 0.2, "content": "chunk2"},
        {"doc_path": "doc1.md", "vector_distance": 0.3, "content": "chunk3"},
        {"doc_path": "doc2.md", "vector_distance": 0.15, "content": "chunk4"},
    ]

    # Deduplicate - keep 2 per doc
    deduplicated = retriever.deduplicate_results(results, max_per_doc=2)

    assert len(deduplicated) == 3
    # Should keep top 2 from doc1 and 1 from doc2
    doc1_chunks = [r for r in deduplicated if r["doc_path"] == "doc1.md"]
    assert len(doc1_chunks) == 2
    assert doc1_chunks[0]["vector_distance"] == 0.1
    assert doc1_chunks[1]["vector_distance"] == 0.2
