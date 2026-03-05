# Next Phase: Deterministic Runbook Layer for Engineering Agent

**Date:** 2026-03-04  
**Purpose:** Design the deterministic layer that sits above the RAG pipeline  
**Status:** Design Phase

---

## 1. Current State Review

### Completed RAG Components

The repository has a **production-ready RAG pipeline** with the following capabilities:

#### A. Ingestion & Chunking
- **Ingest** (`src/redis_agent_control_plane/rag/ingest.py`)
  - Recursive markdown file discovery
  - UTF-8 encoding with error handling
  - Metadata extraction (file_path, title, source_repo)
  
- **Chunker** (`src/redis_agent_control_plane/rag/chunker.py`)
  - Adaptive H2/H3 boundary chunking
  - Code block preservation (never splits)
  - Table and procedural list preservation
  - YAML frontmatter parsing
  - Subchunking for long sections (>2000 chars)
  - **13 metadata fields per chunk:**
    - `source`, `doc_path`, `doc_url`, `title`
    - `category` (operate/integrate/develop)
    - `product_area` (redis_software/redis_cloud/redis_stack/redis_oss)
    - `section_heading`, `toc_path`
    - `chunk_id`, `chunk_index`, `subchunk_index`
    - `content`, `embedding`

#### B. Embedding & Indexing
- **Embedder** (`src/redis_agent_control_plane/rag/embedder.py`)
  - Model: sentence-transformers/all-MiniLM-L6-v2 (384 dims)
  - Local execution (FREE, no API costs)
  - In-memory cache with TTL (600s)
  - Batch processing support
  - 63.8% cache hit rate at scale

- **Indexer** (`src/redis_agent_control_plane/rag/indexer.py`)
  - Redis 8.4+ native vector search (no modules required)
  - FT.CREATE index with HNSW algorithm
  - BM25 text indexing for keyword search
  - 4 TAG fields (source, category, product_area, chunk_id)
  - 6 TEXT fields (doc_path, doc_url, title, section_heading, toc_path, content)
  - 2 NUMERIC fields (chunk_index, subchunk_index)
  - 1 VECTOR field (embedding, FLOAT32, 384 dims, COSINE)

#### C. Retrieval Capabilities
- **Retriever** (`src/redis_agent_control_plane/rag/retriever.py`)
  - **Vector search:** Semantic similarity using HNSW (O(log n))
  - **Hybrid search:** Vector + BM25 with Reciprocal Rank Fusion (RRF)
  - **Filter-first pattern:** Apply metadata filters before vector ranking
  - **Metadata filtering:** product_area, category
  - **Result deduplication:** Top N chunks per document
  - **Configurable weights:** vector_weight (0.7), text_weight (0.3)
  - **Distance threshold:** Default 0.30 (cosine distance)

#### D. Scale & Performance Validation
- **Corpus:** 4,207 documents → 20,249 chunks
- **Processing time:** 237 seconds (~4 minutes)
- **Index size:** ~200-300MB (well under 1GB limit)
- **Query latency:** <100ms (P95) with FT.SEARCH
- **Speedup:** 10-100x faster than brute-force
- **Supported query types:**
  - Semantic: "How do I configure memory limits?"
  - Exact commands: "CONFIG SET maxmemory"
  - Config parameters: "maxmemory-policy allkeys-lru"
  - API methods: "HSET key field value"
  - Hybrid: "eviction policy configuration"

### Existing Metadata for Filtering

The RAG pipeline already extracts and indexes:
- **category:** operate, integrate, develop
- **product_area:** redis_software, redis_cloud, redis_stack, redis_oss
- **doc_path:** Full path for provenance
- **section_heading:** Contextual location within document
- **toc_path:** Breadcrumb trail

These metadata fields provide **bounded context** for deterministic routing.

### What's Missing for an Engineering Agent

The RAG pipeline is a **retrieval subsystem**, not a **deployment orchestrator**.

**Missing capabilities:**
1. **Deterministic routing** - No logic to select which deployment workflow applies
2. **Runbook registry** - No catalog of structured deployment procedures
3. **Execution steps** - No ordered, validated step sequences
4. **Validation hooks** - No pre/post-condition checks
5. **Tool integration** - No hooks for kubectl, terraform, Redis CLI, etc.
6. **Context assembly** - No structured way to package RAG results for agent consumption
7. **Decision logic** - No rules engine for deployment variant selection

---

## 2. Gap Analysis

### Current State: Working Docs RAG Pipeline
- ✅ Can retrieve relevant documentation chunks
- ✅ Can filter by product area and category
- ✅ Can handle semantic and exact match queries
- ✅ Production-ready performance and scale

### Target State: Deterministic Engineering Agent for Redis Deployment
- ❌ Cannot determine which deployment workflow to execute
- ❌ Cannot provide ordered, validated steps
- ❌ Cannot enforce prerequisites or validations
- ❌ Cannot integrate with deployment tools
- ❌ Cannot track execution state or progress
- ❌ Cannot provide deterministic doc references per step

### The Missing Layer: Deterministic Orchestration

**The gap is NOT a RAG problem. The gap is an orchestration problem.**

RAG should be a **supporting subsystem** that:
- Enriches step-specific context
- Provides troubleshooting guidance
- Answers clarifying questions
- Fills knowledge gaps

The deterministic layer should:
- **Route:** DeploymentSpec → runbook_id (rules-based, not embedding-based)
- **Structure:** Provide ordered steps with validations
- **Integrate:** Hook into deployment tools (kubectl, terraform, Redis CLI)
- **Validate:** Check prerequisites and post-conditions
- **Assemble:** Package RAG context for agent consumption

---

## 3. Proposed Deterministic Architecture

### Core Building Blocks

#### A. DeploymentSpec (Input Contract)

A structured input that captures deployment intent.

**Proposed schema (YAML/JSON):**
```yaml
deployment_spec:
  # Product selection
  product: redis_enterprise | redis_cloud | redis_stack
  
  # Platform
  platform: vm | kubernetes | eks | gke | aks | openshift
  
  # Topology
  topology: single_node | clustered | active_active
  
  # Cloud provider (if applicable)
  cloud_provider: aws | gcp | azure | on_prem
  
  # Networking
  networking:
    type: public | private | vpc_peering
    tls_enabled: true | false
    
  # Scale
  scale:
    nodes: 3
    shards: 2
    replicas: 1
    
  # Optional: specific requirements
  requirements:
    - high_availability
    - geo_distribution
    - compliance_fips
```

**Purpose:** Deterministic input that can be validated and routed.

#### B. Runbook Registry (Catalog)

A deterministic catalog of deployment runbooks.

**Proposed structure:**
```
runbooks/
├── redis_enterprise/
│   ├── vm/
│   │   ├── single_node.yaml
│   │   └── clustered.yaml
│   ├── kubernetes/
│   │   ├── single_node.yaml
│   │   ├── clustered.yaml
│   │   └── active_active.yaml
│   └── eks/
│       ├── clustered.yaml
│       └── active_active.yaml
├── redis_cloud/
│   ├── aws/
│   │   ├── basic.yaml
│   │   └── vpc_peering.yaml
│   └── gcp/
│       └── basic.yaml
└── redis_stack/
    └── docker/
        └── single_node.yaml
```

**Runbook naming convention:**
- `runbook.{product}.{platform}.{topology}.yaml`
- Examples:
  - `runbook.re.vm.single`
  - `runbook.re.k8s.clustered`
  - `runbook.re.aa.k8s`
  - `runbook.rc.peering.aws`

#### C. Router (Deterministic Mapping)

A rules-based router that maps DeploymentSpec → runbook_id.

**NOT embedding-based. NOT LLM-based. Deterministic table/rules.**

**Proposed implementation:**
```python
class RunbookRouter:
    """Deterministic router for runbook selection."""

    def route(self, spec: DeploymentSpec) -> str:
        """Route deployment spec to runbook ID.

        Args:
            spec: Deployment specification

        Returns:
            Runbook ID (e.g., "runbook.re.k8s.clustered")
        """
        # Deterministic routing logic
        product = spec.product
        platform = spec.platform
        topology = spec.topology

        # Build runbook ID
        runbook_id = f"runbook.{product}.{platform}.{topology}"

        # Validate runbook exists
        if not self.registry.has_runbook(runbook_id):
            raise RunbookNotFoundError(f"No runbook for: {runbook_id}")

        return runbook_id
```

**Routing table example:**
```yaml
routing_rules:
  - match:
      product: redis_enterprise
      platform: kubernetes
      topology: clustered
    runbook: runbook.re.k8s.clustered

  - match:
      product: redis_enterprise
      platform: eks
      topology: active_active
    runbook: runbook.re.aa.eks

  - match:
      product: redis_cloud
      platform: aws
      networking.type: vpc_peering
    runbook: runbook.rc.peering.aws
```

**Key principle:** Routing is deterministic, not probabilistic.

#### D. Runbook Definition Format

A structured format for runbooks containing ordered steps, validations, and RAG assist queries.

**Proposed schema (YAML):**
```yaml
runbook:
  id: runbook.re.k8s.clustered
  name: "Redis Enterprise on Kubernetes - Clustered"
  description: "Deploy a clustered Redis Enterprise cluster on Kubernetes"
  version: "1.0.0"

  # Prerequisites
  prerequisites:
    - check: kubectl_installed
      command: "kubectl version --client"
      error_message: "kubectl not found. Install kubectl first."

    - check: cluster_access
      command: "kubectl cluster-info"
      error_message: "Cannot access Kubernetes cluster."

    - check: namespace_exists
      command: "kubectl get namespace redis"
      error_message: "Namespace 'redis' does not exist."
      optional: true

  # Ordered execution steps
  steps:
    - id: step_1
      name: "Create namespace"
      description: "Create Kubernetes namespace for Redis Enterprise"

      # Deterministic doc references
      doc_refs:
        - path: "operate/kubernetes/deployment/quick-start.md"
          section: "Create namespace"

      # Optional RAG assist query
      rag_assist:
        query: "How do I create a Kubernetes namespace for Redis Enterprise?"
        filters:
          category: operate
          product_area: redis_software
        max_results: 3

      # Tool execution
      tool: kubectl
      command: "kubectl create namespace redis"

      # Validation
      validation:
        command: "kubectl get namespace redis"
        expect: "Active"

    - id: step_2
      name: "Install Redis Enterprise Operator"
      description: "Deploy the Redis Enterprise Operator using Helm or kubectl"

      doc_refs:
        - path: "operate/kubernetes/deployment/operator.md"
          section: "Install Operator"

      rag_assist:
        query: "How do I install the Redis Enterprise Operator on Kubernetes?"
        filters:
          category: operate
          product_area: redis_software
        max_results: 5

      tool: kubectl
      command: "kubectl apply -f https://raw.githubusercontent.com/RedisLabs/redis-enterprise-k8s-docs/master/bundle.yaml"

      validation:
        command: "kubectl get pods -n redis"
        expect: "Running"
        retry: 10
        retry_delay: 5

    - id: step_3
      name: "Create Redis Enterprise Cluster"
      description: "Deploy the Redis Enterprise Cluster (REC) resource"

      doc_refs:
        - path: "operate/kubernetes/deployment/rec.md"
          section: "Create REC"

      rag_assist:
        query: "How do I create a Redis Enterprise Cluster on Kubernetes?"
        filters:
          category: operate
          product_area: redis_software
        max_results: 5

      tool: kubectl
      command: "kubectl apply -f rec.yaml"

      validation:
        command: "kubectl get rec -n redis"
        expect: "Running"
        retry: 20
        retry_delay: 10

  # Post-deployment validations
  post_validations:
    - check: cluster_ready
      command: "kubectl get rec -n redis -o jsonpath='{.status.state}'"
      expect: "Running"

    - check: pods_running
      command: "kubectl get pods -n redis | grep -c Running"
      expect: "3"  # Expect 3 pods running

  # Rollback steps (optional)
  rollback:
    - command: "kubectl delete rec -n redis --all"
    - command: "kubectl delete namespace redis"
```

**Key features:**
- **Ordered steps:** Sequential execution with dependencies
- **Deterministic doc refs:** Explicit pointers to documentation
- **RAG assist queries:** Bounded RAG enrichment per step
- **Tool hooks:** Integration with kubectl, terraform, etc.
- **Validations:** Pre/post-condition checks
- **Rollback:** Cleanup steps if deployment fails

#### E. Context Pack / Context Surface

A structured format for packaging RAG results for agent consumption.

**Proposed schema:**
```python
@dataclass
class ContextPack:
    """Structured context for agent consumption."""

    # Step context
    step_id: str
    step_name: str
    step_description: str

    # Deterministic references
    doc_refs: list[DocReference]

    # RAG-retrieved context
    rag_results: list[RAGChunk]

    # Metadata
    retrieval_method: str  # "vector" | "hybrid" | "deterministic"
    confidence_score: float

@dataclass
class DocReference:
    """Deterministic document reference."""

    path: str
    section: str
    url: str

@dataclass
class RAGChunk:
    """RAG-retrieved chunk with provenance."""

    content: str
    doc_path: str
    section_heading: str
    toc_path: str
    distance: float
    rank: int
    why_included: str  # "semantic_match" | "keyword_match" | "hybrid"
```

**Purpose:** Provide agent with:
1. **Deterministic references** (always included)
2. **RAG-enriched context** (optional, bounded)
3. **Provenance** (where did this come from?)
4. **Confidence** (how relevant is this?)

---

## 4. Recommended Implementation Phases

### Phase A: Deterministic Routing + Runbook Registry
**Goal:** Build the deterministic foundation

**Deliverables:**
- `src/redis_agent_control_plane/runbooks/` - Runbook registry directory
- `src/redis_agent_control_plane/orchestration/deployment_spec.py` - DeploymentSpec dataclass
- `src/redis_agent_control_plane/orchestration/runbook.py` - Runbook dataclass and loader
- `src/redis_agent_control_plane/orchestration/router.py` - RunbookRouter class
- `tests/test_router.py` - Router unit tests
- 3-5 sample runbooks (YAML)

**Acceptance criteria:**
- DeploymentSpec can be created and validated
- Router can deterministically map spec → runbook_id
- Runbooks can be loaded from YAML
- All routing is table/rules-based (no embeddings)

### Phase B: Runbook Schema + Sample Runbooks
**Goal:** Define and validate runbook format

**Deliverables:**
- `schemas/runbook_schema.yaml` - JSON Schema for runbook validation
- `runbooks/redis_enterprise/kubernetes/clustered.yaml` - Sample runbook
- `runbooks/redis_enterprise/vm/single_node.yaml` - Sample runbook
- `runbooks/redis_cloud/aws/vpc_peering.yaml` - Sample runbook
- `src/redis_agent_control_plane/orchestration/validator.py` - Runbook validator
- `tests/test_runbook_validation.py` - Validation tests

**Acceptance criteria:**
- Runbooks validate against schema
- Sample runbooks cover 3+ deployment variants
- Prerequisites, steps, validations all defined
- Doc refs and RAG assist queries specified

### Phase C: Harness/Tests for Routing and Runbook Validation
**Goal:** Ensure deterministic behavior

**Deliverables:**
- `tests/test_routing_determinism.py` - Determinism tests
- `tests/test_runbook_loader.py` - Loader tests
- `scripts/validate_runbooks.py` - CLI tool to validate all runbooks
- `scripts/test_routing.py` - CLI tool to test routing logic

**Acceptance criteria:**
- Same DeploymentSpec always routes to same runbook
- All runbooks validate successfully
- No probabilistic behavior in routing
- 100% test coverage for router

### Phase D: Context Pack Builder Using Existing Retriever
**Goal:** Integrate RAG as bounded enrichment

**Deliverables:**
- `src/redis_agent_control_plane/orchestration/context_builder.py` - ContextPack builder
- Integration with existing `RedisRetriever`
- `tests/test_context_builder.py` - Context builder tests

**Acceptance criteria:**
- Can build ContextPack from runbook step
- Deterministic doc refs always included
- RAG results bounded by step-specific query
- Provenance tracked for all chunks

### Phase E: Optional Enhancements
**Goal:** Improve RAG quality and evaluation

**Deliverables:**
- Embedding cache improvements (persistent cache)
- Evaluation harness for RAG quality
- Query analytics and feedback loop

**Status:** Deferred until Phases A-D complete

---

## 5. Recommended Branch/Task Strategy

### Branch Strategy
- **Current branch:** `rag-redis-docs-ingestion` (RAG work complete)
- **Recommended:** Create new branch `deterministic-runbook-layer`
- **Rationale:** Keep RAG work separate from orchestration work

### Task IDs
- `[ORCH-001]` Phase A: Deterministic Routing + Runbook Registry
- `[ORCH-002]` Phase B: Runbook Schema + Sample Runbooks
- `[ORCH-003]` Phase C: Harness/Tests for Routing and Validation
- `[ORCH-004]` Phase D: Context Pack Builder
- `[ORCH-005]` Phase E: Optional Enhancements (deferred)

### Blast Radius Control
- **Phase A:** New files only, no changes to RAG pipeline
- **Phase B:** New runbook files only
- **Phase C:** New test files only
- **Phase D:** Integration with existing retriever (minimal changes)

---

## 6. Explicit Guidance on What NOT to Do Yet

### ❌ Do NOT Implement Yet

1. **Agent APIs** - No FastAPI endpoints yet
2. **Full orchestration engine** - No execution engine yet
3. **UI** - No web interface or CLI yet
4. **Broad refactors** - Do not refactor existing RAG pipeline
5. **LLM integration** - No LLM calls yet
6. **Tool execution** - No actual kubectl/terraform execution yet
7. **State management** - No execution state tracking yet
8. **Monitoring** - No metrics or observability yet

### ✅ Focus on Design First

The purpose of Phases A-C is to:
- **Design** the deterministic layer cleanly
- **Validate** the runbook format
- **Test** the routing logic
- **Prove** deterministic behavior

Only after the deterministic layer is solid should we:
- Add execution engine
- Integrate with tools
- Add LLM for natural language interface
- Build APIs

---

## 7. Summary

### Current State
- ✅ Production-ready RAG pipeline (20k+ chunks, <100ms latency)
- ✅ Hybrid search (vector + BM25)
- ✅ Metadata filtering (category, product_area)
- ✅ Validated at scale (4,207 docs)

### Missing Layer
- ❌ Deterministic routing (spec → runbook)
- ❌ Runbook registry (structured workflows)
- ❌ Execution steps (ordered, validated)
- ❌ Context assembly (RAG as bounded enrichment)

### Proposed Solution
- **DeploymentSpec:** Structured input contract
- **RunbookRouter:** Deterministic routing (rules-based)
- **Runbook Registry:** Catalog of YAML runbooks
- **Runbook Format:** Steps + validations + doc refs + RAG assist
- **ContextPack:** Structured context for agent consumption

### Implementation Phases
- **Phase A:** Routing + Registry (foundation)
- **Phase B:** Schema + Sample Runbooks (validation)
- **Phase C:** Tests + Harness (determinism)
- **Phase D:** Context Builder (RAG integration)
- **Phase E:** Optional Enhancements (deferred)

### Key Principle
**RAG is a supporting subsystem, not the primary planner.**

Deterministic routing + structured runbooks + validations
**with** RAG used as bounded context enrichment

**NOT** free-form RAG retrieval deciding the deployment plan by itself.

---

**Next Action:** Review this design and approve Phases A-D for implementation.


