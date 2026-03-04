# Testing the RAG Pipeline

This guide walks you through testing the RAG pipeline implementation.

## Prerequisites

- Python 3.10+
- Redis running on localhost:6379
- Virtual environment activated

## Step-by-Step Testing

### 1. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install all dependencies
make install
```

This installs:
- `redisvl` - Redis vector library
- `sentence-transformers` - Embedding generation
- `pyyaml` - YAML parsing
- All development dependencies

**Expected output:**
```
Installing dependencies...
Successfully installed redisvl-0.3.x sentence-transformers-2.x.x pyyaml-6.x
```

### 2. Verify Redis is Running

```bash
redis-cli ping
```

**Expected output:**
```
PONG
```

If Redis is not running:
```bash
# Option 1: Docker
docker run -d -p 6379:6379 redis/redis-stack-server:latest

# Option 2: Local Redis
redis-server
```

### 3. Run Quality Checks

```bash
# Run all checks: format, lint, type-check, test
make all
```

**Expected output:**
```
Formatting code with venv...
All done! ✨ 🍰 ✨

Running linter with venv...
All checks passed!

Running type checker with venv...
Success: no issues found in 8 source files

Running tests with venv...
====== 14 passed in X.XXs ======
All checks passed!
```

### 4. Run End-to-End Pipeline Test

```bash
python3 scripts/test_rag_pipeline.py
```

**Expected output:**
```
============================================================
RAG Pipeline End-to-End Test
============================================================

[1/6] Creating test documents...
  ✓ Created 2 test documents

[2/6] Chunking documents...
  ✓ Created 8 chunks
  ✓ Avg chunks per doc: 4.0

  Sample chunk metadata:
    - Title: Active-Active Databases
    - Category: operate
    - Product Area: redis_software
    - Section: Overview
    - Content length: 234 chars

[3/6] Generating embeddings...
  ✓ Using model: sentence-transformers/all-MiniLM-L6-v2
  ✓ Embedding dimensions: 384
  ✓ Generated 8 embeddings
  ✓ Cache size: 8

[4/6] Indexing chunks in Redis...
  ✓ Created index: test_rag_pipeline
  ✓ Indexed 8 chunks

[5/6] Testing retrieval...

  Query 1: 'How do I set up Active-Active replication?'
    ✓ Found 3 results
    ✓ Best match: Configuration
    ✓ Distance: 0.123

  Query 2: 'What are the eviction policies?'
    ✓ Found 3 results
    ✓ Best match: Eviction Policies
    ✓ Distance: 0.089

  Query 3: 'database configuration' (filtered)
    ✓ Found 5 results with filters

[6/6] Summary
  ✓ All pipeline stages completed successfully!
  ✓ Documents: 2
  ✓ Chunks: 8
  ✓ Embeddings: 8
  ✓ Retrieval: Working

============================================================
✅ RAG Pipeline Test PASSED
============================================================
```

**Note:** First run will download the embedding model (~90MB). This is normal and only happens once.

### 5. Test with Real Documentation (Optional)

```bash
# Test with 10 real documents from operate/
python3 scripts/build_rag_index.py --source ../docs/content/operate --limit 10 --overwrite
```

**Expected output:**
```
============================================================
RAG Pipeline: Build Index
============================================================

[1/4] Ingesting documents from ../docs/content/operate...
  ✓ Loaded 10 documents in 0.12s

[2/4] Chunking documents...
  ✓ Created 45 chunks in 0.03s
  ✓ Avg chunks per doc: 4.5

[3/4] Generating embeddings...
  ✓ Using model: sentence-transformers/all-MiniLM-L6-v2
  ✓ Embedding dimensions: 384
  ✓ Generated 45 embeddings in 2.34s
  ✓ Cache size: 45

[4/4] Indexing chunks in Redis (redis://localhost:6379)...
  ✓ Created index: redis_docs
  ✓ Indexed 45 chunks in 0.15s

============================================================
Pipeline Summary
============================================================
Documents processed: 10
Chunks created: 45
Embeddings generated: 45
Index name: redis_docs
Total time: 2.64s
============================================================
```

### 6. Test Retrieval Interactively

```python
# Start Python REPL
python3

# Run this code:
import sys
sys.path.insert(0, 'src')

from redis_agent_control_plane.rag.retriever import RedisRetriever

retriever = RedisRetriever(index_name="redis_docs")
results = retriever.search("How do I configure Active-Active replication?", top_k=3)

for i, result in enumerate(results, 1):
    print(f"\n{i}. {result.get('title')} - {result.get('section_heading')}")
    print(f"   Distance: {result.get('vector_distance', 0):.3f}")
    print(f"   Content: {result.get('content', '')[:150]}...")
```

## Troubleshooting

### Import Errors

**Problem:**
```
ModuleNotFoundError: No module named 'redisvl'
```

**Solution:**
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
make install
```

### Redis Connection Errors

**Problem:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solution:**
```bash
# Check if Redis is running
redis-cli ping

# If not, start Redis
docker run -d -p 6379:6379 redis/redis-stack-server:latest
```

### Model Download Issues

**Problem:**
```
Error downloading model from HuggingFace
```

**Solution:**
- Check internet connection
- Model downloads automatically on first run (~90MB)
- Wait for download to complete

## Success Criteria

✅ All tests pass (`make all`)  
✅ End-to-end test passes (`python3 scripts/test_rag_pipeline.py`)  
✅ Can build index with real docs  
✅ Can retrieve relevant results  

## Next Steps

Once all tests pass, you're ready to:

1. **Commit the changes** (see commit message below)
2. **Build the full index** with all 4,231 documents
3. **Integrate with the agent** for RAG-powered responses

## Suggested Commit Message

```
feat(rag): implement baseline RAG pipeline (Phase 2)

- Add chunker with adaptive H2/H3 strategy
- Add embedder with sentence-transformers and caching
- Add indexer with RedisVL and 13 metadata fields
- Add retriever with filter-first pattern
- Add end-to-end pipeline script
- Add unit tests and integration test
- Preserve code blocks, tables, lists, shortcodes
- Extract frontmatter metadata
- Assign product_area and category from path

Implements [RAG-004] Phase 2: Implement Baseline Pipeline

Files changed:
- src/redis_agent_control_plane/rag/chunker.py (new)
- src/redis_agent_control_plane/rag/embedder.py (new)
- src/redis_agent_control_plane/rag/indexer.py (new)
- src/redis_agent_control_plane/rag/retriever.py (new)
- scripts/build_rag_index.py (new)
- scripts/test_rag_pipeline.py (new)
- tests/test_rag_*.py (new, 5 files)
- requirements.txt (updated)
- docs/RAG_PIPELINE.md (new)
- TESTING.md (new)
```

