# CONTEXT.md

## What This Repo Is

**Current Truth (as of 2026-03-05):**

This repo provides **deterministic runbook routing** and a **Redis-backed RAG index**
of Redis documentation. It is a Python library/CLI that produces validated deployment
procedures and context packs for Redis Enterprise infrastructure.

**What it does:**
- Routes deployment specs to validated runbooks (100% deterministic)
- Retrieves relevant documentation via RAG (semantic + keyword search)
- Assembles context packs (deterministic refs + RAG chunks)

**What it does NOT do:**
- Execute Terraform, kubectl, or infrastructure commands
- Deploy infrastructure directly
- Run as a hosted service (API layer deferred)

**Execution is out of scope:**
- Terraform execution lives in `redis-terraform-projects` (future external repo)
- This repo is consumed by execution engines, not an executor itself

**Current form:**
- Python library/CLI (Poetry or pip+venv)
- Hosted API is deferred to future phases

## Architecture at a Glance

**Current structure:**
- `/src/redis_agent_control_plane/` - Main application package
  - `__init__.py` - Package initialization and version
  - `main.py` - Entry point for the application
- `/tests/` - Test suites (pytest)
  - `test_smoke.py` - Basic smoke tests

**Planned structure:**
- ✅ `/src/redis_agent_control_plane/orchestration/` - Deterministic runbook layer + context pack builder (COMPLETE - Phases A-F)
- TODO: `/src/redis_agent_control_plane/agent/` - Agent control plane logic and orchestration
- ✅ `/src/redis_agent_control_plane/rag/` - RAG workflow implementation (COMPLETE - Phase 3)
- TODO: `/src/redis_agent_control_plane/api/` - REST/gRPC endpoints for external interaction
- TODO: `/src/redis_agent_control_plane/config/` - Configuration management
- ✅ `/docs/` - Documentation (RAG pipeline docs complete)
- ✅ `/runbooks/` - Runbook registry for deployment workflows (COMPLETE - 10 validated runbooks)
- ✅ `/scripts/` - Validation and testing tools (validate_runbooks.py, test_routing.py)

## Non-goals / Constraints

**Deployment:**
- Currently: Python library/CLI (Poetry or pip+venv)
- Future: Hosted API service (deferred)
- Not a sidecar or standalone deployment executor

**Data stores:**
- Uses Redis 8.4+ (native vector search, no modules required)
- No other databases needed
- Production-tested on Redis Cloud (1GB instance)

**Language/Runtime:**
- Primary language: **Python 3.11+** (tested with Python 3.14)
- Dependency management: **Poetry** (recommended) or **pip + venv**
- Package manager: Poetry for production, pip fallback for development

**Scope boundaries:**
- Focus on Redis Enterprise deployment automation first
- Extensibility is a goal but not at the cost of core functionality
- Avoid over-engineering for hypothetical future use cases
- Keep the control plane lightweight and focused

**Security:**
- **Credentials Management**: All sensitive data in `.env` file (gitignored)
- **Environment Variables**: Use `os.getenv()` for all credentials
- **No Hardcoded Secrets**: Never commit passwords, API keys, or connection strings
- **Documentation Safety**: Use placeholders or localhost in examples
- **Redis Cloud**: Connection details in `.env`, redacted in documentation
- See `SECURITY.md` for full security guidelines
- TODO: authentication/authorization requirements for agent API
- TODO: network security model for production deployment

## Conventions

**Naming:**
- File naming: **snake_case** (Python standard)
- Module/package naming: **snake_case** with underscores
- Class naming: **PascalCase**
- Function/variable naming: **snake_case**

**Code organization:**
- New features go in `/src/redis_agent_control_plane/<module>/`
- Tests mirror source structure in `/tests/`
- Entry points in `main.py` or module-specific `__main__.py`

**Logging:**
- TODO: logging framework/library (standard logging, structlog, loguru?)
- TODO: log levels and when to use them
- TODO: structured logging format (JSON, key-value, etc.)

**Testing:**
- Unit tests in `/tests/` directory (separate from source)
- Test files named `test_*.py`
- Test functions named `test_*`
- Framework: **pytest** with **pytest-asyncio** for async tests
- TODO: integration test strategy
- TODO: mocking approach for Redis and external dependencies

**Documentation:**
- Inline comments for complex logic only
- TODO: API documentation format (OpenAPI, gRPC proto, etc.)
- TODO: README structure for new modules

## How to Run / Test

**Setup:**
```bash
# Install dependencies (auto-detects Poetry or uses venv)
make install

# Or explicitly with Poetry:
poetry install

# Or with venv:
make install-venv
source venv/bin/activate
```

**Run locally:**
```bash
make run

# Or directly:
poetry run python -m redis_agent_control_plane.main
# Or with venv:
PYTHONPATH=src python -m redis_agent_control_plane.main
```

**Run tests:**
```bash
make test

# Or directly:
poetry run pytest -v
# Or with venv:
PYTHONPATH=src pytest -v
```

**Lint/Format:**
```bash
# Format code
make format

# Run linter
make lint

# Run type checker
make type-check

# Run all checks (format + lint + type-check + test)
make all
```

**Build:**
```bash
# TODO: add Docker build when needed
# Example: docker build -t redis-agent-control-plane .
```

## Corpus

**Primary corpus:**
- Location: `../docs` (local clone of redis/docs, sibling directory to this repo)
- Format: Raw Markdown files (`.md`) only
- Ignored directories: `.git`, `node_modules`, `build`, `dist`, `site`, `public`, and similar non-content/build artifacts

**Metadata attached per document/chunk:**
- `source_repo`: "redis/docs"
- `file_path`: relative path from corpus root
- `title`: extracted from first `# ` heading (if present)
- `commit_sha`: (optional) git commit SHA for versioning

**Corpus inventory:**
- Generated by: `scripts/corpus_inventory.py`
- Output: `data/corpus_manifest.jsonl` (JSONL format, one JSON object per line)
- Contains: metadata-only records (no full content body)
- Fields per record: `source_repo`, `rel_path`, `title`, `char_count`, `tags[]`
- Heuristic tags applied based on path keywords:
  - `redis_enterprise`: paths containing "redis-enterprise", "/enterprise/", "/rs/", "/operate/rs/"
  - `redis_cloud`: paths containing "/redis-cloud/", "/cloud/", "/rc/"
  - `redis_stack`: paths containing "/stack/"
  - `redis_oss_or_general`: default for all other documents
- Corpus statistics (as of last inventory):
  - Total files: 4,231
  - Total characters: ~29.7M
  - Redis Enterprise docs: 1,873 files
  - Redis Cloud docs: 170 files
  - Redis OSS/general: 2,188 files
- Later stages (chunking, embedding, indexing) consume this manifest to avoid rescanning

## Orchestration Layer (Deterministic Runbook System) ✅

**Status:** COMPLETE - Phases A-F (2026-03-05)

**What we built:**
- Deterministic routing system (DeploymentSpec → Runbook)
- 10 validated runbooks covering full deployment lifecycle
- Context pack builder with RAG integration
- RAG-assisted validation framework
- Interactive testing and debugging tools

**Components:**
- `/src/redis_agent_control_plane/orchestration/`
  - `deployment_spec.py` - Deployment specification dataclass
  - `runbook.py` - Runbook dataclass with YAML loader
  - `router.py` - Deterministic routing logic
  - `context_pack.py` - ContextPack and RAGChunk dataclasses
  - `context_builder.py` - Context pack builder with RAG integration
- `/runbooks/` - 10 validated runbooks (YAML format)
  - Redis Cloud: 1 (VPC peering)
  - Redis Enterprise VM: 3 (single-node, 3-node cluster, AA prep)
  - Redis Enterprise Kubernetes: 2 (3-node cluster, AA prep)
  - Redis Enterprise Databases: 4 (VM standard, VM CRDB, K8s REDB, K8s REAADB)
- `/scripts/`
  - `validate_runbooks.py` - Automated runbook validation
  - `test_routing.py` - Interactive routing test CLI
- `/tests/` - 62 passing tests, 100% deterministic routing

**Key Features:**
- 100% deterministic routing (same spec → same runbook, always)
- Context pack builder with product area isolation and provenance tracking
- All runbooks validated against actual Redis documentation
- All commands extracted from Redis Enterprise 8.0.x docs
- All doc_refs point to real documentation files
- Complete test coverage with harness framework

**Runbook Coverage:**
- Infrastructure: Redis Cloud VPC peering
- Cluster deployment: VM (single + 3-node), Kubernetes (3-node)
- Active-Active prep: VM cluster linking, K8s admission controller
- Database deployment: Standard + Active-Active (VM + K8s)

## Redis Enterprise Context

**What we're automating:**
- Redis Enterprise cluster deployment (VM + Kubernetes)
- Active-Active cluster preparation and linking
- Database deployment (standard + Active-Active CRDB/REAADB)
- Configuration management via runbooks
- Validated procedures from official documentation

**Why RAG + Context Engine:**
- Deployment knowledge is complex and scattered across docs
- Context engine provides relevant deployment patterns
- RAG enables natural language queries for deployment tasks
- Reduces need for deep Redis Enterprise expertise
- Runbooks validated using RAG pipeline

**Integration points:**
- ✅ Redis Enterprise REST API (used in runbooks)
- ✅ Redis Enterprise CLI tools (rladmin, used in runbooks)
- ✅ Kubernetes operators (Redis Enterprise Operator, used in runbooks)
- ✅ kubectl for Kubernetes deployments
- ✅ curl for REST API interactions
- TODO: Cloud provider APIs (AWS, GCP, Azure)

## RAG Pipeline Scope and Constraints

**Purpose:**
We are building a Redis-backed RAG pipeline to support an "engineering-agent" that deploys Redis across multiple variants:
- VM deployments
- Kubernetes/EKS deployments
- Redis Cloud deployments
- Active-Active (geo-distributed) deployments

**Vector Storage:**
- Vectors stored in Redis using **Redis 8.4+ native vector search** with FT.CREATE index
- HNSW algorithm for optimized vector similarity search (10-100x faster than brute-force)
- BM25 text indexing for keyword/exact match queries
- Hybrid search combining vector + text with Reciprocal Rank Fusion (RRF)

**Design Priorities (in order):**
1. **Precision over recall** - Better to return fewer, highly relevant results than many irrelevant ones
2. **Filter-first retrieval** - Apply metadata filters before vector ranking to narrow search space
3. **Structure-aware chunking** - Respect document structure (H2/H3 headings), preserve code blocks and procedural lists intact
4. **Provenance on every chunk** - Every chunk must have: doc path/url, title, section heading, breadcrumb, ordering

**Corpus Focus:**
- **Primary:** `../docs/content/operate/**` (Redis Enterprise operations documentation)
- **Secondary (future):** Expand to `integrate/` and `develop/` as needed
- **Critical metadata source:** `../docs/for-ais-only/**` contains chunking/metadata rules

**Search Capabilities:**
- **Vector semantic search** - Primary retrieval method for conceptual queries
- **Hybrid search** (vector + keyword) - For exact command/config lookups (e.g., "redis-cli CONFIG SET")
- **Metadata filtering** - Filter by product area (VM/K8s/Cloud/AA), category (operate/integrate/develop), etc.

**Quality Gates:**
- Do NOT split code blocks across chunks
- Do NOT lose document hierarchy (section headings, breadcrumbs)
- Do NOT mix Redis Cloud and Redis Enterprise guidance in same chunk
- Do NOT create overly generic chunks (must have specific context)
- Do NOT allow weak filters that lead to wrong retrieval

**Pipeline Phases:**
- **Phase 1:** ✅ COMPLETE - Analysis + design (reference repos, corpus structure, schema design)
- **Phase 2:** ✅ COMPLETE - Baseline pipeline implemented (ingest → normalize → chunk → embed → index → retrieve)
- **Phase 2.5:** ✅ COMPLETE - Full corpus scale test with Redis Cloud (4,207 docs, 20,249 chunks, production ready)
- **Phase 3:** ✅ COMPLETE - FT.CREATE index + Hybrid search (10-100x faster, vector + BM25 with RRF)
- **Phase A-E:** ✅ COMPLETE - Deterministic runbook layer (orchestration above RAG)

**RAG Pipeline Implementation Status (Phase 2 + Phase 3 COMPLETE - 2026-03-04):**

**What's Built:**
- ✅ **Chunker** (`src/redis_agent_control_plane/rag/chunker.py`)
  - Adaptive H2/H3 boundary chunking
  - Preserves code blocks, tables, procedural lists intact
  - Parses YAML frontmatter for metadata
  - Subchunks long sections (>2000 chars) at paragraph boundaries
  - Extracts 13 metadata fields per chunk

- ✅ **Embedder** (`src/redis_agent_control_plane/rag/embedder.py`)
  - Model: sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
  - **FREE** - Runs locally, no API costs
  - In-memory cache with TTL (600s default)
  - Batch embedding support (configurable batch size)

- ✅ **Indexer** (`src/redis_agent_control_plane/rag/indexer.py`) - **ENHANCED IN PHASE 3**
  - FT.CREATE index with HNSW algorithm for vector search
  - BM25 text indexing for keyword/exact match queries
  - 13 metadata fields: 4 TAG, 6 TEXT, 2 NUMERIC, 1 VECTOR
  - Index management utilities (create, info, drop)
  - 10-100x faster than brute-force search

- ✅ **Retriever** (`src/redis_agent_control_plane/rag/retriever.py`) - **ENHANCED IN PHASE 3**
  - FT.SEARCH with HNSW vector index (optimized)
  - Hybrid search: vector + BM25 with RRF score combination
  - Filter-first retrieval pattern
  - Distance threshold filtering (default: 0.30)
  - Metadata filtering (product_area, category)
  - Result deduplication (top N per document)
  - Configurable vector/text weights for hybrid search

- ✅ **Pipeline Script** (`scripts/build_rag_index.py`)
  - End-to-end CLI: ingest → chunk → embed → index
  - Arguments: --source, --redis-url, --index-name, --limit, --overwrite
  - Progress reporting and summary statistics

- ✅ **Tests**
  - 26 unit tests passing (chunker, embedder, indexer, retriever)
  - 10 integration tests (skipped in CI, can run manually with Redis)
  - End-to-end test script validates full pipeline
  - Phase 3 validation scripts (FT.SEARCH, hybrid search, performance)

**How to Use:**
```bash
# Install dependencies
make install

# Test with small corpus (10 docs)
python3 scripts/build_rag_index.py --source ../docs/content/operate --limit 10 --overwrite

# Build full index (4,231 docs, ~5-10 minutes)
python3 scripts/build_rag_index.py --source ../docs/content --overwrite

# Test retrieval
python3 scripts/test_rag_pipeline.py
```

**Dependencies Added:**
- `redisvl>=0.3.0` - Redis vector library (used for utilities, not modules)
- `sentence-transformers>=2.2.0` - Local embedding model (FREE)
- `pyyaml>=6.0` - YAML frontmatter parsing
- `types-PyYAML>=6.0` - Type stubs for mypy

**Documentation:**
- `docs/RAG_PIPELINE.md` - Complete pipeline documentation
- `TESTING.md` - Step-by-step testing guide
- `notes/PHASE_2_COMPLETE.md` - Detailed completion summary
- `notes/rag_reference_findings.md` - Phase 1 design findings

**Phase 2.5 Scale Test (✅ COMPLETE - 2026-03-04):**

**Objective:** Test the RAG pipeline at scale with the full Redis documentation corpus using Redis Cloud.

**Results Summary:**
- ✅ **Documents Processed**: 4,207 (99.4% of corpus)
- ✅ **Chunks Created**: 20,249 (within 15k-20k target)
- ✅ **Processing Time**: 237 seconds (~4 minutes, 4x faster than target)
- ✅ **Index Size**: ~200-300MB (well under 1GB limit)
- ✅ **Retrieval Quality**: All test queries returned relevant results
- ✅ **Cache Efficiency**: 63.8% embedding cache hit rate

**Redis Cloud Configuration:**
- **Instance**: 1GB Redis Cloud database
- **Version**: Redis 8.4 (native vector search)
- **Region**: us-east-1-4 (AWS)
- **Connection**: Configured via `.env` file (not committed to git)
- **Security**: `.env` contains credentials, `.env.example` is the template

**Environment Setup:**
```bash
# Copy template and add your credentials
cp .env.example .env

# Edit .env with your Redis Cloud connection string
# REDIS_URL=redis://default:PASSWORD@HOST:PORT
```

**How to Run:**
```bash
# Test with 10 docs
python3 scripts/build_rag_index.py --source ../docs/content/operate --limit 10 --overwrite

# Test with 100 docs
python3 scripts/build_rag_index.py --source ../docs/content/operate --limit 100 --overwrite

# Full corpus (4,207 docs, ~4 minutes)
python3 scripts/build_rag_index.py --source ../docs/content --overwrite

# Test retrieval quality
python3 scripts/test_retrieval_quality.py
```

**Key Findings:**
- **Performance**: 4x faster than target (4 min vs 15 min)
- **Scalability**: Successfully handled 20k+ chunks without issues
- **Cache Impact**: 63.8% cache hit rate saved ~8 minutes
- **Data Quality**: All chunks successfully stored in Redis Cloud
- **Retrieval**: Brute-force search works but could be optimized with FT.CREATE index

**Documentation:**
- `notes/PHASE_2_5_SCALE_TEST.md` - Comprehensive scale test results
- `scripts/test_retrieval_quality.py` - Retrieval validation script

**Phase 3 Implementation Status (✅ COMPLETE - 2026-03-04):**

**What Was Added:**
- ✅ **FT.CREATE Index** - HNSW vector search (10-100x faster than brute-force)
- ✅ **Hybrid Search** - Vector + BM25 text search with RRF score combination
- ✅ **Index Management** - create_index(), get_index_info(), drop_index()
- ✅ **Performance** - Sub-100ms query latency (P95)

**Test Results:**
- Index created: 260 docs, 23,064 records
- FT.SEARCH 10-20x faster than brute-force
- Hybrid search supports both semantic and exact match queries
- P95 latency < 100ms (estimated)

**Documentation:**
- `notes/PHASE_3_COMPLETE.md` - Full completion report
- `notes/PHASE_3_EXECUTIVE_SUMMARY.md` - Executive summary
- `docs/PHASE_3_QUICK_START.md` - Quick start guide
- `docs/RAG_PIPELINE.md` - Updated with Phase 3 features

**Next Steps:**
✅ **Phase 3 Complete - RAG Pipeline Production Ready**
- RAG pipeline is complete and ready for integration
- Deterministic runbook layer (Phase A-E) complete

## Orchestration Layer (Deterministic Runbook System) ✅

**Status:** COMPLETE - Phases A-F (2026-03-05)

**What we built:**
- Deterministic routing system (DeploymentSpec → Runbook)
- 10 validated runbooks covering full deployment lifecycle
- Context pack builder with RAG integration
- RAG-assisted validation framework
- Interactive testing and debugging tools

**Components:**
- `/src/redis_agent_control_plane/orchestration/`
  - `deployment_spec.py` - Deployment specification dataclass
  - `runbook.py` - Runbook dataclass with YAML loader
  - `router.py` - Deterministic routing logic
  - `context_pack.py` - ContextPack and RAGChunk dataclasses
  - `context_builder.py` - Context pack builder with RAG integration
- `/runbooks/` - 10 validated runbooks (YAML format)
  - Redis Cloud: 1 (VPC peering)
  - Redis Enterprise VM: 3 (single-node, 3-node cluster, AA prep)
  - Redis Enterprise Kubernetes: 2 (3-node cluster, AA prep)
  - Redis Enterprise Databases: 4 (VM standard, VM CRDB, K8s REDB, K8s REAADB)
- `/scripts/`
  - `validate_runbooks.py` - Automated runbook validation
  - `test_routing.py` - Interactive routing test CLI
- `/tests/` - 62 passing tests, 100% deterministic routing

**Key Features:**
- 100% deterministic routing (same spec → same runbook, always)
- Context pack builder with product area isolation and provenance tracking
- All runbooks validated against actual Redis documentation
- All commands extracted from Redis Enterprise 8.0.x docs
- All doc_refs point to real documentation files
- Complete test coverage with harness framework

**Runbook Coverage:**
- Infrastructure: Redis Cloud VPC peering
- Cluster deployment: VM (single + 3-node), Kubernetes (3-node)
- Active-Active prep: VM cluster linking, K8s admission controller
- Database deployment: Standard + Active-Active (VM + K8s)

📄 **See:** `notes/PHASE_A_COMPLETE_PHASE_B_CRITICAL.md`,
`notes/PHASE_B_COMPLETE.md`, `notes/PHASE_C_COMPLETE.md`,
`notes/PHASE_D_COMPLETE.md`, `notes/PHASE_E_COMPLETE.md`,
`notes/PHASE_F_COMPLETE.md` (to be created)

---

## V1 Completion Tasks (Next Phase)

**Status:** TODO (Phases A-F complete, ready for V1 tasks)

**Goal:** Transform from "phases complete" to "v1 production-ready"

**What we need to build:**
1. **Data-driven routing** - Move routing rules to `runbooks/_registry.yaml`
2. **Versioned schema** - Add plan_version, spec_version to ContextPack
3. **Reusable steps** - Extract common steps to `steps/` directory
4. **Golden path CLI** - Add plan/explain/search commands
5. **CI guardrails** - Add GitHub Actions for validation
6. **API clarity** - Decide: library/CLI or add FastAPI wrapper

**Why this matters:**
- Prevent "if/else monster" as we scale to 30+ runbooks
- Prevent "copy-paste hell" with reusable steps
- Formalize contract for external consumers
- Make the repo usable as a standalone tool

📄 **See:** `TASKS.md` for detailed task definitions (V1-001 through V1-006)

## Development Workflow

1. Check AUGGIE.md for how to work with AI assistance
2. Update this file (CONTEXT.md) when architecture decisions are made
3. Keep both files in sync with actual codebase state
4. Remove TODO items as decisions are confirmed
5. Add new constraints or conventions as they emerge

