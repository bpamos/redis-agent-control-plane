# Redis Enterprise Installation Documentation Findings

**Date:** 2026-03-05  
**Purpose:** Extract actual Redis Enterprise installation procedures from documentation for validated runbooks  
**Target Version:** Redis Software 8.0.x (latest)

---

## Latest Version Information

**Redis Software 8.0.x** is the latest version as of the documentation.

**Key Features:**
- Redis 8.0, 8.2, and 8.4 feature set versions
- Performance improvements and memory reduction
- New vector set data structure
- Redis Flex revamped engine

**Source:** `../docs/content/operate/rs/release-notes/rs-8-0-releases/_index.md`

---

## Installation Prerequisites

**Source:** `../docs/content/operate/rs/installing-upgrading/install/plan-deployment/hardware-requirements.md`

### Minimum Requirements
- **Production:** Minimum of 3 nodes (uneven number recommended)
- **Development/Testing:** Single node supported (with limitations - no HA/replication)
- **Memory:** Varies by use case (see sizing considerations)
- **Storage:** Persistent and ephemeral storage paths required

### Sizing Considerations
- Dataset size + overhead
- Database throughput (affects shard count)
- Modules usage (increases memory)
- Database clustering (spreads data across shards)
- Database replication (doubles memory consumption)

---

## Download Installation Package

**Source:** `../docs/content/operate/rs/installing-upgrading/install/prepare-install/download-install-package.md`

### Download Steps
1. Go to [Redis download page](https://cloud.redis.io/#/rlec-downloads)
2. Sign in with Redis credentials or create account
3. In Downloads section for Redis Software, select installation package for your platform
4. Select **Go** to download

**Note:** Package is platform-specific (Ubuntu/Debian, RHEL, etc.)

---

## Installation Steps on Linux

**Source:** `../docs/content/operate/rs/installing-upgrading/install/install-on-linux.md`

### Step-by-Step Installation

1. **Copy installation package to the node**

2. **Extract the installation files:**
   ```sh
   tar vxf <tarfile name>
   ```

3. **(Optional) Verify package authenticity using GPG:**
   - For Ubuntu:
     ```sh
     gpg --import <path to GPG key>
     dpkg-sig --verify </path-to/package.deb>
     ```
   - For RHEL:
     ```sh
     rpm --import <path to GPG key>
     rpm --checksig </path-to/package.rpm>
     ```

4. **Run the installation script:**
   
   **Default installation:**
   ```sh
   sudo ./install.sh
   ```
   
   **Custom installation directories:**
   ```sh
   sudo ./install.sh --install-dir <path> --config-dir <path> --var-dir <path>
   ```
   
   **Silent installation (skip questions):**
   ```sh
   sudo ./install.sh -y
   ```

5. **Answer installation questions** (or use `-y` flag to skip)

6. **Installation complete** - Output displays Cluster Manager UI address:
   ```
   Summary:
   -------
   ALL TESTS PASSED.
   Please logout and login again to make sure all environment changes are applied.
   Point your browser at the following URL to continue:
   https://<your_ip_here>:8443
   ```

7. **Repeat for each node in the cluster**

### Important Notes
- Must be root user or use `sudo`
- Default user/group: `redislabs`/`redislabs`
- Default port for Cluster Manager UI: `8443` (HTTPS)
- Uses self-signed certificate for TLS

---

## Cluster Setup

**Source:** `../docs/content/operate/rs/clusters/new-cluster-setup.md`

### Create New Cluster (via Web UI)

1. **Access Cluster Manager UI:**
   - Navigate to `https://<IP address>:8443`
   - Example: `https://10.0.1.34:8443`

2. **Select "Create new cluster"**

3. **Create administrator account:**
   - Enter email and password
   - Select **Next**

4. **Enter cluster license key** (or use trial license)

5. **Configure cluster settings:**
   - **FQDN:** Enter unique cluster name
   - **Private & public endpoints:** Enable if needed
   - **Rack-zone awareness:** Enable if needed
   - Select **Next**

6. **Configure storage and network:**
   - **Ephemeral storage path:** Enter or use default
   - **Persistent storage path:** Enter or use default
   - **Flash storage:** Enable for Redis Flex/Auto Tiering (optional)
   - **Rack-zone ID:** Set if rack-zone awareness enabled
   - **IP addresses:** Configure internal and external IPs if multiple available

7. **Select "Create cluster"**

8. **Confirm TLS certificate replacement**

9. **Cluster created** - Sign in to Cluster Manager UI

### Post-Setup Actions
- Create databases
- Add additional nodes to cluster

---

## Key Documentation References

All paths relative to `../docs/content/operate/rs/`:

1. **Installation:**
   - `installing-upgrading/install/install-on-linux.md`
   - `installing-upgrading/install/prepare-install/download-install-package.md`
   - `installing-upgrading/install/install-script.md`

2. **Planning:**
   - `installing-upgrading/install/plan-deployment/hardware-requirements.md`
   - `installing-upgrading/install/plan-deployment/supported-platforms.md`
   - `installing-upgrading/install/plan-deployment/persistent-ephemeral-storage.md`

3. **Cluster Setup:**
   - `clusters/new-cluster-setup.md`
   - `clusters/add-node.md`

4. **Release Notes:**
   - `release-notes/rs-8-0-releases/_index.md`

---

## Next Steps

Use this information to create validated runbooks:
1. Single-node VM deployment (development/testing)
2. 3-node VM cluster deployment (production)

All commands and procedures extracted from actual Redis Enterprise documentation.

