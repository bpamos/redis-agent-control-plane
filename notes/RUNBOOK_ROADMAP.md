# Redis Enterprise Runbook Roadmap

**Date:** 2026-03-05
**Updated:** 2026-03-05
**Purpose:** Comprehensive roadmap for validated Redis Enterprise runbooks
**Status:** Phase B Complete, Phase C & D Planned

---

## Overview

This document outlines the complete roadmap for creating validated, production-ready runbooks for Redis Enterprise deployments. Each runbook serves as the authoritative design specification for Terraform/IaC implementations.

**Total Runbooks: 9** (2 complete, 7 planned)

---

## Phase A: Foundation ✅ COMPLETE

**Task:** [ORCH-001] Deterministic Routing + Runbook Registry  
**Status:** ✅ COMPLETE (2026-03-05)

**Deliverables:**
- ✅ DeploymentSpec dataclass with validation
- ✅ Runbook dataclass with YAML loader
- ✅ RunbookRouter with deterministic routing
- ✅ 100% deterministic routing validated

---

## Phase B: VM Deployments ✅ COMPLETE

**Task:** [ORCH-002] Validated Runbooks for Redis Enterprise  
**Status:** ✅ COMPLETE (2026-03-05)

**Deliverables:**
- ✅ `runbooks/redis_enterprise/vm/single_node.yaml` (v2.0.0)
- ✅ `runbooks/redis_enterprise/vm/clustered_3node.yaml` (v2.0.0)
- ✅ `scripts/validate_runbooks.py` (validation script)
- ✅ Documentation research and validation methodology

**Validation Results:**
- 2/2 runbooks passed validation
- 12 total doc_refs validated
- All commands from Redis Software 8.0.x documentation

---

## Phase C: Kubernetes Cluster & Active-Active Preparation 🚧 TODO

**Task:** [ORCH-003] Kubernetes Cluster & Active-Active Preparation
**Status:** TODO
**Priority:** HIGH

### Architecture Note

**Cluster deployment is reusable:**
- For dual-region Active-Active, deploy `clustered_3node.yaml` twice (once per region)
- The "Active-Active" configuration happens in TWO places:
  1. **Preparation runbooks** (cluster linking, networking, credentials) ← Phase C
  2. **Database runbooks** (CRDB/REAADB creation) ← Phase D

**Infrastructure vs Redis Enterprise:**
- These runbooks cover ONLY Redis Enterprise configuration
- Infrastructure (VPC, peering, security groups, K8s clusters) is handled in Terraform
- Preparation runbooks assume infrastructure exists and document prerequisites

### Runbooks to Create

#### 1. Kubernetes 3-Node Cluster
**File:** `runbooks/redis_enterprise/kubernetes/clustered_3node.yaml`

**Scope:**
- Redis Enterprise Operator installation
- 3-node REC (Redis Enterprise Cluster) deployment
- Single Kubernetes cluster
- Reusable for multi-region (deploy twice)
- Assumes: K8s cluster already exists (created in Terraform)

**Documentation Sources:**
- `operate/kubernetes/deployment/`
- `operate/kubernetes/rec/`

#### 2. VM Active-Active Preparation
**File:** `runbooks/redis_enterprise/vm/active_active_prepare.yaml`

**Scope:**
- Configure Redis Enterprise clusters to be aware of each other
- Exchange cluster credentials/certificates
- Set up cluster FQDNs in Redis Enterprise
- Use rladmin/REST API to link clusters
- Assumes: VPC peering, security groups, DNS already configured in Terraform

**Prerequisites:**
- 2 VM clusters deployed (using `clustered_3node.yaml` twice)
- VPC peering configured (Terraform)
- Security groups allow Redis ports (Terraform)
- DNS/Route53 configured (Terraform)

**Documentation Sources:**
- `operate/rs/clusters/active-active/`
- `operate/rs/databases/active-active/create/` (for context)

#### 3. Kubernetes Active-Active Preparation
**File:** `runbooks/redis_enterprise/kubernetes/active_active_prepare.yaml`

**Scope:**
- Install admission controller on both clusters
- Exchange secrets between clusters
- Configure REAADB prerequisites
- Set up participating cluster configuration
- Assumes: Cross-cluster networking, K8s clusters already configured in Terraform

**Prerequisites:**
- 2 K8s clusters with Redis Enterprise Operator deployed
- Cross-cluster networking configured (Terraform)
- Network policies allow Redis ports (Terraform)

**Documentation Sources:**
- `operate/kubernetes/active-active/`
- `operate/kubernetes/reaadb/` (for context)

---

## Phase D: Database Deployments 🚧 TODO

**Task:** [ORCH-004] Database Deployment Runbooks
**Status:** TODO
**Priority:** HIGH

### Architecture Note

**Database runbooks are separate from cluster runbooks:**
- Cluster runbooks deploy the Redis Enterprise infrastructure
- Database runbooks deploy databases on existing clusters
- This separation matches operational reality (platform team vs database team)

**Active-Active databases require preparation:**
- CRDB runbook requires `vm/active_active_prepare.yaml` completed first
- REAADB runbook requires `kubernetes/active_active_prepare.yaml` completed first

### Database Specifications (All Runbooks)
- **Memory:** 1GB
- **Shards:** 1 master shard
- **Replication:** Enabled (except single-node VM)
- **HA:** Enabled where supported (3+ node clusters)
- **Active-Active:** Joined across participating clusters (CRDB/REAADB only)

### Runbooks to Create

#### 1. VM Standard Database
**File:** `runbooks/redis_enterprise/database/vm_standard.yaml`

**Scope:**
- Covers both simple (single-node) and HA (3-node cluster) variants
- Simple: HA disabled, no replication (single node limitation)
- HA: HA enabled, replication enabled
- 1GB memory, 1 master shard

**Prerequisites:**
- Simple variant: Single-node VM cluster deployed
- HA variant: 3-node VM cluster deployed

**Documentation Sources:**
- `operate/rs/databases/create/`

#### 2. VM CRDB (Active-Active)
**File:** `runbooks/redis_enterprise/database/vm_crdb.yaml`

**Scope:**
- Deploy Active-Active CRDB database
- Joined across participating clusters (dual region)
- 1GB memory per instance, 1 master shard, replication enabled

**Prerequisites:**
- 2 VM clusters deployed (using `clustered_3node.yaml` twice)
- VM Active-Active preparation completed (`vm/active_active_prepare.yaml`)

**Documentation Sources:**
- `operate/rs/databases/active-active/create/`

#### 3. Kubernetes REDB
**File:** `runbooks/redis_enterprise/database/kubernetes_redb.yaml`

**Scope:**
- Deploy REDB (Redis Enterprise Database) resource
- HA enabled, replication enabled
- 1GB memory, 1 master shard, replication enabled

**Prerequisites:**
- Kubernetes 3-node cluster deployed (`kubernetes/clustered_3node.yaml`)

**Documentation Sources:**
- `operate/kubernetes/re-databases/`

#### 4. Kubernetes REAADB (Active-Active)
**File:** `runbooks/redis_enterprise/database/kubernetes_reaadb.yaml`

**Scope:**
- Deploy REAADB (Redis Enterprise Active-Active Database) resource
- Joined across participating clusters (dual region)
- 1GB memory per instance, 1 master shard, replication enabled

**Prerequisites:**
- 2 K8s clusters deployed (using `kubernetes/clustered_3node.yaml` twice)
- Kubernetes Active-Active preparation completed (`kubernetes/active_active_prepare.yaml`)

**Documentation Sources:**
- `operate/kubernetes/active-active/`

---

## Summary

### Total Runbooks Planned: 9

**Cluster Deployments (3):**
1. ✅ `vm/single_node.yaml` - Single-node VM (dev/test)
2. ✅ `vm/clustered_3node.yaml` - 3-node VM cluster (reuse for multi-region)
3. 🚧 `kubernetes/clustered_3node.yaml` - 3-node K8s cluster (reuse for multi-region)

**Active-Active Preparation (2):**
4. 🚧 `vm/active_active_prepare.yaml` - Configure 2 VM clusters for Active-Active
5. 🚧 `kubernetes/active_active_prepare.yaml` - Configure 2 K8s clusters for Active-Active

**Database Deployments (4):**
6. 🚧 `database/vm_standard.yaml` - Standard VM database (simple + HA variants)
7. 🚧 `database/vm_crdb.yaml` - Active-Active CRDB (requires #4)
8. 🚧 `database/kubernetes_redb.yaml` - Standard K8s database
9. 🚧 `database/kubernetes_reaadb.yaml` - Active-Active K8s database (requires #5)

### Status
- ✅ **Complete:** 2 runbooks (22%)
- 🚧 **Planned:** 7 runbooks (78%)

### Deployment Flow Examples

**Single-region HA deployment (VM):**
```bash
1. Deploy cluster: vm/clustered_3node.yaml
2. Create database: database/vm_standard.yaml (HA variant)
```

**Dual-region Active-Active deployment (VM):**
```bash
1. Deploy cluster in region A: vm/clustered_3node.yaml
2. Deploy cluster in region B: vm/clustered_3node.yaml
3. Prepare for Active-Active: vm/active_active_prepare.yaml
4. Create CRDB database: database/vm_crdb.yaml
```

**Dual-region Active-Active deployment (Kubernetes):**
```bash
1. Deploy cluster in region A: kubernetes/clustered_3node.yaml
2. Deploy cluster in region B: kubernetes/clustered_3node.yaml
3. Prepare for Active-Active: kubernetes/active_active_prepare.yaml
4. Create REAADB database: database/kubernetes_reaadb.yaml
```

---

## Use Case: Terraform Deployment Repo

These runbooks will serve as the **authoritative design specification** for the `redis-enterprise-terraform-deployments` repository.

**Workflow:**
1. Select deployment variant (e.g., "3-node VM cluster")
2. Open corresponding runbook (e.g., `clustered_3node.yaml`)
3. Use runbook to design Terraform:
   - Prerequisites → Terraform variables/validations
   - Steps → Terraform provisioners/resources
   - Validations → Terraform checks
   - Doc refs → Comments in Terraform code
4. Implement Terraform based on validated procedures
5. Reference runbook version in Terraform comments

**Value:** Ensures Terraform implements correct, validated, production-ready deployment procedures from official Redis documentation.

