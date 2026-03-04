# Phase 3 Quick Start Guide

**New Features:** FT.CREATE Index + Hybrid Search

---

## Overview

Phase 3 adds two major enhancements to the RAG pipeline:
1. **FT.CREATE Index** - 10-100x faster vector search with HNSW
2. **Hybrid Search** - Combined vector + BM25 text search with RRF

---

## Quick Start

### 1. Create the FT.CREATE Index

```python
from redis_agent_control_plane.rag.indexer import RedisIndexer

# Create indexer
indexer = RedisIndexer(
    redis_url="redis://localhost:6379",
    index_name="redis_docs"
)

# Create index (idempotent - safe to run multiple times)
indexer.create_index(overwrite=False)

# Get index info
info = indexer.get_index_info()
print(f"Documents: {info['num_docs']}")
print(f"Records: {info['num_records']}")
```

### 2. Use FT.SEARCH for Fast Vector Search

```python
from redis_agent_control_plane.rag.embedder import Embedder
from redis_agent_control_plane.rag.retriever import RedisRetriever

# Create retriever
embedder = Embedder()
retriever = RedisRetriever(
    redis_url="redis://localhost:6379",
    index_name="redis_docs",
    embedder=embedder
)

# Search with FT.SEARCH (default, 10-100x faster)
results = retriever.search(
    query="How do I configure Active-Active replication?",
    top_k=5,
    use_index=True  # Default: True
)

# Display results
for i, result in enumerate(results, 1):
    print(f"{i}. {result['section_heading']}")
    print(f"   Distance: {result['vector_distance']:.3f}")
    print(f"   Content: {result['content'][:100]}...")
```

### 3. Use Hybrid Search for Exact + Semantic Queries

```python
# Hybrid search (vector + BM25 text search)
results = retriever.hybrid_search(
    query="CONFIG SET maxmemory",
    top_k=5,
    vector_weight=0.7,  # 70% vector similarity
    text_weight=0.3,    # 30% text matching
    rrf_k=60            # RRF constant
)

# Display results with scores
for i, result in enumerate(results, 1):
    print(f"{i}. {result['section_heading']}")
    print(f"   Hybrid: {result['hybrid_score']:.4f}")
    print(f"   Vector: {result['vector_score']:.4f} (rank {result['vector_rank']})")
    print(f"   Text: {result['text_score']:.4f} (rank {result['text_rank']})")
```

### 4. Use Filtered Search

```python
# Filter by product area
results = retriever.search(
    query="How do I configure replication?",
    top_k=5,
    product_area="redis_software",
    use_index=True
)

# Filter by category
results = retriever.search(
    query="How do I deploy Redis?",
    top_k=5,
    category="operate",
    use_index=True
)

# Filter by both
results = retriever.search(
    query="How do I integrate Redis?",
    top_k=5,
    product_area="redis_cloud",
    category="integrate",
    use_index=True
)
```

---

## When to Use What

### Use Vector-Only Search (`search()`)
- ✅ Semantic queries: "How do I configure memory limits?"
- ✅ Conceptual questions: "What are the best practices?"
- ✅ General exploration: "Tell me about replication"

### Use Hybrid Search (`hybrid_search()`)
- ✅ Exact commands: "CONFIG SET maxmemory"
- ✅ Config parameters: "maxmemory-policy allkeys-lru"
- ✅ API methods: "HSET key field value"
- ✅ Mixed queries: "eviction policy configuration"

### Use Filtered Search
- ✅ Product-specific: "How do I deploy Redis Cloud?"
- ✅ Category-specific: "How do I operate Redis?"
- ✅ Narrow scope: "Redis Stack integration guides"

---

## Testing

### Test FT.CREATE Index

```bash
source venv/bin/activate
python3 scripts/test_ft_search.py
```

**Expected output:**
```
✓ Index exists: redis_docs
✓ Documents: 260
✓ Records: 23,064
✓ FT.SEARCH 10-20x faster than brute-force
```

### Test Hybrid Search

```bash
python3 scripts/test_hybrid_search.py
```

**Expected output:**
```
✓ Hybrid search combines vector + text signals
✓ Exact commands rank higher with text matching
✓ Semantic queries rank higher with vector search
```

### Run Comprehensive Validation

```bash
python3 scripts/test_phase3_validation.py
```

**Expected output:**
```
✓ Index operational
✓ FT.SEARCH 10-20x faster
✓ Hybrid search working
✓ Filtered search working
✓ P95 latency < 100ms
```

---

## Advanced Usage

### Adjust Hybrid Search Weights

```python
# More weight on text matching (good for exact commands)
results = retriever.hybrid_search(
    query="CONFIG SET maxmemory",
    vector_weight=0.3,  # 30% vector
    text_weight=0.7     # 70% text
)

# More weight on vector similarity (good for semantic queries)
results = retriever.hybrid_search(
    query="How do I configure memory?",
    vector_weight=0.9,  # 90% vector
    text_weight=0.1     # 10% text
)
```

### Fallback to Brute-Force

```python
# Use brute-force if index is not available
results = retriever.search(
    query="How do I configure Redis?",
    top_k=5,
    use_index=False  # Force brute-force
)
```

### Index Management

```python
# Drop index (keep data)
indexer.drop_index(delete_docs=False)

# Drop index and data
indexer.drop_index(delete_docs=True)

# Recreate index
indexer.create_index(overwrite=True)
```

---

## Performance Tips

1. **Always use `use_index=True`** (default) for production queries
2. **Use hybrid search** for diverse query types (commands, configs, semantic)
3. **Use filters** to narrow scope and improve precision
4. **Adjust weights** based on query type (exact vs semantic)
5. **Monitor latency** - target P95 < 100ms

---

## Troubleshooting

### Index not found
```python
# Create index
indexer.create_index(overwrite=False)
```

### Slow queries
```python
# Check if using index
results = retriever.search(query="...", use_index=True)

# Check index info
info = indexer.get_index_info()
print(info)
```

### Poor results
```python
# Try hybrid search
results = retriever.hybrid_search(query="...")

# Adjust weights
results = retriever.hybrid_search(
    query="...",
    vector_weight=0.5,
    text_weight=0.5
)
```

---

## Next Steps

1. ✅ Test the new features with your queries
2. ✅ Integrate into agent control plane
3. ✅ Monitor performance and quality
4. ✅ Adjust weights and filters as needed

---

## References

- **Full Documentation:** `docs/RAG_PIPELINE.md`
- **Phase 3 Complete:** `notes/PHASE_3_COMPLETE.md`
- **Executive Summary:** `notes/PHASE_3_EXECUTIVE_SUMMARY.md`

