# redis-agent-control-plane

Agent control plane with context engine and RAG workflow for simplifying Redis Enterprise Infrastructure deployments.

## Overview

This project provides an intelligent agent control plane that uses Retrieval-Augmented Generation (RAG) to assist with Redis Enterprise deployment operations. The system is designed to be extensible for other use cases in the future.

**Current Status:**
- ✅ **RAG Pipeline (Phase 3 COMPLETE)** - Production-ready with FT.CREATE index and hybrid search
- 🎯 **Next Phase:** TBD

## Prerequisites

- Python 3.11 or higher
- [Poetry](https://python-poetry.org/docs/#installation) (recommended) OR pip + venv

## Quick Start

### 1. Install Dependencies

The Makefile auto-detects whether you have Poetry installed:

```bash
make install
```

**With Poetry (recommended):**

```bash
poetry install
```

**Without Poetry (using venv):**

```bash
make install-venv
# Then activate the virtual environment:
source venv/bin/activate
```

### 2. Run the Application

```bash
make run
```

Or directly with Poetry:

```bash
poetry run python -m redis_agent_control_plane.main
```

### 3. Run Tests

```bash
make test
```

## Development Commands

```bash
make help          # Show all available commands
make install       # Install dependencies
make run           # Run the application
make test          # Run tests with pytest
make lint          # Run ruff linter
make format        # Format code with black
make type-check    # Run mypy type checker
make all           # Run format, lint, type-check, and test
make clean         # Remove generated files and caches
```

## Project Structure

```
redis-agent-control-plane/
├── src/
│   └── redis_agent_control_plane/
│       ├── __init__.py
│       ├── main.py
│       └── rag/                    # ✅ RAG Pipeline (Phase 3 COMPLETE)
│           ├── chunker.py          # Adaptive H2/H3 chunking
│           ├── embedder.py         # Local embedding model
│           ├── indexer.py          # FT.CREATE index with HNSW
│           └── retriever.py        # Hybrid search (vector + BM25)
├── tests/
│   ├── __init__.py
│   ├── test_smoke.py
│   └── test_rag_*.py               # RAG pipeline tests
├── scripts/
│   ├── build_rag_index.py          # Build RAG index from docs
│   ├── test_rag_pipeline.py        # End-to-end pipeline test
│   ├── test_ft_search.py           # FT.SEARCH performance test
│   └── test_hybrid_search.py       # Hybrid search test
├── docs/
│   ├── RAG_PIPELINE.md             # RAG pipeline documentation
│   └── PHASE_3_QUICK_START.md      # Phase 3 quick start guide
├── notes/
│   ├── PHASE_3_COMPLETE.md         # Phase 3 completion report
│   └── rag_reference_findings.md   # Phase 1 design findings
├── pyproject.toml
├── Makefile
├── AUGGIE.md      # AI assistant operating manual
├── CONTEXT.md     # Repository context and architecture
├── TASKS.md       # Task definitions and status
└── README.md
```

## RAG Pipeline (Phase 3 COMPLETE ✅)

The RAG pipeline ingests Redis documentation, creates optimized indexes, and provides hybrid search capabilities.

### Quick Start

```bash
# Build RAG index from Redis docs
source venv/bin/activate
python3 scripts/build_rag_index.py --source ../docs/content --overwrite

# Test retrieval
python3 scripts/test_rag_pipeline.py

# Test hybrid search
python3 scripts/test_hybrid_search.py
```

### Features

- ✅ **FT.CREATE Index** - HNSW vector search (10-100x faster than brute-force)
- ✅ **Hybrid Search** - Vector + BM25 text search with RRF
- ✅ **Adaptive Chunking** - H2/H3 boundary chunking with code/table preservation
- ✅ **Local Embeddings** - Free, no API costs (sentence-transformers)
- ✅ **Production Ready** - 20k+ chunks, sub-100ms latency (P95)

### Documentation

- [RAG Pipeline Documentation](docs/RAG_PIPELINE.md) - Complete pipeline guide
- [Phase 3 Quick Start](docs/PHASE_3_QUICK_START.md) - Quick start guide
- [Phase 3 Complete](notes/PHASE_3_COMPLETE.md) - Completion report

## Contributing

See [AUGGIE.md](AUGGIE.md) for guidelines on working with AI assistance in this repository.

See [CONTEXT.md](CONTEXT.md) for architectural context and constraints.

See [TASKS.md](TASKS.md) for current tasks and development workflow.

## License

TODO: Add license information