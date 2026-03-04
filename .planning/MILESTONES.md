# Milestones

## v1.0 ESXi Pivot (Shipped: 2026-03-04)

**Phases completed:** 4 phases, 15 plans
**Timeline:** 2026-03-02 → 2026-03-04 (2 days)
**LOC:** 2,371 Python

**Key accomplishments:**
- Classified all 31 MCP tools: 22 ESXi-compatible, 8 needs-rewrite, 1 vCenter-only-remove
- Removed `list_datastore_clusters` (vCenter-only `vim.StoragePod`, no ESXi equivalent)
- Rewrote 8 tools to use ESXi-compatible pyVmomi patterns (`host_system.vm`, `ContainerView`, `rootFolder` traversal)
- Rewrote `clone_vm` to use `ovftool` subprocess via `vi://` URL (replaced vCenter-only `CloneVM_Task`)
- Renamed all config keys (`VCENTER_*` → `ESXI_*`) and `_connect_vcenter()` → `_connect_esxi()`; removed datacenter/cluster init
- Updated all user-facing docs (README, `config.yaml.sample`, `docker-entrypoint.sh`, `CLAUDE.md`) to reflect ESXi-only server

---

