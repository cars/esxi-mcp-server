# Requirements: ESXi MCP Server (Standalone ESXi Pivot)

**Defined:** 2026-03-02
**Core Value:** Every MCP tool must work against a standalone ESXi host with no vCenter required.

## v1 Requirements

### Audit

- [ ] **AUDIT-01**: All 31 MCP tools classified as ESXi-compatible, needs-rewrite, or vCenter-only-remove
- [ ] **AUDIT-02**: pyVmomi API differences documented for each tool requiring rewrite (vCenter objects → ESXi equivalents)

### Tool Removal

- [ ] **RMVL-01**: `list_datastore_clusters` tool removed — vCenter-only StoragePod concept, no ESXi equivalent

### Tool Rewrites

- [ ] **RWRT-01**: `create_vm` rewritten to use ESXi host folder (`host.vm`) instead of datacenter `vmFolder`, and host resource pool instead of cluster resource pool
- [ ] **RWRT-02**: `clone_vm` rewritten to use ESXi-compatible folder and resource pool placement (no datacenter/cluster objects)
- [ ] **RWRT-03**: `create_vm_custom` rewritten to use ESXi-compatible placement (host folder + host resource pool)
- [ ] **RWRT-04**: `deploy_ovf` and `deploy_ova` verified to work on standalone ESXi; datacenter/cluster references removed from OVF manager calls
- [ ] **RWRT-05**: Any remaining tools that reference `datacenter`, `cluster`, or `ComputeResource` objects updated to use ESXi-compatible equivalents

### Configuration

- [ ] **CONF-01**: Config keys renamed: `VCENTER_HOST` → `ESXI_HOST`, `VCENTER_USER` → `ESXI_USER`, `VCENTER_PASSWORD` → `ESXI_PASSWORD`, `VCENTER_INSECURE` → `ESXI_INSECURE`
- [ ] **CONF-02**: `VCENTER_DATACENTER` and `VCENTER_CLUSTER` config keys removed; corresponding `Config` dataclass fields removed
- [ ] **CONF-03**: `VCENTER_DATASTORE` → `ESXI_DATASTORE`, `VCENTER_NETWORK` → `ESXI_NETWORK` config keys renamed
- [ ] **CONF-04**: Startup connection logic simplified: datacenter and cluster resolution code removed from `VMwareManager` initialization

### Code Renaming

- [ ] **CODE-01**: `_connect_vcenter()` method renamed to `_connect_esxi()` in `vmware_manager.py`; all call sites updated
- [ ] **CODE-02**: `config.py` dataclass field names updated to match new env var names (`vcenter_host` → `esxi_host`, etc.)
- [ ] **CODE-03**: Internal comments, docstrings, and log messages updated to reference ESXi instead of vCenter
- [ ] **CODE-04**: `mcp_server.py` and `tools.py` updated to remove references to removed tools and vCenter-specific concepts

### Documentation

- [ ] **DOCS-01**: `README.md` updated: project description, config key names, tool list, connection instructions for standalone ESXi
- [ ] **DOCS-02**: `config.yaml.sample` updated with new `ESXI_*` variable names and ESXi-specific comments
- [ ] **DOCS-03**: `docker-entrypoint.sh` updated to use new `ESXI_*` environment variable names
- [ ] **DOCS-04**: `CLAUDE.md` updated to reflect new tool count, removed tools, and renamed config keys

## v2 Requirements

### Quality Improvements

- **QUAL-01**: Replace bare `Exception` catches with specific pyVmomi fault types for better error diagnostics
- **QUAL-02**: Fix authentication flag (`manager.authenticated`) — currently never set to `True`, making API key auth non-functional
- **QUAL-03**: Replace busy-wait loops in task completion with `pyVmomi.tools.tasks.wait_for_task()` or sleep-based polling
- **QUAL-04**: Add timeout to `_ensure_connected()` session check to prevent indefinite hangs

### Features

- **FEAT-01**: `reboot_vm` tool (graceful guest restart via VMware Tools, then hard reset fallback)
- **FEAT-02**: `list_resource_pools` tool for ESXi resource pool visibility

## Out of Scope

| Feature | Reason |
|---------|--------|
| vCenter support (dual-mode) | Pivoting to ESXi-only; no auto-detect needed |
| Datacenter management tools | vCenter-only concept, no ESXi equivalent |
| Cluster management tools | vCenter-only concept, no ESXi equivalent |
| Distributed virtual switch (DVS) tools | vCenter-only; ESXi uses standard vSwitch |
| Backwards-compatible `VCENTER_*` config aliases | Greenfield usage; breaking changes acceptable |
| Mobile/web UI | Out of scope for MCP server |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUDIT-01 | Phase 1 | Pending |
| AUDIT-02 | Phase 1 | Pending |
| RMVL-01 | Phase 2 | Pending |
| RWRT-01 | Phase 2 | Pending |
| RWRT-02 | Phase 2 | Pending |
| RWRT-03 | Phase 2 | Pending |
| RWRT-04 | Phase 2 | Pending |
| RWRT-05 | Phase 2 | Pending |
| CONF-01 | Phase 3 | Pending |
| CONF-02 | Phase 3 | Pending |
| CONF-03 | Phase 3 | Pending |
| CONF-04 | Phase 3 | Pending |
| CODE-01 | Phase 3 | Pending |
| CODE-02 | Phase 3 | Pending |
| CODE-03 | Phase 3 | Pending |
| CODE-04 | Phase 3 | Pending |
| DOCS-01 | Phase 4 | Pending |
| DOCS-02 | Phase 4 | Pending |
| DOCS-03 | Phase 4 | Pending |
| DOCS-04 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-02*
*Last updated: 2026-03-02 after roadmap creation*
