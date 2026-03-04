# Phase 3: Optimization Plan - Specialized Chunking + Hybrid Search

**Date:** 2026-03-04  
**Task:** [RAG-005] Phase 3: Specialize Chunking/Filters + Hybrid Search  
**Status:** IN PROGRESS

---

## Phase 2.5 Findings Summary

### ✅ What's Working Well
1. **Scale**: Successfully processed 4,207 docs → 20,249 chunks in 4 minutes
2. **Quality**: All test queries returned relevant results (distance scores 0.15-0.35)
3. **Stability**: No errors or memory issues with Redis Cloud (1GB instance)
4. **Cache Efficiency**: 63.8% embedding cache hit rate saved ~8 minutes
5. **Chunking**: Average 4.8 chunks per doc is reasonable

### ⚠️ Identified Optimization Opportunities

1. **Retrieval Performance**: Currently using brute-force similarity search
   - Scans all 20,249 chunks for every query
   - Works but not optimized for production scale
   - **Solution**: Implement FT.CREATE index with HNSW vector search

2. **Search Capabilities**: Only vector search, no keyword/exact match
   - Cannot handle exact command lookups (e.g., "CONFIG SET maxmemory")
   - Cannot handle exact config parameter searches
   - **Solution**: Implement hybrid search (vector + BM25 text search)

3. **Metadata Filtering**: Basic filter-first pattern implemented
   - Only supports product_area and category filters
   - Could be enhanced with more granular filtering
   - **Solution**: Add more metadata fields and filter combinations

4. **Chunking Strategy**: Generic H2/H3 chunking
   - Works well (avg 4.8 chunks/doc)
   - Could be specialized for Redis docs structure
   - **Solution**: Analyze corpus patterns and optimize chunking rules

---

## Phase 3 Objectives

### 1. Implement FT.CREATE Index for Optimized Vector Search
**Goal**: Replace brute-force search with Redis native vector index

**Current State**:
- Retriever scans all keys with `SCAN` command
- Computes cosine similarity for every chunk
- O(n) complexity for every query

**Target State**:
- Use `FT.CREATE` to create HNSW vector index
- Use `FT.SEARCH` for optimized vector queries
- O(log n) complexity with HNSW algorithm

**Implementation**:
- Update `indexer.py` to create FT.CREATE index on startup
- Update `retriever.py` to use FT.SEARCH instead of SCAN
- Support both vector-only and filtered vector search
- Maintain backward compatibility with existing data

**Expected Impact**:
- 10-100x faster retrieval on large corpus
- Lower latency for production queries
- Better scalability for future growth

---

### 2. Implement Hybrid Search (Vector + BM25)
**Goal**: Add keyword/exact match capabilities for command/config lookups

**Use Cases**:
- Exact command searches: "CONFIG SET maxmemory"
- Config parameter lookups: "maxmemory-policy allkeys-lru"
- API method searches: "HSET key field value"
- Error message searches: "OOM command not allowed"

**Implementation**:
- Add BM25 text index to `content` field in FT.CREATE
- Implement RRF (Reciprocal Rank Fusion) for combining scores
- Add `hybrid_search()` method to retriever
- Support configurable weights for vector vs text scores

**Reference**: See `notes/rag_reference_findings.md` Section A.2 for HybridQuery pattern

**Expected Impact**:
- Better precision for exact matches
- Improved recall for technical queries
- More robust search across different query types

---

### 3. Enhance Metadata Filtering
**Goal**: Improve filter-first retrieval with more granular metadata

**Current Filters**:
- `product_area`: redis_software, redis_cloud, redis_stack, redis_oss
- `category`: operate, integrate, develop

**Proposed Enhancements**:
- Add `doc_type` filter: guide, reference, tutorial, api, troubleshooting
- Add `version` filter: extracted from frontmatter
- Add `tags` filter: extracted from frontmatter (multi-value)
- Support filter combinations (AND/OR logic)

**Implementation**:
- Update chunker to extract additional metadata from frontmatter
- Update indexer schema to include new TAG fields
- Update retriever to support complex filter queries
- Add filter validation and error handling

---

### 4. Specialize Chunking Strategy
**Goal**: Optimize chunking for Redis documentation structure

**Current Strategy**:
- Adaptive H2/H3 chunking
- Preserve code blocks, tables, lists
- Subchunk sections >2000 chars
- Average: 4.8 chunks/doc

**Proposed Optimizations**:
1. **Command Reference Chunking**: Keep command syntax + description together
2. **Code Example Preservation**: Never split code blocks across chunks
3. **Table Handling**: Keep tables with their context (before/after text)
4. **Procedural List Chunking**: Keep numbered steps together
5. **Hugo Shortcode Handling**: Parse and preserve shortcode content

**Analysis Needed**:
- Sample 50 random docs from corpus
- Identify common patterns and edge cases
- Measure chunk quality metrics (coherence, completeness)
- Validate against test queries

---

## Implementation Plan

### Phase 3.1: FT.CREATE Index (Priority: HIGH)
- [ ] Update `indexer.py` to create FT.CREATE index
- [ ] Update `retriever.py` to use FT.SEARCH
- [ ] Add index management utilities (create, drop, info)
- [ ] Test with full corpus (20,249 chunks)
- [ ] Benchmark performance improvement

### Phase 3.2: Hybrid Search (Priority: HIGH)
- [ ] Add BM25 text index to schema
- [ ] Implement RRF score combination
- [ ] Add `hybrid_search()` method to retriever
- [ ] Test with command/config queries
- [ ] Compare results with vector-only search

### Phase 3.3: Enhanced Metadata (Priority: MEDIUM)
- [ ] Analyze frontmatter fields across corpus
- [ ] Update chunker to extract new metadata
- [ ] Update indexer schema with new fields
- [ ] Update retriever to support new filters
- [ ] Test filter combinations

### Phase 3.4: Specialized Chunking (Priority: MEDIUM)
- [ ] Sample and analyze 50 docs from corpus
- [ ] Identify chunking optimization opportunities
- [ ] Implement specialized chunking rules
- [ ] Test chunk quality with sample queries
- [ ] Measure impact on retrieval quality

---

## Success Metrics

1. **Performance**: Retrieval latency < 100ms for 95th percentile
2. **Quality**: Hybrid search improves precision for exact matches by >20%
3. **Coverage**: Enhanced filters support >90% of user filter needs
4. **Chunking**: Specialized chunking maintains or improves avg distance scores

---

## Next Steps

1. Start with Phase 3.1 (FT.CREATE index) - highest impact
2. Implement Phase 3.2 (hybrid search) - critical for production
3. Enhance metadata (Phase 3.3) based on user feedback
4. Optimize chunking (Phase 3.4) based on quality analysis

