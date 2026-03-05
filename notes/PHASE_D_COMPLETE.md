# Phase D Complete: Database Deployment Runbooks

**Date:** 2026-03-05  
**Status:** ✅ COMPLETE

---

## Deliverables

- ✅ `runbooks/redis_enterprise/database/vm_standard.yaml` (v2.0.0, 4 steps)
- ✅ `runbooks/redis_enterprise/database/vm_crdb.yaml` (v2.0.0, 5 steps)
- ✅ `runbooks/redis_enterprise/database/kubernetes_redb.yaml` (v2.0.0, 4 steps)
- ✅ `runbooks/redis_enterprise/database/kubernetes_reaadb.yaml` (v2.0.0, 6 steps)
- ✅ Updated `scripts/validate_runbooks.py` to validate database runbooks

## Validation Results

- 10/10 runbooks passed validation (4 new + 6 existing)
- All doc_refs validated
- All commands extracted from Redis Enterprise 8.0.x documentation

## Database Specifications (All Runbooks)

- **Memory:** 1GB
- **Shards:** 1 master shard
- **Replication:** Enabled (except single-node VM)
- **HA:** Enabled where supported (3+ node clusters)
- **Active-Active:** Joined across participating clusters (CRDB/REAADB only)

## Runbook Details

### 1. VM Standard Database (`database/vm_standard.yaml`)
- Covers both simple (single-node) and HA (3-node cluster) variants
- Simple: HA disabled, no replication (single node limitation)
- HA: HA enabled, replication enabled
- 1GB memory, 1 master shard

### 2. VM CRDB - Active-Active (`database/vm_crdb.yaml`)
- Active-Active CRDB database
- Joined across participating clusters (dual region)
- 1GB memory per instance, 1 master shard, replication enabled
- Requires: `vm/active_active_prepare.yaml` completed

### 3. Kubernetes REDB (`database/kubernetes_redb.yaml`)
- REDB (Redis Enterprise Database) resource
- HA enabled, replication enabled
- 1GB memory, 1 master shard

### 4. Kubernetes REAADB - Active-Active (`database/kubernetes_reaadb.yaml`)
- REAADB (Redis Enterprise Active-Active Database) resource
- Joined across participating clusters (dual region)
- 1GB memory per instance, 1 master shard, replication enabled
- Requires: `kubernetes/active_active_prepare.yaml` completed

## Architecture Notes

**Database runbooks are separate from cluster runbooks:**
- Cluster runbooks deploy the Redis Enterprise infrastructure
- Database runbooks deploy databases on existing clusters
- This separation matches operational reality (platform team vs database team)

**Active-Active databases require preparation:**
- CRDB runbook requires `vm/active_active_prepare.yaml` completed first
- REAADB runbook requires `kubernetes/active_active_prepare.yaml` completed first

## Documentation Sources Researched

- `operate/rs/databases/create/` - Database creation
- `operate/rs/databases/active-active/create/` - CRDB creation
- `operate/kubernetes/re-databases/` - Kubernetes REDB
- `operate/kubernetes/active-active/` - Kubernetes REAADB

## Next Steps

✅ Phase D complete → Move to Phase E (Harness/Tests for Routing and Validation)

