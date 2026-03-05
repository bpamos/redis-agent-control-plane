# ContextPack Schema Documentation

**Version:** 1.0.0
**Last Updated:** 2026-03-05

## Overview

The `ContextPack` is the primary output artifact of the Redis Agent Control Plane. It combines:
- **Deterministic doc refs** (always included, from runbook YAML)
- **RAG-retrieved chunks** (bounded results, optional)
- **Full provenance** (where did this data come from?)

This document defines the schema, versioning rules, and validation requirements for `ContextPack` JSON output.

---

## Schema Version

The `ContextPack` schema is versioned using semantic versioning (semver):

```
plan_version: "1.0.0"  # ContextPack schema version
spec_version: "1.0.0"  # DeploymentSpec schema version
```

### Version Compatibility Rules

- **Major version change (e.g., 1.0.0 → 2.0.0):** Breaking changes, consumers must update
- **Minor version change (e.g., 1.0.0 → 1.1.0):** New fields added, backward compatible
- **Patch version change (e.g., 1.0.0 → 1.0.1):** Bug fixes, fully compatible

Consumers should:
1. Check `plan_version` before parsing
2. Reject major version mismatches
3. Accept minor/patch version differences

---

## Schema Definition

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `runbook_id` | string | ✅ | Runbook identifier (e.g., `runbook.redis_enterprise.kubernetes.clustered`) |
| `runbook_version` | string | ✅ | Runbook version (semver) |
| `deployment_spec` | object | ✅ | Deployment specification (see below) |
| `step_id` | string | ✅ | Step identifier within the runbook |
| `step_name` | string | ✅ | Human-readable step name |
| `step_description` | string | ✅ | Step description |
| `deterministic_doc_refs` | array | ✅ | Deterministic document references |
| `rag_chunks` | array | ✅ | RAG-retrieved chunks (may be empty) |
| `docs_commit_sha` | string | ❌ | Git commit SHA of docs corpus |
| `index_name` | string | ✅ | Redis index name (default: `redis_docs`) |
| `chunk_ids` | array | ✅ | List of chunk IDs included |
| `retrieval_timestamp` | string | ✅ | ISO 8601 timestamp of retrieval |
| `retrieval_method` | string | ✅ | `vector`, `hybrid`, or `deterministic_only` |
| `plan_version` | string | ✅ | ContextPack schema version (semver) |
| `spec_version` | string | ✅ | DeploymentSpec schema version (semver) |

---

### DeploymentSpec Schema

The `deployment_spec` object captures deployment intent:

```json
{
  "product": "redis_enterprise",
  "platform": "kubernetes",
  "topology": "clustered",
  "networking": {
    "type": "private",
    "tls_enabled": true
  },
  "scale": {
    "nodes": 3,
    "shards": 2,
    "replicas": 1
  },
  "cloud_provider": null,
  "requirements": []
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product` | string | ✅ | `redis_enterprise`, `redis_cloud`, or `redis_stack` |
| `platform` | string | ✅ | `vm`, `kubernetes`, `eks`, `gke`, `aks`, `openshift`, `aws`, `gcp`, `azure` |
| `topology` | string | ✅ | `single_node`, `clustered`, `active_active`, `vpc_peering` |
| `networking` | object | ✅ | Networking configuration |
| `scale` | object | ✅ | Scale configuration |
| `cloud_provider` | string | ❌ | `aws`, `gcp`, `azure`, `on_prem` |
| `requirements` | array | ❌ | Additional requirements |

---

### DocReference Schema

Each deterministic doc reference has:

```json
{
  "path": "docs/operate/kubernetes/deployment/quick-start.md",
  "section": "Install the operator"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | ✅ | Relative path to documentation file |
| `section` | string | ✅ | Section heading within the document |

---

### RAGChunk Schema

Each RAG chunk has full provenance:

```json
{
  "content": "To install the Redis Enterprise Operator...",
  "doc_path": "docs/operate/kubernetes/deployment/quick-start.md",
  "doc_url": "https://redis.io/docs/operate/kubernetes/deployment/quick-start/",
  "title": "Quick Start Guide",
  "section_heading": "Install the operator",
  "toc_path": "Operate > Kubernetes > Deployment > Quick Start",
  "category": "operate",
  "product_area": "redis_software",
  "chunk_id": "redis_docs:chunk:1",
  "chunk_index": 0,
  "vector_distance": 0.15,
  "rank": 1,
  "why_included": "semantic_match"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | string | ✅ | Chunk content (markdown) |
| `doc_path` | string | ✅ | Relative path to source document |
| `doc_url` | string | ❌ | Public URL to documentation |
| `title` | string | ❌ | Document title |
| `section_heading` | string | ❌ | Section heading |
| `toc_path` | string | ❌ | Table of contents path |
| `category` | string | ✅ | `operate`, `integrate`, or `develop` |
| `product_area` | string | ✅ | `redis_software`, `redis_cloud`, or `redis_stack` |
| `chunk_id` | string | ✅ | Unique chunk identifier |
| `chunk_index` | int | ❌ | Index within document |
| `vector_distance` | float | ❌ | Vector similarity distance |
| `rank` | int | ❌ | Position in results (1-based) |
| `why_included` | string | ❌ | `semantic_match`, `keyword_match`, or `hybrid` |

---

## Validation

Use `scripts/validate_plan.py` to validate context pack JSON:

```bash
python scripts/validate_plan.py context_pack.json
```

The validator checks:
1. ✅ Valid JSON structure
2. ✅ All required fields present
3. ✅ Valid schema versions (semver format)
4. ✅ Properly formatted doc_refs
5. ✅ RAG chunks have full provenance
6. ✅ Can deserialize using `ContextPack.from_dict()`

Exit codes:
- `0`: Valid context pack
- `1`: Invalid context pack (errors printed to stderr)

---

## Complete Example

Here's a complete example of a valid `ContextPack` JSON:

```json
{
  "runbook_id": "runbook.redis_enterprise.kubernetes.clustered",
  "runbook_version": "2.0.0",
  "deployment_spec": {
    "product": "redis_enterprise",
    "platform": "kubernetes",
    "topology": "clustered",
    "networking": {
      "type": "private",
      "tls_enabled": true
    },
    "scale": {
      "nodes": 3,
      "shards": 2,
      "replicas": 1
    },
    "cloud_provider": null,
    "requirements": []
  },
  "step_id": "step_1",
  "step_name": "Install Redis Enterprise Operator",
  "step_description": "Install the Redis Enterprise Operator using kubectl",
  "deterministic_doc_refs": [
    {
      "path": "docs/operate/kubernetes/deployment/quick-start.md",
      "section": "Install the operator"
    }
  ],
  "rag_chunks": [
    {
      "content": "To install the Redis Enterprise Operator...",
      "doc_path": "docs/operate/kubernetes/deployment/quick-start.md",
      "doc_url": "https://redis.io/docs/operate/kubernetes/deployment/quick-start/",
      "title": "Quick Start Guide",
      "section_heading": "Install the operator",
      "toc_path": "Operate > Kubernetes > Deployment > Quick Start",
      "category": "operate",
      "product_area": "redis_software",
      "chunk_id": "redis_docs:chunk:1",
      "chunk_index": 0,
      "vector_distance": 0.15,
      "rank": 1,
      "why_included": "semantic_match"
    }
  ],
  "docs_commit_sha": "abc123def456",
  "index_name": "redis_docs",
  "chunk_ids": ["redis_docs:chunk:1"],
  "retrieval_timestamp": "2026-03-05T10:30:00Z",
  "retrieval_method": "hybrid",
  "plan_version": "1.0.0",
  "spec_version": "1.0.0"
}
```

---

## Usage in Python

### Serialization

```python
from redis_agent_control_plane.orchestration.context_pack import ContextPack

# Create a ContextPack instance
context_pack = ContextPack(...)

# Convert to dictionary
data = context_pack.to_dict()

# Convert to JSON string
json_str = context_pack.to_json(indent=2)

# Save to file
with open("context_pack.json", "w") as f:
    f.write(json_str)
```

### Deserialization

```python
import json
from redis_agent_control_plane.orchestration.context_pack import ContextPack

# Load from file
with open("context_pack.json") as f:
    data = json.load(f)

# Create ContextPack from dictionary
context_pack = ContextPack.from_dict(data)

# Or directly from JSON string
context_pack = ContextPack.from_json(json_str)
```

---

## Migration Guide

### Future Schema Changes

When the schema evolves:

1. **Adding optional fields (minor version bump):**
   - Old consumers can ignore new fields
   - New consumers should handle missing fields gracefully

2. **Changing field types (major version bump):**
   - Requires migration script
   - Old consumers must reject new version

3. **Removing fields (major version bump):**
   - Requires migration script
   - Old consumers must reject new version

### Example: Migrating from 1.0.0 to 2.0.0

```python
def migrate_1_to_2(old_data: dict) -> dict:
    """Migrate ContextPack from v1.0.0 to v2.0.0."""
    new_data = old_data.copy()

    # Example: Rename field
    if "old_field" in new_data:
        new_data["new_field"] = new_data.pop("old_field")

    # Update version
    new_data["plan_version"] = "2.0.0"

    return new_data
```

---

## See Also

- [RAG Pipeline Documentation](RAG_PIPELINE.md)
- [Runbook Registry](../runbooks/_registry.yaml)
- [Validation Script](../scripts/validate_plan.py)

