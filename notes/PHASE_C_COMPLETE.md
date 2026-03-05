# Phase C Complete: Kubernetes Cluster & Active-Active Preparation

**Date:** 2026-03-05  
**Status:** ✅ COMPLETE

---

## Deliverables

- ✅ `runbooks/redis_enterprise/kubernetes/clustered.yaml` (v2.0.0, 6 steps)
- ✅ `runbooks/redis_enterprise/vm/active_active_prepare.yaml` (v2.0.0, 9 steps)
- ✅ `runbooks/redis_enterprise/kubernetes/active_active.yaml` (v2.0.0, 9 steps)
- ✅ Updated `scripts/validate_runbooks.py` to validate Kubernetes runbooks

## Validation Results

- 6/6 runbooks passed validation (3 new + 3 existing)
- All doc_refs validated
- All commands extracted from Redis Enterprise 8.0.x documentation

## Architecture Notes

**Cluster deployment is reusable:**
- For dual-region Active-Active, deploy `clustered_3node.yaml` twice (once per region)
- The "Active-Active" configuration happens in preparation runbooks (networking, cluster linking)
- Database-level Active-Active happens in database runbooks (CRDB/REAADB creation)

**Infrastructure vs Redis Enterprise:**
- These runbooks cover ONLY Redis Enterprise configuration
- Infrastructure (VPC, peering, security groups, K8s clusters) is handled in Terraform
- Preparation runbooks assume infrastructure exists and document prerequisites

## Runbook Details

### 1. Kubernetes 3-Node Cluster (`kubernetes/clustered.yaml`)
- Redis Enterprise Operator installation
- 3-node REC (Redis Enterprise Cluster) deployment
- Single Kubernetes cluster
- Reusable for multi-region (deploy twice)

### 2. VM Active-Active Preparation (`vm/active_active_prepare.yaml`)
- Configure Redis Enterprise clusters to be aware of each other
- Exchange cluster credentials/certificates
- Set up cluster FQDNs in Redis Enterprise
- Use rladmin/REST API to link clusters
- Assumes: VPC peering, security groups, DNS already configured in Terraform

### 3. Kubernetes Active-Active Preparation (`kubernetes/active_active.yaml`)
- Install admission controller on both clusters
- Exchange secrets between clusters
- Configure REAADB prerequisites
- Set up participating cluster configuration
- Assumes: Cross-cluster networking, K8s clusters already configured in Terraform

## Documentation Sources Researched

- `operate/kubernetes/deployment/` - Kubernetes deployment
- `operate/kubernetes/rec/` - Redis Enterprise Cluster on K8s
- `operate/rs/clusters/active-active/` - Active-Active cluster configuration
- `operate/kubernetes/active-active/` - Kubernetes Active-Active setup
- `operate/rs/databases/active-active/create/` - CRDB creation (for context)

## Next Steps

✅ Phase C complete → Move to Phase D (Database Deployment Runbooks)

