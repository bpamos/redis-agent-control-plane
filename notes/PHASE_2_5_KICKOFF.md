# Phase 2.5 Kickoff: Full Corpus Scale Test with Redis Cloud

**Date:** 2026-03-04  
**Task:** [RAG-004.5] Phase 2.5: Full Corpus Test with Redis Cloud  
**Status:** Ready to Start

## Objective

Test the Phase 2 RAG pipeline at scale by ingesting the full Redis documentation corpus (4,231 documents) into a production Redis Cloud instance.

## Why Phase 2.5?

Phase 2 implementation is complete and tested with small test documents (7 chunks). Before moving to Phase 3 (advanced features) or integration, we need to validate that the pipeline works at production scale with real documentation.

## Redis Cloud Configuration

**Instance Details:**
- **Provider**: Redis Cloud
- **Size**: 1GB database
- **Version**: Redis 8.4 (native vector search support)
- **Region**: us-east-1-4 (AWS)
- **Endpoint**: redis-17562.crce219.us-east-1-4.ec2.cloud.redislabs.com:17562

**Security:**
- Connection string stored in `.env` file (not committed to git)
- `.env.example` provides template for configuration
- `.env` is in `.gitignore` to prevent credential leaks

## Environment Setup Complete

✅ **Files Created:**
- `.env` - Contains actual Redis Cloud credentials (not committed)
- `.env.example` - Template for Redis configuration (committed)

✅ **Scripts Updated:**
- `scripts/build_rag_index.py` - Now reads `REDIS_URL` from `.env`
- `scripts/test_rag_pipeline.py` - Now reads `REDIS_URL` from `.env`

✅ **Dependencies Added:**
- `python-dotenv>=1.0.0` - For loading `.env` files

✅ **Documentation Updated:**
- `TASKS.md` - Added [RAG-004.5] task definition
- `CONTEXT.md` - Added Phase 2.5 section with configuration details
- `AUGGIE.md` - Updated current phase and kickoff instructions

## Staged Testing Plan

### Stage 1: 10 Documents (Validation)
**Command:**
```bash
python3 scripts/build_rag_index.py --source ../docs/content/operate --limit 10 --overwrite
```

**Purpose:** Validate Redis Cloud connection and basic functionality  
**Expected:** ~40-50 chunks, < 1 minute processing  
**Validates:** Connection works, chunking works, indexing works

### Stage 2: 100 Documents (Performance)
**Command:**
```bash
python3 scripts/build_rag_index.py --source ../docs/content/operate --limit 100 --overwrite
```

**Purpose:** Validate performance and memory usage at medium scale  
**Expected:** ~400-500 chunks, 2-3 minutes processing  
**Validates:** No memory issues, acceptable performance

### Stage 3: Full Corpus (Production)
**Command:**
```bash
python3 scripts/build_rag_index.py --source ../docs/content --overwrite
```

**Purpose:** Validate production readiness with full corpus  
**Expected:** ~15,000-20,000 chunks, 5-10 minutes processing  
**Validates:** All documents process successfully, index size < 1GB

## Quality Validation

After indexing, test retrieval quality with sample queries:

1. "How do I configure Active-Active replication?"
2. "What are the eviction policies in Redis?"
3. "How do I deploy Redis on Kubernetes?"
4. "What is the difference between Redis Cloud and Redis Software?"

**Validate:**
- Retrieval returns relevant results
- Metadata filtering works (product_area, category)
- Deduplication works (top N chunks per document)
- Retrieval latency < 1 second

## Success Criteria

- ✅ All 4,231 documents processed without errors
- ✅ Retrieval returns relevant results for test queries
- ✅ Index size < 1GB
- ✅ Processing time < 15 minutes
- ✅ No performance issues or crashes

## Deliverables

1. **Updated Scripts** - Scripts now use `.env` for configuration
2. **Scale Test Results** - Document in `notes/PHASE_2_5_SCALE_TEST.md`
3. **Updated Documentation** - Update Phase 2 completion notes with scale validation

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Index size exceeds 1GB | Monitor during Stage 2, adjust chunking if needed |
| Performance issues | Staged testing allows early detection |
| Redis Cloud connection issues | Test connection first, have fallback to local |
| Unexpected document formats | Log errors, handle gracefully, document edge cases |

## Next Steps After Completion

**If Successful:**
- Move to Phase 3 (Hybrid Search, Reranking, Query Rewriting)
- OR Integrate with Agent (FastAPI endpoints, connect to control plane)

**If Issues Found:**
- Fix issues and re-test
- Document lessons learned
- Adjust implementation as needed

## How to Kick Off

**Start a new Auggie session with:**

```
Execute Phase 2.5 from TASKS.md: [RAG-004.5] Phase 2.5: Full Corpus Test with Redis Cloud

Test the RAG pipeline at scale by ingesting the full Redis documentation corpus into Redis Cloud.

Important:
- Use Redis Cloud connection from .env file (already configured)
- Run staged tests: 10 docs → 100 docs → full corpus (4,231 docs)
- Validate retrieval quality with sample queries
- Document results in notes/PHASE_2_5_SCALE_TEST.md
- DO NOT commit .env file (contains credentials)
```

## Expected Duration

**Total Time:** 30-45 minutes
- Stage 1: 5 minutes (run + validate)
- Stage 2: 10 minutes (run + validate)
- Stage 3: 15 minutes (run + validate)
- Documentation: 10 minutes

---

**Ready to start Phase 2.5!** 🚀

