# RAG Reference Findings - Phase 1 Analysis

**Date:** 2026-03-04  
**Purpose:** Analysis and design for Redis Docs RAG Pipeline (Phase 1)  
**Status:** Complete

---

## Executive Summary

This document presents findings from analyzing reference repositories and the Redis docs corpus structure to design a robust RAG pipeline for Redis documentation. The pipeline will support an engineering deployment agent with precision-first retrieval, structure-aware chunking, and comprehensive metadata tracking.

**Key Recommendations:**
1. Use RedisVL for vector indexing and retrieval (proven in all reference repos)
2. Implement filter-first retrieval with metadata tags (product_area, category, doc_type)
3. Chunk by H2/H3 boundaries while preserving code blocks and procedural lists
4. Support hybrid search (vector + BM25) for exact command/config lookups
5. Track provenance metadata on every chunk (doc_path, title, section_heading, breadcrumb, chunk_index)

---

## A) Per-Repository Analysis

### 1. redis-ai-resources/python-recipes/RAG/04_advanced_redisvl.ipynb

**Location:** `../redis-ai-resources/python-recipes/RAG/04_advanced_redisvl.ipynb`

**What to Reuse:**
- **Dense content representation pattern**: Use LLM to decompose raw text into propositional phrases before embedding
  - System prompt pattern for extracting propositions from raw content
  - JSON response format for structured extraction
  - Improves semantic retrieval accuracy by creating clearer, more discrete chunks
- **RedisVL AsyncSearchIndex**: Async interface for vector search operations
- **Embedding cache pattern**: `EmbeddingsCache` to avoid re-embedding identical text
  - TTL-based cache (600s default)
  - Significant cost/latency savings for repeated queries
- **Query rewriting**: Use LLM to expand/improve user queries before retrieval
  - Example: "How big is the company?" → "What is the company's revenue, market capitalization, and employee count?"
- **Schema definition pattern**: Clear separation of text fields, tag fields, and vector fields
  ```python
  {
    "chunk_id": "tag",
    "proposition": "text",
    "text_embedding": "vector"
  }
  ```

**What to Ignore:**
- PDF-specific ingestion (we already have markdown ingestion)
- OpenAI-specific LLM calls (we may use different providers)
- Financial document-specific prompts

**Key Takeaways:**
- **Precision improvement**: Dense content representation (propositions) significantly improves retrieval quality
- **Caching is critical**: Embedding cache reduces costs and latency for repeated queries
- **Query enhancement**: LLM-based query rewriting can improve search quality
- **Async operations**: Use async Redis operations for better performance

---

### 2. redis-ai-resources/python-recipes/vector-search/02_hybrid_search.ipynb

**Location:** `../redis-ai-resources/python-recipes/vector-search/02_hybrid_search.ipynb`

**What to Reuse:**
- **HybridQuery class** (RedisVL 0.13.0+): Unified interface for hybrid search
  - Combines text similarity (BM25) and vector similarity (cosine)
  - Supports RRF (Reciprocal Rank Fusion) and linear combination methods
  - Example:
    ```python
    HybridQuery(
        text="user query",
        text_field_name="description",
        vector=query_vector,
        vector_field_name="description_vector",
        combination_method="RRF",  # or "LINEAR"
        rrf_window=20,
        yield_text_score_as="text_score",
        yield_vsim_score_as="vector_similarity",
        yield_combined_score_as="hybrid_score",
        return_fields=["title", "content"]
    )
    ```
- **Stopwords handling**: NLTK-based stopword removal for text queries
  - Configurable by language or custom list
  - Critical for avoiding irrelevant matches on common words
- **Text scoring functions**: BM25STD (default), TFIDF, TFIDF.DOCNORM, etc.
  - BM25STD recommended for most use cases
- **RRF formula**: `score = weight * (1 / (rank + k))` where k=60 (default)
  - Handles ranked lists of different lengths and score scales
  - More robust than linear combination for diverse result sets

**What to Ignore:**
- Movie dataset specifics
- Colab-specific setup code

**Key Takeaways:**
- **Hybrid search is essential**: For exact command/config lookups (e.g., "redis-cli CONFIG SET")
- **RRF > Linear combination**: More robust for combining text and vector scores
- **Stopwords matter**: Remove common words to avoid irrelevant matches
- **Redis 8.4.0+ required**: For FT.HYBRID command (or use aggregations API for older versions)

---

### 3. redis-rag-workbench

**Location:** `../redis-rag-workbench/`

**What to Reuse:**
- **Chunking configuration pattern**: Configurable chunk_size and chunking_technique
  - Default: chunk_size=500, chunking_technique="Recursive Character"
  - RecursiveCharacterTextSplitter from LangChain with chunk_overlap
- **RedisVectorStore integration**: LangChain's RedisVectorStore for vector storage
  - Seamless integration with LangChain retrieval chains
- **Reranking pattern**: HFCrossEncoderReranker and CohereReranker
  - Post-retrieval reranking to improve result quality
  - Example: `HFCrossEncoderReranker("BAAI/bge-reranker-base")`
- **Semantic caching**: SemanticCache for LLM response caching
  - Reduces costs and latency for similar queries
- **Semantic router**: Route queries to different handlers based on semantic similarity
  - YAML-based configuration for routes
- **Distance threshold filtering**: Filter results by vector similarity threshold
  - Default: 0.30 (configurable)
- **Top-k retrieval**: Configurable number of results to retrieve
  - Default: 3 (configurable)

**What to Ignore:**
- Gradio UI components
- PDF upload/management UI
- RAGAS evaluation (useful for later phases, but not core pipeline)

**Key Takeaways:**
- **Reranking improves precision**: Post-retrieval reranking with cross-encoder models
- **Configurable chunking**: Allow tuning chunk_size and overlap for different content types
- **Semantic caching**: Cache LLM responses for similar queries to reduce costs
- **Distance threshold**: Filter out low-quality results below similarity threshold

---

### 4. redis-slack-worker-agent

**Location:** `../redis-slack-worker-agent/`

**What to Reuse:**
- **Chunking pattern** (`app/etl/tasks/vectorization.py`):
  - RecursiveCharacterTextSplitter with CHUNK_SIZE=1000, CHUNK_OVERLAP=200
  - Larger chunks than redis-rag-workbench (1000 vs 500)
  - Higher overlap (200 vs default)
- **Ingestion pipeline** (`app/etl/tasks/ingestion.py`):
  - Structured ETL with separate ingestion and vectorization tasks
  - S3-based storage for processed content
  - Date-based folder organization (YYYY-MM-DD)
  - Content type categorization (repo, blog, notebook)
- **Embedding cache approach**: Note for later phases (not implemented in current codebase)
- **Vector search pattern** (`app/agent/tools/search_knowledge_base.py`):
  - AsyncSearchIndex for async operations
  - VectorQuery with configurable num_results
  - Return fields: ["name", "description"]
  - Formatted results with query context
- **Metadata tracking**: Track content type, date_folder, filename, s3_key

**What to Ignore:**
- Slack-specific wrappers and UI
- AWS S3-specific storage (we use local filesystem)
- Docket worker queue system (we may use different task queue)
- Blog/notebook-specific processing

**Key Takeaways:**
- **Larger chunks for technical content**: 1000 chars with 200 overlap works well for technical docs
- **Structured ETL pipeline**: Separate ingestion, processing, and vectorization stages
- **Async operations**: Use AsyncSearchIndex for better performance
- **Metadata is critical**: Track content type, source, and provenance for filtering

---

### 5. Redis Docs Corpus Structure

**Location:** `../docs/`

**Critical Files Analyzed:**
- `for-ais-only/REPOSITORY_MAP_FOR_AI_AGENTS.md`
- `for-ais-only/metadata_docs/PAGE_METADATA_FORMAT.md`
- `for-ais-only/render_hook_docs/README.md`

**Corpus Structure:**
```
docs/
├── content/
│   ├── operate/          # Operations guides (PRIMARY FOCUS)
│   │   ├── rs/           # Redis Software (Enterprise)
│   │   ├── rc/           # Redis Cloud
│   │   ├── redisinsight/ # RedisInsight
│   ├── integrate/        # Integration guides
│   └── develop/          # Development guides
├── for-ais-only/         # AI-FRIENDLY METADATA (CRITICAL)
│   ├── REPOSITORY_MAP_FOR_AI_AGENTS.md
│   ├── metadata_docs/
│   │   └── PAGE_METADATA_FORMAT.md
│   └── render_hook_docs/
│       └── README.md
```

**Page Metadata Structure** (from PAGE_METADATA_FORMAT.md):
- **Core fields**: title, description
- **Navigation**: tableOfContents (hierarchical sections with id, title, children)
- **Categorization**: categories[], scope, topics[], relatedPages[]
- **Command reference**: arguments[], syntax_fmt, complexity, group, command_flags[], acl_categories[], since, arity, key_specs[]
- **Code examples**: codeExamples[] with id, description, difficulty, buildsUpon[], languages[]

**Render Hooks** (interactive components):
- **Checklist**: Interactive checklists with state persistence
- **Hierarchy**: Visual SVG diagrams for class inheritance, filesystem trees
- **Decision tree**: Interactive decision trees for guiding users

**Key Takeaways:**
- **Rich metadata available**: Page metadata includes TOC, categories, code examples, command specs
- **Structure-aware content**: H2/H3 headings define section boundaries
- **Code blocks are sacred**: Preserve code blocks intact (do NOT split)
- **Procedural lists**: Checklists and step-by-step guides must stay together
- **Product area categorization**: operate/rs/ = Redis Software, operate/rc/ = Redis Cloud
- **Breadcrumb tracking**: Use path structure to derive breadcrumbs (e.g., operate > rs > databases > active-active > planning)

---

## B) Recommended Pipeline Architecture

### Pipeline Stages

```
1. INGEST
   ↓
2. NORMALIZE (extract metadata, parse frontmatter)
   ↓
3. CHUNK (structure-aware: H2/H3 boundaries, preserve code blocks)
   ↓
4. EMBED (generate vector embeddings with caching)
   ↓
5. INDEX (store in Redis with metadata)
   ↓
6. RETRIEVE (filter-first, then vector/hybrid search)
```

### Stage Details

**1. INGEST**
- Input: Markdown files from `../docs/content/operate/**`
- Output: Document objects with file_path, title, content, source_repo
- Reuse: Existing `src/redis_agent_control_plane/rag/ingest.py`

**2. NORMALIZE**
- Parse YAML frontmatter (title, description, categories, etc.)
- Extract H2/H3 section headings and TOC structure
- Identify code blocks, checklists, decision trees
- Compute breadcrumb from file path
- Assign product_area tag based on path (rs/ → redis_software, rc/ → redis_cloud)
- Assign category tag (operate, integrate, develop)

**3. CHUNK**
- Split by H2/H3 boundaries (primary chunking strategy)
- Preserve code blocks intact (do NOT split across chunks)
- Preserve procedural lists/checklists intact
- For very long sections (>2000 chars), split into subchunks with ordering
- Assign chunk_id, chunk_index, subchunk_index
- Attach metadata to each chunk:
  - source, doc_path, doc_url, title, category, product_area
  - section_heading, toc_path (breadcrumb), chunk_id, chunk_index, subchunk_index
  - content (text), embedding (vector)

**4. EMBED**
- Use sentence-transformers (e.g., all-MiniLM-L6-v2) or OpenAI embeddings
- Implement EmbeddingsCache (TTL=600s) to avoid re-embedding
- Generate embeddings for chunk content
- Store as float32 vectors

**5. INDEX**
- Use RedisVL SearchIndex
- Store chunks in Redis with metadata fields
- Create vector index with HNSW algorithm

**6. RETRIEVE**
- **Filter-first**: Apply metadata filters (product_area, category) before vector search
- **Vector search**: Semantic similarity search on embeddings
- **Hybrid search**: Combine vector + BM25 for exact command/config lookups
- **Reranking** (optional): Post-retrieval reranking with cross-encoder
- **Deduplication**: Remove duplicate chunks from same document
- **Top-k**: Return top 3-5 results (configurable)

---

## C) Proposed Redis Index Schema

### Index Configuration

```python
{
  "index": {
    "name": "redis_docs_rag",
    "prefix": "doc:chunk:",
    "storage": "hash"
  },
  "fields": [
    # Metadata fields (for filtering)
    {
      "name": "source",
      "type": "tag",
      "attrs": {"sortable": False}
    },
    {
      "name": "doc_path",
      "type": "text",
      "attrs": {"sortable": False}
    },
    {
      "name": "doc_url",
      "type": "text",
      "attrs": {"sortable": False}
    },
    {
      "name": "title",
      "type": "text",
      "attrs": {"sortable": False}
    },
    {
      "name": "category",
      "type": "tag",
      "attrs": {"sortable": False}
      # Values: operate, integrate, develop
    },
    {
      "name": "product_area",
      "type": "tag",
      "attrs": {"sortable": False}
      # Values: redis_software, redis_cloud, redis_stack, redis_oss
    },
    {
      "name": "section_heading",
      "type": "text",
      "attrs": {"sortable": False}
    },
    {
      "name": "toc_path",
      "type": "text",
      "attrs": {"sortable": False}
      # Breadcrumb: "operate > rs > databases > active-active > planning"
    },
    {
      "name": "chunk_id",
      "type": "tag",
      "attrs": {"sortable": True}
    },
    {
      "name": "chunk_index",
      "type": "numeric",
      "attrs": {"sortable": True}
    },
    {
      "name": "subchunk_index",
      "type": "numeric",
      "attrs": {"sortable": True}
    },

    # Content fields
    {
      "name": "content",
      "type": "text",
      "attrs": {"sortable": False}
    },

    # Vector field
    {
      "name": "embedding",
      "type": "vector",
      "attrs": {
        "dims": 384,  # for all-MiniLM-L6-v2
        "distance_metric": "cosine",
        "algorithm": "hnsw",
        "datatype": "float32"
      }
    }
  ]
}
```

### Metadata Field Descriptions

| Field | Type | Purpose | Example Values |
|-------|------|---------|----------------|
| `source` | TAG | Source repository | `redis_docs` |
| `doc_path` | TEXT | Relative file path | `content/operate/rs/databases/active-active/planning.md` |
| `doc_url` | TEXT | Public URL | `https://redis.io/docs/latest/operate/rs/databases/active-active/planning/` |
| `title` | TEXT | Page title | `Considerations for planning Active-Active databases` |
| `category` | TAG | Top-level category | `operate`, `integrate`, `develop` |
| `product_area` | TAG | Product area | `redis_software`, `redis_cloud`, `redis_stack`, `redis_oss` |
| `section_heading` | TEXT | H2/H3 heading | `Participating clusters`, `Memory limits` |
| `toc_path` | TEXT | Breadcrumb | `operate > rs > databases > active-active > planning` |
| `chunk_id` | TAG | Unique chunk ID | `operate_rs_aa_planning_001` |
| `chunk_index` | NUMERIC | Chunk order in doc | `0`, `1`, `2` |
| `subchunk_index` | NUMERIC | Subchunk order | `0`, `1`, `2` (0 if not split) |
| `content` | TEXT | Chunk text content | Full text of chunk |
| `embedding` | VECTOR | Vector embedding | 384-dim float32 vector |

---

## D) Redis Docs Chunking Strategy

### Chunking Rules

**1. Primary Chunking: H2/H3 Boundaries**
- Split document by H2 (`##`) and H3 (`###`) headings
- Each chunk = one H2 or H3 section
- Include heading text in chunk content
- Preserve hierarchy: H3 chunks reference parent H2

**2. Preserve Code Blocks**
- **NEVER** split code blocks across chunks
- If code block is within a section, keep it with that section
- If code block is very large (>1500 chars), keep it as a single chunk

**3. Preserve Procedural Lists**
- Keep numbered lists and checklists intact
- Do NOT split step-by-step instructions across chunks
- If list is very long (>2000 chars), keep it as a single chunk

**4. Subchunking for Long Sections**
- If section > 2000 chars (after preserving code blocks and lists):
  - Split into subchunks at paragraph boundaries
  - Assign subchunk_index (0, 1, 2, ...)
  - Include section_heading in all subchunks
  - Maintain ordering with chunk_index and subchunk_index

**5. Metadata Assignment**
- **category**: Extract from path (operate/, integrate/, develop/)
- **product_area**: Extract from path:
  - `operate/rs/` → `redis_software`
  - `operate/rc/` → `redis_cloud`
  - `operate/stack/` → `redis_stack`
  - Default → `redis_oss`
- **toc_path**: Derive from file path and section headings
  - Example: `operate > rs > databases > active-active > planning > Participating clusters`
- **doc_url**: Construct from doc_path
  - `content/operate/rs/databases/active-active/planning.md` → `https://redis.io/docs/latest/operate/rs/databases/active-active/planning/`

### Chunking Algorithm Pseudocode

```python
def chunk_document(doc):
    chunks = []
    sections = extract_h2_h3_sections(doc.content)

    for section_index, section in enumerate(sections):
        # Check for code blocks and lists
        has_code_block = contains_code_block(section.content)
        has_procedural_list = contains_procedural_list(section.content)

        # Preserve code blocks and lists intact
        if has_code_block or has_procedural_list:
            chunk = create_chunk(
                doc=doc,
                section=section,
                chunk_index=section_index,
                subchunk_index=0
            )
            chunks.append(chunk)

        # Split long sections into subchunks
        elif len(section.content) > 2000:
            subchunks = split_at_paragraph_boundaries(section.content, max_size=1500)
            for subchunk_index, subchunk_content in enumerate(subchunks):
                chunk = create_chunk(
                    doc=doc,
                    section=section,
                    chunk_index=section_index,
                    subchunk_index=subchunk_index,
                    content=subchunk_content
                )
                chunks.append(chunk)

        # Normal section (< 2000 chars)
        else:
            chunk = create_chunk(
                doc=doc,
                section=section,
                chunk_index=section_index,
                subchunk_index=0
            )
            chunks.append(chunk)

    return chunks
```

---

## E) Retrieval Strategy

### Filter-First Retrieval Pattern

**Goal:** Narrow search space with metadata filters BEFORE vector ranking

**Steps:**
1. **Parse user query** to extract filters:
   - Product area: "Redis Cloud" → filter `product_area=redis_cloud`
   - Category: "deployment" → filter `category=operate`
   - Command: "CONFIG SET" → use hybrid search (vector + BM25)

2. **Apply metadata filters**:
   ```python
   from redisvl.query import FilterExpression

   filter_expr = FilterExpression(
       Tag("product_area") == "redis_software"
   ) & FilterExpression(
       Tag("category") == "operate"
   )
   ```

3. **Execute search**:
   - **Vector search** (default): For conceptual queries
   - **Hybrid search** (RRF): For exact command/config lookups

4. **Post-processing**:
   - Deduplicate chunks from same document
   - Rerank with cross-encoder (optional)
   - Return top-k results (default: 3-5)

### When to Use Vector vs Hybrid Search

| Query Type | Search Method | Example |
|------------|---------------|---------|
| Conceptual | Vector search | "How do I set up Active-Active replication?" |
| Exact command | Hybrid search (RRF) | "redis-cli CONFIG SET maxmemory" |
| Configuration | Hybrid search (RRF) | "maxmemory-policy allkeys-lru" |
| Troubleshooting | Vector search | "Why is my cluster running out of memory?" |
| Best practices | Vector search | "What are the best practices for Redis Enterprise clustering?" |

### Recommended Default Parameters

- **top_k**: 5 (return top 5 results)
- **distance_threshold**: 0.30 (filter out results with cosine distance > 0.30)
- **rrf_window**: 20 (for hybrid search)
- **rrf_constant**: 60 (for hybrid search)
- **rerank**: Optional (use HFCrossEncoderReranker for precision-critical queries)

### Deduplication Strategy

**Problem:** Multiple chunks from same document may be retrieved

**Solution:**
1. Group results by `doc_path`
2. For each document, keep only the highest-scoring chunk
3. OR: Keep top 2 chunks per document if they are from different sections

### Reranking (Optional)

**When to use:**
- Precision-critical queries (e.g., deployment instructions)
- User explicitly requests "best" or "most relevant" results

**How:**
```python
from redisvl.utils.rerank import HFCrossEncoderReranker

reranker = HFCrossEncoderReranker("BAAI/bge-reranker-base")
reranked_results = reranker.rank(
    query=user_query,
    docs=[result["content"] for result in results]
)
```

---

## F) Risks, Pitfalls, and Quality Gates

### Risks and Pitfalls

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Splitting code blocks** | Broken code examples, unusable chunks | Detect code blocks (```) and preserve intact |
| **Losing hierarchy** | Chunks lack context (e.g., H3 without parent H2) | Include section_heading and toc_path in metadata |
| **Mixing Cloud and Enterprise** | Wrong guidance for user's deployment | Filter by product_area tag (redis_cloud vs redis_software) |
| **Overly generic chunks** | Low precision, irrelevant results | Ensure chunks have specific context (section_heading, toc_path) |
| **Weak filters** | Retrieve wrong product area or category | Validate filters before search, use strict TAG matching |
| **Embedding drift** | Inconsistent embeddings over time | Use EmbeddingsCache, version embedding model |
| **Large chunks** | Poor retrieval granularity | Subchunk long sections (>2000 chars) at paragraph boundaries |
| **Small chunks** | Lack of context | Minimum chunk size: 200 chars (or keep with parent section) |

### Quality Gates

**1. Chunking Quality**
- ✅ No code blocks split across chunks
- ✅ No procedural lists split across chunks
- ✅ All chunks have section_heading and toc_path
- ✅ Chunk size distribution: 80% between 200-2000 chars
- ✅ All chunks have valid product_area and category tags

**2. Metadata Quality**
- ✅ All chunks have doc_path, doc_url, title
- ✅ All chunks have chunk_id, chunk_index, subchunk_index
- ✅ toc_path matches file path structure
- ✅ product_area matches path (rs/ → redis_software, rc/ → redis_cloud)

**3. Retrieval Quality**
- ✅ Filter-first retrieval returns only relevant product_area
- ✅ Hybrid search returns exact command matches in top 3
- ✅ Vector search returns semantically relevant results
- ✅ No duplicate chunks from same document in top 5
- ✅ Distance threshold filters out low-quality results (>0.30)

**4. Index Quality**
- ✅ All chunks indexed successfully (no errors)
- ✅ Vector field has correct dimensions (384 for all-MiniLM-L6-v2)
- ✅ TAG fields are indexed for filtering
- ✅ TEXT fields are indexed for hybrid search

### Testing Strategy

**Unit Tests:**
- Test chunking algorithm with sample documents
- Test metadata extraction from frontmatter
- Test product_area and category assignment from path
- Test code block detection and preservation
- Test procedural list detection and preservation

**Integration Tests:**
- Test end-to-end pipeline (ingest → chunk → embed → index)
- Test filter-first retrieval with product_area and category filters
- Test hybrid search with exact command queries
- Test deduplication logic
- Test reranking (optional)

**Quality Checks:**
- Manual review of 20 random chunks for quality
- Verify no code blocks split across chunks
- Verify all chunks have required metadata fields
- Verify retrieval returns relevant results for sample queries

---

## G) Implementation Roadmap (Phase 2 and Beyond)

### Phase 2: Implement Baseline Pipeline

**Goals:**
- Implement chunking algorithm (H2/H3 boundaries, preserve code blocks)
- Implement metadata extraction (frontmatter, path-based tags)
- Implement embedding generation with caching
- Implement Redis indexing with RedisVL
- Implement filter-first retrieval (vector search only)

**Deliverables:**
- `src/redis_agent_control_plane/rag/chunker.py`
- `src/redis_agent_control_plane/rag/embedder.py`
- `src/redis_agent_control_plane/rag/indexer.py`
- `src/redis_agent_control_plane/rag/retriever.py`
- Unit tests for each module
- Integration test for end-to-end pipeline
- Smoke-check command to verify pipeline works

### Phase 3: Specialize Chunking/Filters + Hybrid Search

**Goals:**
- Refine chunking for Redis docs (handle render hooks, decision trees)
- Add hybrid search (vector + BM25) for exact command lookups
- Add reranking (optional)
- Add deduplication logic
- Tune distance threshold and top-k parameters

**Deliverables:**
- Enhanced chunking algorithm for render hooks
- Hybrid search implementation (HybridQuery)
- Reranking implementation (HFCrossEncoderReranker)
- Deduplication logic
- Performance benchmarks and quality metrics

---

## H) References

### Reference Repositories
1. `../redis-ai-resources/python-recipes/RAG/04_advanced_redisvl.ipynb`
2. `../redis-ai-resources/python-recipes/vector-search/02_hybrid_search.ipynb`
3. `../redis-rag-workbench/`
4. `../redis-slack-worker-agent/`

### Redis Docs Corpus
- `../docs/for-ais-only/REPOSITORY_MAP_FOR_AI_AGENTS.md`
- `../docs/for-ais-only/metadata_docs/PAGE_METADATA_FORMAT.md`
- `../docs/for-ais-only/render_hook_docs/README.md`
- `../docs/content/operate/**` (primary focus)

### Key Technologies
- **RedisVL**: Vector indexing and retrieval
- **LangChain**: Text splitting, document loaders
- **sentence-transformers**: Embedding models (all-MiniLM-L6-v2)
- **Redis Stack**: Vector search with HNSW algorithm

---

## I) Appendix: Sample Chunk

### Example Chunk from `operate/rs/databases/active-active/planning.md`

```json
{
  "source": "redis_docs",
  "doc_path": "content/operate/rs/databases/active-active/planning.md",
  "doc_url": "https://redis.io/docs/latest/operate/rs/databases/active-active/planning/",
  "title": "Considerations for planning Active-Active databases",
  "category": "operate",
  "product_area": "redis_software",
  "section_heading": "Participating clusters",
  "toc_path": "operate > rs > databases > active-active > planning > Participating clusters",
  "chunk_id": "operate_rs_aa_planning_001",
  "chunk_index": 0,
  "subchunk_index": 0,
  "content": "## Participating clusters\n\nYou need at least two participating clusters for an Active-Active database. If your database requires more than ten participating clusters, contact Redis support. You can add or remove participating clusters after database creation.\n\n{{<note>}}\nIf an Active-Active database runs on flash memory, you cannot add participating clusters that run on RAM only.\n{{</note>}\n\nChanges made from the Cluster Manager UI to an Active-Active database configuration only apply to the cluster you are editing. For global configuration changes across all clusters, use the `crdb-cli` command-line utility.",
  "embedding": [0.023, -0.045, 0.012, ...]  // 384-dim vector
}
```

---

**End of Phase 1 Findings**

