# Final Runbook Structure - 9 Runbooks

**Date:** 2026-03-05  
**Status:** Architecture Finalized

---

## Key Architectural Decisions

### 1. Cluster Deployment is Reusable
- For dual-region Active-Active, deploy `clustered_3node.yaml` **twice** (once per region)
- No need for separate "dual-region" cluster runbooks
- Just change cluster name, region, and IPs

### 2. Active-Active Configuration Happens in Two Places
1. **Preparation Runbooks** (Phase C) - Cluster-level configuration:
   - Configure clusters to be aware of each other
   - Exchange credentials/certificates
   - Set up cluster FQDNs
   - Link clusters using rladmin/REST API

2. **Database Runbooks** (Phase D) - Database-level configuration:
   - Create CRDB/REAADB database
   - Join participating instances
   - Verify cross-region replication

### 3. Infrastructure vs Redis Enterprise
**These runbooks cover ONLY Redis Enterprise:**
- ✅ Redis Enterprise installation
- ✅ Redis Enterprise cluster configuration
- ✅ Redis Enterprise Active-Active setup
- ✅ Redis database creation

**Infrastructure is handled in Terraform:**
- ❌ VPC/networking
- ❌ Security groups
- ❌ Load balancers
- ❌ Kubernetes cluster creation

**Preparation runbooks assume infrastructure exists and document prerequisites.**

---

## Complete Runbook Set (9 Total)

### Cluster Deployments (3)
1. ✅ `vm/single_node.yaml` - Single-node VM (dev/test)
2. ✅ `vm/clustered_3node.yaml` - 3-node VM cluster (reuse for multi-region)
3. 🚧 `kubernetes/clustered_3node.yaml` - 3-node K8s cluster (reuse for multi-region)

### Active-Active Preparation (2)
4. 🚧 `vm/active_active_prepare.yaml` - Configure 2 VM clusters for Active-Active
5. 🚧 `kubernetes/active_active_prepare.yaml` - Configure 2 K8s clusters for Active-Active

### Database Deployments (4)
6. 🚧 `database/vm_standard.yaml` - Standard VM database (simple + HA variants)
7. 🚧 `database/vm_crdb.yaml` - Active-Active CRDB (requires #4)
8. 🚧 `database/kubernetes_redb.yaml` - Standard K8s database
9. 🚧 `database/kubernetes_reaadb.yaml` - Active-Active K8s database (requires #5)

---

## Deployment Flow Examples

### Single-Region HA (VM)
```bash
1. Deploy cluster: vm/clustered_3node.yaml
2. Create database: database/vm_standard.yaml (HA variant)
```

### Dual-Region Active-Active (VM)
```bash
1. Deploy cluster in region A: vm/clustered_3node.yaml
2. Deploy cluster in region B: vm/clustered_3node.yaml
3. Prepare for Active-Active: vm/active_active_prepare.yaml
4. Create CRDB database: database/vm_crdb.yaml
```

### Dual-Region Active-Active (Kubernetes)
```bash
1. Deploy cluster in region A: kubernetes/clustered_3node.yaml
2. Deploy cluster in region B: kubernetes/clustered_3node.yaml
3. Prepare for Active-Active: kubernetes/active_active_prepare.yaml
4. Create REAADB database: database/kubernetes_reaadb.yaml
```

---

## What Goes in Each Runbook Type

### Cluster Deployment Runbooks
**Prerequisites:**
- Infrastructure exists (VMs/K8s cluster created in Terraform)
- SSH access / kubectl access configured

**Steps:**
- Install Redis Enterprise software
- Run installation script
- Create cluster via web UI
- Verify cluster is running

**Outputs:**
- Cluster name
- Cluster IP/endpoint
- Admin credentials

### Active-Active Preparation Runbooks
**Prerequisites:**
- 2 clusters deployed (using cluster deployment runbook twice)
- Infrastructure networking configured (VPC peering, security groups, DNS)

**Steps:**
- Configure cluster FQDNs in Redis Enterprise
- Exchange cluster credentials/certificates
- Link clusters using rladmin/REST API (VM) or admission controller (K8s)
- Verify cross-cluster connectivity

**Outputs:**
- Cluster 1 ID
- Cluster 2 ID
- Clusters linked and ready for CRDB/REAADB

### Database Deployment Runbooks
**Prerequisites:**
- Cluster(s) deployed
- For Active-Active: Preparation runbook completed

**Steps:**
- Create database via web UI or kubectl
- Configure database settings (memory, shards, replication)
- For Active-Active: Join participating instances
- Verify database is running

**Outputs:**
- Database name
- Database endpoint
- Connection string

---

## Use Case: Terraform Deployment Repo

These runbooks serve as **design specifications** for Terraform modules:

```
redis-enterprise-terraform-deployments/
├── terraform/
│   ├── aws/
│   │   ├── networking/           # VPC, peering, security groups
│   │   ├── compute/              # EC2 instances
│   │   └── kubernetes/           # EKS cluster
│   └── modules/
│       ├── redis-cluster-vm/     # Based on vm/clustered_3node.yaml
│       ├── redis-aa-prep-vm/     # Based on vm/active_active_prepare.yaml
│       ├── redis-database-vm/    # Based on database/vm_standard.yaml
│       └── redis-crdb/           # Based on database/vm_crdb.yaml
└── runbooks/                     # Copy from this repo (reference)
```

**Workflow:**
1. Infrastructure team uses runbooks to design Terraform networking modules
2. Platform team uses runbooks to design Terraform cluster modules
3. Database team uses runbooks to design Terraform database modules
4. All teams reference the same validated, production-ready procedures

---

## Status

- ✅ **Architecture finalized:** 9-runbook structure
- ✅ **Phase B complete:** 2 runbooks validated
- 🚧 **Phase C planned:** 3 runbooks (Kubernetes + Active-Active prep)
- 🚧 **Phase D planned:** 4 runbooks (Database deployments)

