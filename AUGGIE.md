# AUGGIE.md

## Purpose
- This file defines how Auggie (AI assistant) should operate when working in this repository
- Ensures consistent, safe, and predictable development workflow
- Minimizes risk while maximizing productivity through clear boundaries and checklists
- Works in conjunction with TASKS.md (task definitions) and CONTEXT.md (architecture context)

## ⚠️ CRITICAL: Git Commit Policy

**DO NOT commit code to git without explicit approval from Brandon.**

See `AI_COMMIT_POLICY.md` for full details.

**Before running `git commit`, `git push`, or any destructive git command:**
1. **STOP**
2. **ASK**: "Should I commit/push these changes?"
3. **WAIT** for explicit approval
4. **ONLY THEN** proceed

## 🔒 CRITICAL: Security and Sensitive Information

**NEVER include sensitive information in code, documentation, or any tracked files.**

See `SECURITY.md` for full security guidelines.

**Protected Information:**
- ❌ Passwords, API keys, tokens, secrets
- ❌ Database credentials (usernames, passwords, connection strings)
- ❌ Redis Cloud URIs with credentials (host, port, password)
- ❌ Private endpoints or internal URLs
- ❌ Any real credentials or production configuration

**Safe Practices:**
- ✅ Use environment variables (`.env` file, gitignored)
- ✅ Use placeholders in examples (`YOUR_PASSWORD`, `YOUR_HOST`)
- ✅ Use localhost for development examples
- ✅ Redact real endpoints in documentation (`[REDACTED]`)
- ✅ Provide `.env.example` templates with safe placeholders

**Before creating or modifying files:**
1. **CHECK**: Does this file contain or reference credentials?
2. **VERIFY**: Are all credentials loaded from environment variables?
3. **CONFIRM**: Are examples using placeholders or localhost?
4. **ENSURE**: Real credentials are only in `.env` (gitignored)

## Operating Principles

**Low blast radius:**
- Make the smallest change that works
- Touch as few files as possible
- Prefer editing existing files over creating new ones

**Plan-first:**
- Propose a brief plan before coding when task isn't trivial
- Get confirmation on approach for non-obvious changes

**No drive-by refactors:**
- Don't refactor code unrelated to the current task
- Don't fix formatting/style issues outside the scope
- Don't "improve" working code unless explicitly asked

**Respect constraints:**
- Always check TASKS.md for active tasks and scope boundaries
- Always check CONTEXT.md before starting work
- Honor architectural decisions and conventions
- Stay within defined non-goals

**When blocked:**
- Output "BLOCKED: <what's needed>" and ask for clarification
- Do not guess at requirements, APIs, or infrastructure details
- Do not invent product features or capabilities

## Standard Workflow

1. **Restate the task** - Confirm understanding and define success criteria
2. **Identify files** - List files likely to touch and explain why each is needed
3. **Implement** - Make minimal changes to achieve the goal
4. **Verify** - Add/update tests OR provide a deterministic smoke-check command
5. **Run checks** - Execute lint/type/tests if available in the project
6. **Summarize** - Report what changed, commands run, files touched, risks, next steps

## Definition of Done

Before marking any task complete, verify:

- [ ] Code builds/runs without errors
- [ ] Tests pass (existing + new if applicable)
- [ ] No new lint or type errors introduced
- [ ] No unrelated formatting or style churn
- [ ] Documentation updated if public APIs changed
- [ ] CONTEXT.md updated if architecture changed
- [ ] No TODOs or placeholder code left behind (unless explicitly agreed)
- [ ] Changes align with constraints in CONTEXT.md
- [ ] **SECURITY**: No credentials or sensitive data in tracked files
- [ ] **SECURITY**: All credentials loaded from environment variables
- [ ] **SECURITY**: Examples use placeholders or localhost only
- [ ] **SECURITY**: `.env` file not modified or committed

## Change Boundaries

**DO NOT change the following unless the task explicitly requests it:**
- Infrastructure configuration (Docker, K8s, cloud resources)
- Dependencies (package.json, requirements.txt, go.mod, etc.) - use package managers if needed
- Global configuration files (tsconfig, eslint, pytest.ini, etc.)
- CI/CD pipelines or GitHub Actions
- Database schemas or migrations (without explicit approval)
- Authentication or security-related code
- `.env` file (contains credentials - never commit)
- `.gitignore` (unless adding new sensitive files to ignore)

**DO NOT include in any files:**
- Real passwords, API keys, or credentials
- Production database connection strings
- Redis Cloud URIs with credentials
- Private endpoints or internal URLs

**When in doubt:** Ask before modifying.

## Branching & Commits

**Branching:**
- Default: one feature branch per task (e.g., `feature/add-rag-endpoint`)
- Branch from `main` unless user specifies otherwise
- If multiple parallel tasks/agents: separate branches required

**Commits:**
- Make atomic commits (one logical change per commit)
- Use conventional commit format:
  ```
  <type>(<scope>): <description>
  
  [optional body]
  ```
  Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`
  
**Example:**
```
feat(rag): add vector similarity search endpoint

- Implement /api/search endpoint
- Add Redis vector store integration
- Include basic error handling
```

## Output Format

Use this template for all non-trivial responses:

```
### Plan
- What I'm going to do
- Why this approach
- Files I'll touch

### Changes
- Brief description of each change made
- Key decisions or tradeoffs

### Commands Run
- `command 1` - what it does
- `command 2` - what it does

### Files Touched
- path/to/file1.py - what changed
- path/to/file2.py - what changed

### Notes/Risks
- Any gotchas or things to watch
- Known limitations of the implementation

### Next Step
- What should happen next (or "Ready for review")
```

## Quick Start Prompts

**Small bugfix:**
```
Fix the bug where [specific behavior] happens when [condition].
Expected: [correct behavior]
Files likely involved: [file1, file2]
```

**Feature addition:**
```
Add [feature name] that does [specific thing].
Acceptance criteria:
- [ ] criterion 1
- [ ] criterion 2
Constraints: [any specific requirements]
```

**Bounded refactor:**
```
Refactor [specific component/function] to [improvement].
Scope: ONLY touch [specific files/modules]
Do NOT change: [things to leave alone]
Success: [how to verify it works]
```

## Tips for Effective Collaboration

- **Be specific:** "Add error handling to the Redis connection" beats "improve the code"
- **Provide context:** Link to relevant docs, error messages, or examples
- **Set boundaries:** Explicitly state what should NOT change
- **Verify incrementally:** Ask Auggie to run tests after each logical step
- **Review diffs:** Check the changes before committing

## Emergency Stops

If Auggie is:
- Making changes outside the stated scope
- Creating unnecessary files
- Refactoring unrelated code
- Guessing at requirements

**Say:** "STOP - revert changes and let's clarify the scope"

---

# Branch Task: deterministic-runbook-layer

## Current Phase: [ORCH-003] Kubernetes Cluster & Active-Active Preparation

**Phase A (Deterministic Routing + Runbook Registry) - ✅ COMPLETE (2026-03-05)**
- **Task**: [ORCH-001] Phase A: Deterministic Routing + Runbook Registry
- **Status**: ✅ ALL OBJECTIVES MET - FOUNDATION COMPLETE

**What Was Built:**
- ✅ DeploymentSpec dataclass with validation (141 lines)
- ✅ Runbook dataclass with YAML loader (175 lines)
- ✅ RunbookRouter with deterministic routing (159 lines)
- ✅ 5 sample runbook YAMLs (structural examples only)
- ✅ Unit tests: 11 new tests, all passing
- ✅ 100% deterministic routing validated (100 iterations)

**Phase B (Validated Runbooks - VM Deployments) - ✅ COMPLETE (2026-03-05)**
- **Task**: [ORCH-002] Validated Runbooks for Redis Enterprise
- **Status**: ✅ ALL OBJECTIVES MET - PRODUCTION READY

**What Was Built:**
- ✅ Single-node VM runbook (v2.0.0, 5 doc_refs validated)
- ✅ 3-node VM cluster runbook (v2.0.0, 7 doc_refs validated)
- ✅ Validation script (`scripts/validate_runbooks.py`)
- ✅ Documentation research and validation methodology
- ✅ All commands extracted from Redis Software 8.0.x documentation

**Key Achievements:**
- 🎯 **100% documentation-based** - All commands from actual Redis docs
- ✅ **All doc_refs validated** - 12 total doc_refs, all point to real files
- ✅ **Version-specific** - Target Redis Software 8.0.x explicitly
- ✅ **Production ready** - Runbooks ready for real deployments

## Current Status: All Orchestration Phases Complete! ✅

**Phase C (Kubernetes Cluster & Active-Active Preparation) - ✅ COMPLETE (2026-03-05)**
- **Task**: [ORCH-003] Phase C: Kubernetes Cluster & Active-Active Preparation
- **Status**: ✅ ALL OBJECTIVES MET

**What Was Built:**
- ✅ Kubernetes 3-node cluster runbook (v2.0.0, 6 steps)
- ✅ VM Active-Active preparation runbook (v2.0.0, 9 steps)
- ✅ Kubernetes Active-Active preparation runbook (v2.0.0, 9 steps)
- ✅ Updated validation script for Kubernetes runbooks
- ✅ All doc_refs validated, all commands from actual documentation

**Phase D (Database Deployment Runbooks) - ✅ COMPLETE (2026-03-05)**
- **Task**: [ORCH-004] Phase D: Database Deployment Runbooks
- **Status**: ✅ ALL OBJECTIVES MET

**What Was Built:**
- ✅ VM standard database runbook (v2.0.0, 4 steps)
- ✅ VM CRDB (Active-Active) runbook (v2.0.0, 5 steps)
- ✅ Kubernetes REDB runbook (v2.0.0, 4 steps)
- ✅ Kubernetes REAADB (Active-Active) runbook (v2.0.0, 6 steps)
- ✅ Updated validation script for database runbooks
- ✅ All doc_refs validated, all commands from actual documentation

**Phase E (Harness/Tests for Routing and Validation) - ✅ COMPLETE (2026-03-05)**
- **Task**: [ORCH-005] Phase E: Harness/Tests for Routing and Validation
- **Status**: ✅ ALL OBJECTIVES MET

**What Was Built:**
- ✅ Interactive routing test CLI (`scripts/test_routing.py`)
- ✅ 100% deterministic routing validated (100 iterations)
- ✅ All 10 runbooks pass validation
- ✅ 53 tests pass, 11 skipped
- ✅ Complete harness framework operational

---

## Complete Runbook Inventory (10 Total) ✅

**Infrastructure (1):**
1. ✅ `redis_cloud/aws/vpc_peering.yaml` - Redis Cloud VPC peering on AWS

**Cluster Deployments (3):**
2. ✅ `vm/single_node.yaml` - Single-node VM (dev/test)
3. ✅ `vm/clustered_3node.yaml` - 3-node VM cluster (reusable for multi-region)
4. ✅ `kubernetes/clustered.yaml` - 3-node K8s cluster (reusable for multi-region)

**Active-Active Preparation (2):**
5. ✅ `vm/active_active_prepare.yaml` - Configure 2 VM clusters for Active-Active
6. ✅ `kubernetes/active_active.yaml` - Configure 2 K8s clusters for Active-Active

**Database Deployments (4):**
7. ✅ `database/vm_standard.yaml` - Standard VM database (simple + HA)
8. ✅ `database/vm_crdb.yaml` - Active-Active CRDB (requires #5)
9. ✅ `database/kubernetes_redb.yaml` - Standard K8s database
10. ✅ `database/kubernetes_reaadb.yaml` - Active-Active K8s database (requires #6)

**Status:** 10/10 complete (100%) 🎉

---

## Next Phase: [ORCH-006] Context Pack Builder (Deferred)

**Objective:** Integrate RAG as bounded enrichment using existing RedisRetriever.

**Status:** Deferred - Low priority

**Note:** All high-priority orchestration phases (A-E) are complete. The deterministic runbook layer is production-ready with 10 validated runbooks covering the full deployment lifecycle.

---

# Previous Work: RAG Pipeline (COMPLETE ✅)

**Phase 1-3 (RAG Pipeline) - ✅ COMPLETE (2026-03-04)**
- ✅ Production-ready RAG pipeline with 20,249 chunks indexed
- ✅ Hybrid search (vector + BM25) with FT.CREATE index
- ✅ 4,207 documents processed from Redis docs corpus
- ✅ <100ms query latency with HNSW algorithm
- ✅ All quality checks pass, fully tested

**Test the RAG Pipeline:**
```bash
# Query for Redis Enterprise installation docs
PYTHONPATH=src venv/bin/python -c "
from redis_agent_control_plane.rag.retriever import RedisRetriever
retriever = RedisRetriever()
results = retriever.search(
    query='How do I install Redis Enterprise on a Linux VM?',
    product_area='redis_software',
    category='operate',
    top_k=10
)
for r in results:
    print(f'{r[\"doc_path\"]}: {r[\"section_heading\"]}')
"
```

---

# Branch Task: rag-redis-docs-pipeline (Phase 1) - COMPLETE ✅

## Objective
On the `rag-redis-docs-pipeline` branch, complete **Phase 1** of the Redis Docs RAG work:
- Update planning docs (TASKS.md, CONTEXT.md)
- Create a `notes/` folder (if missing)
- Analyze reference repos and the local `docs/` corpus structure
- Produce a single findings document: `notes/rag_reference_findings.md`

**Important:** Phase 1 is analysis/design only. Do NOT implement new RAG code yet.

## Inputs (local repos under sibling `../` relative to this repo root)
Reference sources to analyze:

1) Notebooks:
- `../redis-ai-resources/python-recipes/RAG/04_advanced_redisvl.ipynb`
- `../redis-ai-resources/python-recipes/vector-search/02_hybrid_search.ipynb`

2) Repos:
- `../redis-rag-workbench/`
  - Ignore UI components; extract ingestion + chunking + retrieval patterns that are useful for our pipeline
- `../redis-slack-worker-agent/`
  - Focus on indexing/retrieval/chunking patterns; note embedding cache approach for later phases
- `../docs/` (Redis docs corpus we will vectorize)
  - Inspect `content/**`
  - Inspect `for-ais-only/**` (this is critical for chunking/metadata rules)

### Must-read docs corpus structure files
- `../docs/for-ais-only/REPOSITORY_MAP_FOR_AI_AGENTS.md`
- `../docs/for-ais-only/metadata_docs/PAGE_METADATA_FORMAT.md`
- `../docs/for-ais-only/render_hook_docs/README.md`

## Step 1 — Create required folders
Ensure this exists (create if missing):
- `notes/`

Do not modify `.gitignore`.

## Step 2 — Update TASKS.md
Append a new Epic section:

### EPIC: Redis Docs RAG Pipeline (Vectors stored in Redis)
Goal: Build a robust RAG pipeline to ingest Redis documentation, chunk it intelligently, embed chunks, store vectors + metadata in Redis, and support high-precision retrieval (including metadata filtering and hybrid search) for an engineering deployment agent.

Add phased tasks:
- Phase 1: analysis + design (this task)
- Phase 2: implement baseline pipeline in `src/redis_agent_control_plane/rag/`
- Phase 3: specialize chunking/filters for `../docs/` and add hybrid search

Phase 1 must include:
- the reference sources list above
- the required deliverable `notes/rag_reference_findings.md`
- definition of done (per-repo analysis + proposed schema + chunking plan + retrieval plan)

## Step 3 — Update CONTEXT.md
Append a section describing RAG scope/constraints:

- We are building a Redis-backed RAG pipeline to support an "engineering-agent" that deploys Redis across multiple variants (VM, Kubernetes/EKS, Redis Cloud, Active-Active).
- Vectors will be stored in Redis.
- Design priorities:
  1) Precision over recall
  2) Filter-first retrieval (metadata filters before vector ranking)
  3) Structure-aware chunking (H2/H3, preserve code blocks and procedural lists)
  4) Provenance on every chunk (doc path/url, title, section heading, breadcrumb, ordering)

Corpus focus:
- Start with `../docs/content/operate/**`
- Expand later to integrate/develop as needed

Search capabilities:
- Vector semantic search
- Hybrid search (vector + keyword) for exact command/config lookups
- Metadata filtering

## Step 4 — Produce Phase 1 deliverable
Create:

- `notes/rag_reference_findings.md`

It must contain:

### A) Per-repo analysis (for each input repo/notebook)
For each source:
- What to reuse (specific files/modules/functions/classes/patterns)
- What to ignore (UI, slack wrappers, etc.)
- Key takeaways relevant to: ingestion, chunking, embedding, indexing, retrieval, hybrid search

### B) Recommended pipeline architecture
A consolidated "recommended pipeline" section:
ingest → normalize → chunk → embed → index → retrieve

### C) Proposed Redis index schema
A concrete proposal for:
- vector field config
- TAG/TEXT/NUMERIC fields

Include recommended metadata fields such as:
- `source` (redis_docs)
- `doc_path` (and/or `doc_url`)
- `title`
- `category` (operate/integrate/develop)
- `product_area` (vm/kubernetes/cloud/active-active)
- `section_heading`
- `toc_path` / breadcrumb
- `chunk_id`
- `chunk_index` / `subchunk_index`
- `content`
- `embedding`

### D) Redis docs chunking strategy (docs-specific)
Define the chunking rules tailored to `../docs/`:
- chunk by H2/H3 boundaries
- preserve code blocks
- preserve procedural lists/checklists
- when to split very long sections and how to order subchunks
- how to compute/assign `category` and `product_area` filters based on repo structure and metadata docs

### E) Retrieval strategy
Describe:
- filter-first retrieval pattern
- when to use vector search vs hybrid search
- recommended default `top_k`, dedupe, and optional rerank hooks

### F) Risks / pitfalls / quality gates
List common failures and how we detect them:
- splitting code blocks
- losing hierarchy
- mixing Cloud and Enterprise guidance
- overly generic chunks
- weak filters leading to wrong retrieval

## Constraints (Phase 1)
- Do NOT implement new RAG code in `src/redis_agent_control_plane/rag/` yet.
- Do NOT refactor unrelated code.
- Keep changes minimal (low blast radius).
- Follow the repository's standard workflow and output format for non-trivial work.

