# Phase 2 Kickoff Guide

**Date:** 2026-03-04  
**Status:** Ready to start Phase 2 implementation

---

## ✅ Phase 1 Complete

**Deliverables:**
- ✅ `notes/rag_reference_findings.md` (723 lines) - Comprehensive analysis and design
- ✅ TASKS.md updated with RAG EPIC (3 phased tasks)
- ✅ CONTEXT.md updated with RAG scope/constraints
- ✅ AUGGIE.md updated with Phase 2 kickoff instructions

**Key Decisions Made:**
1. **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (384 dims, free, local)
2. **Chunking Strategy**: Adaptive H2/H3 chunking based on actual docs analysis
   - Analyzed 20 sample docs: avg H2 section = 1,067 chars (perfect for RAG)
   - Preserve code blocks, tables, procedural lists, Hugo shortcodes
   - Subchunk sections >2000 chars at paragraph boundaries
3. **Metadata Filters**: product_area (redis_software, redis_cloud, redis_stack, redis_oss), category (operate, integrate, develop)
4. **Corpus Scope**: All of `../docs/content/` (operate, integrate, develop) - ~4,231 files, ~29.7M chars

---

## 🚀 How to Start Phase 2

### Option 1: New Auggie Session (RECOMMENDED)

Start a fresh session and say:
```
Execute Phase 2 from TASKS.md: [RAG-004] Phase 2: Implement Baseline Pipeline
```

### Option 2: Continue Current Session

In the current session, say:
```
I'm ready to start Phase 2. Please implement [RAG-004] from TASKS.md.
```

---

## 📋 Phase 2 Overview

**Task:** [RAG-004] Phase 2: Implement Baseline Pipeline  
**Location:** TASKS.md lines 409-544  
**Status:** TODO → ACTIVE

**What will be implemented:**
1. **Chunker** (`src/redis_agent_control_plane/rag/chunker.py`)
   - Adaptive H2/H3 boundary chunking
   - Preserve code blocks, tables, lists, shortcodes
   - Frontmatter parsing and metadata extraction
   - Subchunking for long sections

2. **Embedder** (`src/redis_agent_control_plane/rag/embedder.py`)
   - sentence-transformers/all-MiniLM-L6-v2
   - EmbeddingsCache with TTL (600s)
   - Batch embedding support

3. **Indexer** (`src/redis_agent_control_plane/rag/indexer.py`)
   - RedisVL SearchIndex with 13 metadata fields
   - HNSW vector index (cosine distance)
   - TAG/TEXT/NUMERIC fields

4. **Retriever** (`src/redis_agent_control_plane/rag/retriever.py`)
   - Filter-first retrieval pattern
   - Vector search with distance threshold (0.30)
   - Top-k results (default: 5)

5. **Pipeline Script** (`scripts/build_rag_index.py`)
   - End-to-end: ingest → chunk → embed → index
   - Summary stats output

6. **Tests**
   - Unit tests for each module
   - Integration test for end-to-end pipeline

---

## 📊 Expected Outcomes

**Chunks Created:** ~15,000-20,000 (avg 1,500 chars per chunk)  
**Index Size:** ~50-100 MB (vectors + metadata)  
**Corpus:** ~4,231 markdown files from `../docs/content/`

**Quality Gates:**
- ✅ No code blocks split across chunks
- ✅ All chunks have required metadata (13 fields)
- ✅ product_area and category correctly assigned from path
- ✅ Retrieval returns relevant results with filter-first pattern

---

## 📚 Reference Documents

**Primary Reference:**
- `notes/rag_reference_findings.md` - Complete Phase 1 analysis (723 lines)
  - Section A: Per-repo analysis
  - Section B: Pipeline architecture
  - Section C: Redis index schema (13 fields)
  - Section D: Chunking strategy (8 rules)
  - Section E: Retrieval strategy
  - Section F: Risks and quality gates

**Task Definition:**
- `TASKS.md` → [RAG-004] (lines 409-544)

**Context:**
- `CONTEXT.md` → "RAG Pipeline Scope and Constraints" section

---

## 🎯 Success Criteria

Phase 2 is complete when:
- [ ] All 4 modules implemented (chunker, embedder, indexer, retriever)
- [ ] End-to-end pipeline script works
- [ ] Unit tests pass
- [ ] Integration test passes
- [ ] Smoke test shows: docs processed, chunks created, index size
- [ ] Sample retrieval query returns relevant results
- [ ] Code passes lint/format/type-check
- [ ] No code blocks split across chunks (manual review of 10 random chunks)

---

## 💡 Tips for Auggie

**Before coding:**
1. Read [RAG-004] from TASKS.md
2. Read chunking strategy from `notes/rag_reference_findings.md` Section D
3. Read schema definition from `notes/rag_reference_findings.md` Section C
4. Propose implementation plan and get confirmation

**During implementation:**
- Follow the chunking rules exactly (8 rules in Section D)
- Use the exact schema (13 fields in Section C)
- Preserve code blocks, tables, lists, shortcodes
- Extract frontmatter metadata
- Assign product_area and category from path

**Testing:**
- Start with unit tests on sample markdown
- Run integration test on 10 sample docs
- Run smoke test on 100 docs before full corpus
- Manually review 10 random chunks for quality

---

**Ready to go! 🚀**

