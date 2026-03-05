# redis-agent-control-plane

Agent control plane with deterministic orchestration, validated runbooks, and RAG-powered context engine for simplifying Redis Enterprise Infrastructure deployments.

## Overview

This project provides an intelligent agent control plane that combines:
- **Deterministic Orchestration Layer** - 100% reproducible deployment routing and validated runbooks
- **RAG Pipeline** - Retrieval-Augmented Generation for documentation-based validation and context
- **Validated Runbooks** - 10 production-ready deployment runbooks extracted from official Redis documentation

The system enables reliable, repeatable Redis Enterprise deployments across VM, Kubernetes, and Cloud platforms with Active-Active support.

## Current Status

### ✅ Orchestration Layer (Phases A-E COMPLETE - 2026-03-05)

**Deterministic Routing System:**
- 100% deterministic routing (same DeploymentSpec → same Runbook, always)
- Validated over 100 iterations with zero variance
- 53 passing tests, 11 skipped

**10 Validated Runbooks:**
- Infrastructure: 1 (Redis Cloud VPC peering)
- Cluster Deployment: 3 (VM single-node, VM 3-node, Kubernetes 3-node)
- Active-Active Preparation: 2 (VM cluster linking, Kubernetes admission controller)
- Database Deployment: 4 (VM standard, VM CRDB, K8s REDB, K8s REAADB)

**Validation & Testing Tools:**
- `scripts/validate_runbooks.py` - Automated runbook validation against documentation
- `scripts/test_routing.py` - Interactive CLI for testing routing logic
- All runbooks validated against Redis Enterprise 8.0.x documentation
- All commands extracted from official Redis documentation (no synthesis)

### ✅ RAG Pipeline (Phase 3 COMPLETE - 2026-03-04)

**Production-Ready Features:**
- 20,249 chunks indexed from Redis documentation
- Hybrid search (vector + BM25) with FT.CREATE index
- <100ms query latency with HNSW algorithm
- 4,207 documents processed from Redis docs corpus
- Metadata filtering by product area and category

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

## Validated Runbooks

All runbooks are validated against official Redis Enterprise 8.0.x documentation with verified doc_refs.

### Infrastructure (1)
- **Redis Cloud VPC Peering** - Set up VPC peering between AWS VPC and Redis Cloud

### Cluster Deployment (3)
- **VM Single Node** - Deploy single-node Redis Enterprise for dev/test (4 steps)
- **VM 3-Node Cluster** - Deploy production 3-node cluster, reusable for multi-region (7 steps)
- **Kubernetes 3-Node Cluster** - Deploy Redis Enterprise Operator and REC (6 steps)

### Active-Active Preparation (2)
- **VM Active-Active Prep** - Configure cluster linking, FQDN, certificate exchange (9 steps)
- **Kubernetes Active-Active Prep** - Install admission controller, exchange secrets (9 steps)

### Database Deployment (4)
- **VM Standard Database** - Create standard database (simple + HA variants, 4 steps)
- **VM CRDB** - Create Active-Active CRDB across dual regions (5 steps)
- **Kubernetes REDB** - Create standard database on Kubernetes (4 steps)
- **Kubernetes REAADB** - Create Active-Active database on Kubernetes (6 steps)

## Key Features

### Deterministic Routing
```python
from redis_agent_control_plane.orchestration import DeploymentSpec, RunbookRouter

# Define deployment specification
spec = DeploymentSpec(
    product="redis_enterprise",
    platform="kubernetes",
    topology="clustered"
)

# Route to runbook (100% deterministic)
router = RunbookRouter()
runbook_id = router.route(spec)  # Always returns same runbook for same spec
runbook = router.load_runbook(runbook_id)
```

### Interactive Routing Test
```bash
# Test routing interactively
python scripts/test_routing.py

# Test a specific deployment spec
python scripts/test_routing.py --spec '{"product": "redis_enterprise", "platform": "vm", "topology": "single_node"}'

# List all available runbooks
python scripts/test_routing.py --list
```

### Runbook Validation
```bash
# Validate all runbooks against documentation
python scripts/validate_runbooks.py

# Validate a specific runbook
python scripts/validate_runbooks.py --runbook runbooks/redis_enterprise/vm/single_node.yaml
```

## Project Structure

```
redis-agent-control-plane/
├── src/
│   └── redis_agent_control_plane/
│       ├── __init__.py
│       ├── main.py
│       ├── orchestration/          # ✅ Orchestration Layer (Phases A-E COMPLETE)
│       │   ├── deployment_spec.py  # Deployment specification dataclass
│       │   ├── runbook.py          # Runbook dataclass with YAML loader
│       │   └── router.py           # Deterministic routing logic
│       └── rag/                    # ✅ RAG Pipeline (Phase 3 COMPLETE)
│           ├── chunker.py          # Adaptive H2/H3 chunking
│           ├── embedder.py         # Local embedding model
│           ├── indexer.py          # FT.CREATE index with HNSW
│           └── retriever.py        # Hybrid search (vector + BM25)
├── runbooks/                       # ✅ 10 Validated Runbooks
│   ├── redis_cloud/
│   │   └── aws/
│   │       └── vpc_peering.yaml
│   └── redis_enterprise/
│       ├── vm/
│       │   ├── single_node.yaml
│       │   ├── clustered_3node.yaml
│       │   └── active_active_prepare.yaml
│       ├── kubernetes/
│       │   ├── clustered.yaml
│       │   └── active_active.yaml
│       └── database/
│           ├── vm_standard.yaml
│           ├── vm_crdb.yaml
│           ├── kubernetes_redb.yaml
│           └── kubernetes_reaadb.yaml
├── tests/
│   ├── __init__.py
│   ├── test_smoke.py
│   ├── test_deployment_spec.py     # DeploymentSpec tests
│   ├── test_router.py              # Router determinism tests (11 tests)
│   ├── test_runbook.py             # Runbook loader tests
│   └── test_rag_*.py               # RAG pipeline tests
├── scripts/
│   ├── validate_runbooks.py        # ✅ Runbook validation CLI
│   ├── test_routing.py             # ✅ Interactive routing test CLI
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

## Architecture

### Orchestration Layer

The orchestration layer provides deterministic routing from deployment specifications to validated runbooks:

1. **DeploymentSpec** - Defines what to deploy (product, platform, topology, scale, networking)
2. **RunbookRouter** - Routes specs to runbooks deterministically (100% reproducible)
3. **Runbook** - YAML-based deployment procedures with validation and doc references
4. **Validation** - All runbooks validated against official Redis documentation

### RAG Pipeline

The RAG pipeline indexes Redis documentation and provides semantic search for validation and context:

1. **Chunker** - Adaptive H2/H3 boundary chunking with code block preservation
2. **Embedder** - Local sentence-transformers model for embeddings
3. **Indexer** - Redis FT.CREATE with HNSW vector index + BM25 text search
4. **Retriever** - Hybrid search with metadata filtering

**Features:**
- ✅ **FT.CREATE Index** - HNSW vector search (10-100x faster than brute-force)
- ✅ **Hybrid Search** - Vector + BM25 text search with RRF
- ✅ **Adaptive Chunking** - H2/H3 boundary chunking with code/table preservation
- ✅ **Local Embeddings** - Free, no API costs (sentence-transformers)
- ✅ **Production Ready** - 20k+ chunks, sub-100ms latency (P95)

## Testing

### Run All Tests

```bash
# Run all tests with quality checks
make all

# Just run tests
make test

# Run specific test file
PYTHONPATH=src pytest tests/test_router.py -v
```

### Test Coverage

- **53 passing tests**, 11 skipped
- Orchestration: 100% deterministic routing validated
- RAG Pipeline: Chunking, embedding, indexing, retrieval
- Runbook Loading: YAML parsing, validation, error handling

## Documentation

- **[AUGGIE.md](AUGGIE.md)** - AI assistant operating instructions and current phase status
- **[TASKS.md](TASKS.md)** - Detailed task definitions with acceptance criteria
- **[CONTEXT.md](CONTEXT.md)** - Architecture overview and technical context
- **[docs/RAG_PIPELINE.md](docs/RAG_PIPELINE.md)** - RAG pipeline technical documentation
- **[docs/PHASE_3_QUICK_START.md](docs/PHASE_3_QUICK_START.md)** - RAG pipeline quick start guide

## Roadmap

### ✅ Completed Phases

- **Phase A** - Deterministic routing and runbook registry
- **Phase B** - Validated VM cluster runbooks
- **Phase C** - Kubernetes and Active-Active preparation runbooks
- **Phase D** - Database deployment runbooks
- **Phase E** - Harness and testing tools
- **RAG Pipeline (Phase 3)** - Production-ready RAG with hybrid search

### 🔮 Future Phases (Deferred)

- **Phase F** - Context Pack Builder (RAG integration with orchestration)
- **Agent Layer** - Execution engine for runbooks
- **API Layer** - REST/gRPC endpoints for external interaction

## Contributing

See [AUGGIE.md](AUGGIE.md) for guidelines on working with AI assistance in this repository.

See [CONTEXT.md](CONTEXT.md) for architectural context and constraints.

See [TASKS.md](TASKS.md) for current tasks and development workflow.

## License

TODO: Add license information