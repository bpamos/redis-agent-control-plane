# redis-agent-control-plane

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/your-org/redis-agent-control-plane/releases/tag/v1.0.0)
[![Status](https://img.shields.io/badge/status-production--ready-green.svg)](https://github.com/your-org/redis-agent-control-plane)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-97%20passing-brightgreen.svg)](https://github.com/your-org/redis-agent-control-plane)

Agent control plane with deterministic orchestration, validated runbooks, and RAG-powered context engine for simplifying Redis Enterprise Infrastructure deployments.

## Overview

This project provides an intelligent agent control plane that combines:
- **Deterministic Orchestration Layer** - 100% reproducible deployment routing and validated runbooks
- **RAG Pipeline** - Retrieval-Augmented Generation for documentation-based validation and context
- **Validated Runbooks** - 10 production-ready deployment runbooks extracted from official Redis documentation

The system produces validated runbooks and context packs for reliable, repeatable Redis Enterprise deployments across VM, Kubernetes, and Cloud platforms with Active-Active support.

## What This Repo Is (and Isn't)

**This repo IS:**
- **Deterministic planning + validated runbooks** - 100% reproducible deployment procedures
- **RAG-powered knowledge retrieval** - Semantic search over Redis documentation
- **Context pack builder** - Combines deterministic doc refs with RAG-retrieved chunks for agent consumption

**This repo IS NOT:**
- **A deployment executor** - Does not run Terraform, kubectl, or infrastructure commands
- **A hosted API service** - This is a Python library and CLI tool (HTTP API deferred to v2 if needed)

**Execution happens elsewhere:**
- Terraform deployments: `redis-terraform-projects` (future external consumer)
- This repo produces: validated runbooks + context packs for deployments

## Usage Modes

This project can be used in two ways:

### 1. CLI Tool (Primary Interface)

The CLI provides 5 commands for interactive use:

```bash
redis-agent-control-plane plan --spec deployment.yaml
redis-agent-control-plane explain context_pack.json
redis-agent-control-plane search "How do I enable TLS?"
redis-agent-control-plane validate --all
redis-agent-control-plane list runbooks
```

See [Quick Start](#quick-start) for detailed CLI usage.

### 2. Python Library (Programmatic Access)

Import and use the modules directly in your Python code:

```python
from redis_agent_control_plane.orchestration.router import RunbookRouter
from redis_agent_control_plane.orchestration.deployment_spec import DeploymentSpec
from redis_agent_control_plane.orchestration.context_builder import ContextBuilder

# Route to runbook
spec = DeploymentSpec.from_dict({
    "product": "redis_enterprise",
    "platform": "kubernetes",
    "topology": "clustered",
    # ... other fields
})
router = RunbookRouter()
runbook_id = router.route(spec)

# Build context pack
builder = ContextBuilder()
# ... use builder to create context packs
```

**Note:** HTTP API is not currently provided. If you need an API interface, please open an issue to discuss requirements. API support may be added in v2 based on demand.

## Current Status

**🎉 v1.0.0 Production Ready (2026-03-05)**

All 6 V1 completion tasks finished:
- ✅ Data-driven routing registry
- ✅ Versioned context pack schema
- ✅ Reusable step library (21 steps)
- ✅ Golden path CLI (5 commands)
- ✅ CI anti-rot guardrails
- ✅ API clarity decision (library/CLI)

### ✅ Orchestration Layer (Phases A-F COMPLETE - 2026-03-05)

**Deterministic Routing System:**
- 100% deterministic routing (same DeploymentSpec → same Runbook, always)
- Data-driven registry-based routing (adding runbooks = config change, not code change)
- Priority-based matching with collision detection
- Validated over 100 iterations with zero variance
- 97 passing tests, 11 skipped

**10 Validated Runbooks:**
- Infrastructure: 1 (Redis Cloud VPC peering)
- Cluster Deployment: 3 (VM single-node, VM 3-node, Kubernetes 3-node)
- Active-Active Preparation: 2 (VM cluster linking, Kubernetes admission controller)
- Database Deployment: 4 (VM standard, VM CRDB, K8s REDB, K8s REAADB)

**Reusable Step Library:**
- 21 reusable deployment steps in `steps/` directory
- DRY principle: define steps once, reference everywhere
- Parameterized steps for flexible configuration
- Supports both inline and referenced steps in runbooks
- `scripts/validate_steps.py` - Automated step validation

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

### 2. Use the CLI

The CLI provides 5 main commands for working with deployment plans:

```bash
# Show help
redis-agent-control-plane --help

# Generate a context pack from a deployment spec
redis-agent-control-plane plan --spec examples/kubernetes_clustered.yaml

# Interactive mode
redis-agent-control-plane plan --interactive

# Explain a context pack in markdown
redis-agent-control-plane explain context_pack.json

# Search documentation
redis-agent-control-plane search "How do I enable TLS?"

# List available runbooks and steps
redis-agent-control-plane list runbooks
redis-agent-control-plane list steps

# Validate all components
redis-agent-control-plane validate --all
```

**Example Workflow:**

```bash
# 1. Generate a context pack
redis-agent-control-plane plan --spec examples/kubernetes_clustered.yaml -o my_plan.json

# 2. Review the plan
redis-agent-control-plane explain my_plan.json

# 3. Search for additional context
redis-agent-control-plane search "Kubernetes deployment best practices" --product redis_enterprise
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

### Registry-Based Routing

The routing system uses a data-driven registry (`runbooks/_registry.yaml`) that maps deployment specifications to runbooks. This makes adding new runbooks a **config change, not a code change**.

**Key Benefits:**
- ✅ Adding runbooks = editing YAML, not writing code
- ✅ Priority-based matching for specialized variants
- ✅ Collision detection prevents ambiguous routing
- ✅ Backward compatible with legacy routing

**Registry Structure:**
```yaml
runbooks:
  - id: runbook.redis_enterprise.kubernetes.clustered
    name: "Redis Enterprise on Kubernetes - 3-Node Cluster"
    path: "runbooks/redis_enterprise/kubernetes/clustered.yaml"
    selectors:
      product: redis_enterprise
      platform: kubernetes
      topology: clustered
    priority: 100
    enabled: true
```

**Routing Algorithm:**
1. Load all enabled runbooks from registry
2. Match selectors against DeploymentSpec (all must match)
3. Sort by priority (descending)
4. Return highest priority match
5. Fail loudly if no match or ambiguous match (same priority)

**Validate Registry:**
```bash
# Validate registry schema, file existence, and detect collisions
python scripts/validate_registry.py
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

### Reusable Step Library

The step library eliminates duplication across runbooks by defining common deployment steps once and referencing them everywhere.

**Step Structure:**
```yaml
# steps/redis_enterprise/kubernetes/install_operator.yaml
step:
  id: install_operator
  name: "Install Redis Enterprise Operator"
  description: "Deploy the Redis Enterprise Operator using the official bundle YAML"
  doc_refs:
    - path: "operate/kubernetes/deployment/quick-start.md"
      section: "Install the operator"
  tool: kubectl
  command: "kubectl apply -f https://raw.githubusercontent.com/RedisLabs/redis-enterprise-k8s-docs/master/bundle.yaml"
  validation:
    command: "kubectl get deployment redis-enterprise-operator -n $NAMESPACE"
    expect: "redis-enterprise-operator"
    retry: 10
    retry_delay: 5
  parameters:
    - name: namespace
      type: string
      default: "redis"
      description: "Kubernetes namespace for the operator"
```

**Using Steps in Runbooks:**
```yaml
# runbooks/redis_enterprise/kubernetes/clustered.yaml
runbook:
  id: runbook.redis_enterprise.kubernetes.clustered
  steps:
    - step_ref: redis_enterprise/kubernetes/install_operator
      parameters:
        namespace: $NAMESPACE

    - step_ref: redis_enterprise/kubernetes/wait_operator_ready
      parameters:
        namespace: $NAMESPACE
```

**Benefits:**
- ✅ Define steps once, reference everywhere
- ✅ Update once, applies everywhere
- ✅ Parameterized for flexibility
- ✅ Supports both inline and referenced steps
- ✅ 21 reusable steps across VM, Kubernetes, and database operations

**Validate Steps:**
```bash
# Validate all step files
python scripts/validate_steps.py
```

**Step Categories:**
- `steps/redis_enterprise/kubernetes/` - Kubernetes deployment steps (7 steps)
- `steps/redis_enterprise/vm/` - VM deployment steps (6 steps)
- `steps/redis_enterprise/database/` - Database creation steps (7 steps)
- `steps/redis_cloud/aws/` - AWS-specific steps (1 step)

## Project Structure

```
redis-agent-control-plane/
├── src/
│   └── redis_agent_control_plane/
│       ├── __init__.py
│       ├── main.py
│       ├── orchestration/          # ✅ Orchestration Layer (Phases A-F COMPLETE)
│       │   ├── deployment_spec.py  # Deployment specification dataclass
│       │   ├── runbook.py          # Runbook dataclass with YAML loader
│       │   ├── router.py           # Deterministic routing logic
│       │   ├── context_pack.py     # ContextPack and RAGChunk dataclasses
│       │   └── context_builder.py  # Context pack builder with RAG integration
│       └── rag/                    # ✅ RAG Pipeline (Phase 3 COMPLETE)
│           ├── chunker.py          # Adaptive H2/H3 chunking
│           ├── embedder.py         # Local embedding model
│           ├── indexer.py          # FT.CREATE index with HNSW
│           └── retriever.py        # Hybrid search (vector + BM25)
├── runbooks/                       # ✅ 10 Validated Runbooks
│   ├── _registry.yaml              # 🆕 Data-driven routing registry
│   ├── redis_cloud/
│   │   └── aws/
├── steps/                          # 🆕 Reusable Step Library (21 steps)
│   ├── README.md                   # Step library documentation
│   ├── redis_enterprise/
│   │   ├── kubernetes/             # Kubernetes deployment steps
│   │   ├── vm/                     # VM deployment steps
│   │   └── database/               # Database creation steps
│   └── redis_cloud/
│       └── aws/                    # AWS-specific steps
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
│   ├── test_router.py              # Router tests (20 tests, including registry routing)
│   ├── test_runbook.py             # Runbook loader tests
│   ├── test_context_builder.py     # Context pack builder tests (9 tests)
│   └── test_rag_*.py               # RAG pipeline tests
├── scripts/
│   ├── validate_runbooks.py        # ✅ Runbook validation CLI
│   ├── validate_registry.py        # 🆕 Registry validation CLI
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

- **62 passing tests**, 11 skipped (integration tests requiring Redis)
- Orchestration: 100% deterministic routing validated
- Context Pack Builder: Product area isolation, bounded results, provenance tracking
- RAG Pipeline: Chunking, embedding, indexing, retrieval
- Runbook Loading: YAML parsing, validation, error handling

## Documentation

- **[AUGGIE.md](AUGGIE.md)** - AI assistant operating instructions and current phase status
- **[TASKS.md](TASKS.md)** - Detailed task definitions with acceptance criteria
- **[CONTEXT.md](CONTEXT.md)** - Architecture overview and technical context
- **[docs/RAG_PIPELINE.md](docs/RAG_PIPELINE.md)** - RAG pipeline technical documentation
- **[docs/PHASE_3_QUICK_START.md](docs/PHASE_3_QUICK_START.md)** - RAG pipeline quick start guide
- **[docs/context_pack_schema.md](docs/context_pack_schema.md)** - ContextPack schema documentation and versioning

## Roadmap

### ✅ Completed Phases

- **Phase A** - Deterministic routing and runbook registry
- **Phase B** - Validated VM cluster runbooks
- **Phase C** - Kubernetes and Active-Active preparation runbooks
- **Phase D** - Database deployment runbooks
- **Phase E** - Harness and testing tools
- **Phase F** - Context Pack Builder (RAG integration with orchestration)
- **RAG Pipeline (Phase 3)** - Production-ready RAG with hybrid search

### 🚀 V1 Completion Tasks (In Progress)

**Goal:** Transform from "phases complete" to "v1 production-ready"

- **Phase 1A** - Data-driven routing registry (prevent if/else monster)
- **Phase 1B** - Versioned context pack schema (formal contract)
- **Phase 2A** - Reusable step library (prevent copy-paste hell)
- **Phase 2B** - Golden path CLI (make it usable)
- **Phase 3A** - CI anti-rot guardrails (prevent drift)
- **Phase 3B** - API clarity decision (library/CLI or API)

📄 **See:** `TASKS.md` for detailed task definitions

### 🔮 Future Phases (Post-V1)

- **Agent Layer** - Execution engine for runbooks (external consumer)
- **Advanced Features** - Step versioning, conditional steps, rollback automation

## Contributing

See [AUGGIE.md](AUGGIE.md) for guidelines on working with AI assistance in this repository.

See [CONTEXT.md](CONTEXT.md) for architectural context and constraints.

See [TASKS.md](TASKS.md) for current tasks and development workflow.

## License

TODO: Add license information