# RAG Pipeline Documentation

## Overview

The RAG (Retrieval-Augmented Generation) pipeline ingests Redis documentation, chunks it intelligently, generates embeddings, and stores them in Redis for semantic search with hybrid retrieval capabilities.

**Phase 3 Status:** ✅ Production-ready with FT.CREATE index and hybrid search

## Architecture

```
Ingest → Chunk → Embed → Index → Retrieve (Vector + Text)
```

1. **Ingest**: Load markdown files from `../docs/content/`
2. **Chunk**: Split documents using adaptive H2/H3 strategy
3. **Embed**: Generate 384-dim vectors using sentence-transformers
4. **Index**: Store in Redis with FT.CREATE index (HNSW + BM25)
5. **Retrieve**: Hybrid search combining vector similarity and text matching

## Quick Start

### 1. Install Dependencies

```bash
make install
```

Or manually:
```bash
pip install -r requirements.txt
```

### 2. Start Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis/redis-stack-server:latest

# Or use existing Redis instance
redis-server
```

### 3. Test the Pipeline

```bash
# Run end-to-end test
python3 scripts/test_rag_pipeline.py
```

### 4. Build the Index

```bash
# Test with 10 documents
python3 scripts/build_rag_index.py --source ../docs/content/operate --limit 10 --overwrite

# Full corpus (~4,231 docs, takes 5-10 minutes)
python3 scripts/build_rag_index.py --source ../docs/content --overwrite
```

## Usage Examples

### Building an Index

```bash
# Basic usage
python3 scripts/build_rag_index.py

# Custom source and index name
python3 scripts/build_rag_index.py \
  --source ../docs/content/operate \
  --index-name redis_operate_docs \
  --redis-url redis://localhost:6379

# Limit documents for testing
python3 scripts/build_rag_index.py --limit 100 --overwrite
```

### Searching the Index

```python
from redis_agent_control_plane.rag.retriever import RedisRetriever

# Create retriever
retriever = RedisRetriever(
    redis_url="redis://localhost:6379",
    index_name="redis_docs"
)

# Basic search
results = retriever.search(
    query="How do I configure Active-Active replication?",
    top_k=5,
    distance_threshold=0.30
)

# Search with filters
results = retriever.search(
    query="database configuration",
    top_k=5,
    product_area="redis_software",  # Filter by product
    category="operate"               # Filter by category
)

# Display results
for i, result in enumerate(results, 1):
    print(f"\n{i}. {result['title']} - {result['section_heading']}")
    print(f"   Distance: {result['vector_distance']:.3f}")
    print(f"   URL: {result['doc_url']}")
    print(f"   Content: {result['content'][:200]}...")
```

### Hybrid Search (Vector + Text)

**New in Phase 3:** Combine vector similarity with BM25 text search using RRF.

```python
# Hybrid search (best for diverse query types)
results = retriever.hybrid_search(
    query="CONFIG SET maxmemory",
    top_k=5,
    vector_weight=0.7,  # 70% vector similarity
    text_weight=0.3,    # 30% text matching
    rrf_k=60            # RRF constant
)

# Results include hybrid scores
for result in results:
    print(f"Hybrid: {result['hybrid_score']:.4f}")
    print(f"  Vector: {result['vector_score']:.4f} (rank {result['vector_rank']})")
    print(f"  Text: {result['text_score']:.4f} (rank {result['text_rank']})")
```

**When to use hybrid search:**
- ✅ Exact command lookups: "CONFIG SET maxmemory"
- ✅ Config parameter searches: "maxmemory-policy allkeys-lru"
- ✅ API method searches: "HSET key field value"
- ✅ Mixed queries: "eviction policy configuration"

**When to use vector-only search:**
- ✅ Semantic queries: "How do I configure memory limits?"
- ✅ Conceptual questions: "What are the best practices?"

### Deduplicating Results

```python
# Get results
results = retriever.search("database setup", top_k=10)

# Keep only top chunk per document
deduplicated = retriever.deduplicate_results(results, max_per_doc=1)

# Keep top 2 chunks per document
deduplicated = retriever.deduplicate_results(results, max_per_doc=2)
```

## Chunking Strategy

The chunker uses an **adaptive H2/H3 strategy**:

- If H2 section has H3 subsections → split by H3
- If H2 section has no H3 → keep entire H2 as one chunk
- Preserves code blocks, tables, and procedural lists intact
- Subchunks long sections (>2000 chars) at paragraph boundaries
- Extracts YAML frontmatter metadata

## Metadata Fields

Each chunk has 13 metadata fields:

| Field | Type | Description |
|-------|------|-------------|
| `source` | TAG | Source repository (e.g., "redis/docs") |
| `doc_path` | TEXT | Relative file path |
| `doc_url` | TEXT | Public URL |
| `title` | TEXT | Document title |
| `category` | TAG | operate, integrate, develop |
| `product_area` | TAG | redis_software, redis_cloud, redis_stack, redis_oss |
| `section_heading` | TEXT | H2/H3 heading |
| `toc_path` | TEXT | Breadcrumb navigation |
| `chunk_id` | TAG | Unique chunk identifier |
| `chunk_index` | NUMERIC | Chunk order in document |
| `subchunk_index` | NUMERIC | Subchunk order (0 if not split) |
| `content` | TEXT | Chunk text content |
| `embedding` | VECTOR | 384-dim vector (cosine distance) |

## Search Index (Phase 3)

The pipeline uses **FT.CREATE** to create an optimized Redis search index:

### Index Schema

- **4 TAG fields**: `source`, `category`, `product_area`, `chunk_id` (exact filtering)
- **6 TEXT fields**: `doc_path`, `doc_url`, `title` (weight 2.0), `section_heading` (weight 1.5), `toc_path`, `content` (BM25 search)
- **2 NUMERIC fields**: `chunk_index`, `subchunk_index` (range queries, sorting)
- **1 VECTOR field**: `embedding` (HNSW algorithm, FLOAT32, 384 dims, COSINE distance)

### Index Management

```python
from redis_agent_control_plane.rag.indexer import RedisIndexer

indexer = RedisIndexer(redis_url="redis://localhost:6379", index_name="redis_docs")

# Create index (idempotent)
indexer.create_index(overwrite=False)

# Get index info
info = indexer.get_index_info()
print(f"Documents: {info['num_docs']}")
print(f"Records: {info['num_records']}")

# Drop index (keep data)
indexer.drop_index(delete_docs=False)

# Drop index and data
indexer.drop_index(delete_docs=True)
```

### Search Performance

**Phase 2.5 (Brute-force):**
- Algorithm: SCAN all keys + compute cosine similarity
- Complexity: O(n) - scans all 20,249 chunks
- Latency: ~500-1000ms per query

**Phase 3 (FT.CREATE + HNSW):**
- Algorithm: HNSW vector index + BM25 text index
- Complexity: O(log n) - logarithmic search
- Latency: ~50-100ms per query (10-20x faster)
- Speedup: **10-100x** on large corpus

## Performance

- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (384 dims)
- **Corpus Size**: 4,207 docs → 20,249 chunks
- **Index Size**: ~100 MB (vectors + metadata)
- **First Run**: Downloads model (~90MB)
- **Processing Time**: ~4 minutes for full corpus (with cache)
- **Query Latency**: <100ms (P95) with FT.SEARCH

## Testing

```bash
# Run all tests
make test

# Run specific test suite
PYTHONPATH=src venv/bin/pytest tests/test_rag_chunker.py -v
PYTHONPATH=src venv/bin/pytest tests/test_rag_embedder.py -v

# Run integration test (requires Redis)
PYTHONPATH=src venv/bin/pytest tests/test_rag_pipeline.py -v
```

## Troubleshooting

### Redis Connection Error
```
Error: Connection refused
```
**Solution**: Start Redis with `docker run -d -p 6379:6379 redis/redis-stack-server:latest`

### Model Download Fails
```
Error downloading model
```
**Solution**: Check internet connection. Model is downloaded on first run (~90MB).

### Out of Memory
```
Error: Cannot allocate memory
```
**Solution**: Use `--limit` to process fewer documents, or increase available memory.

## Next Steps

- **Phase 3**: Hybrid search (vector + BM25), reranking, query rewriting
- **API Integration**: Add FastAPI endpoints for search
- **UI**: Build search interface

