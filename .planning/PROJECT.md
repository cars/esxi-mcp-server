# ESXi MCP Server

## What This Is

An MCP (Model Control Protocol) server for managing VMware ESXi hosts via pyVmomi. Exposes 30 MCP tools for VM lifecycle, snapshots, host management, guest operations, and OVA/OVF deployment — all targeting a direct standalone ESXi host connection with no vCenter required. Supports HTTP (Streamable HTTP, port 8080) and stdio transports.

## Core Value

Every MCP tool works against a standalone ESXi host with no vCenter required.

## Requirements

### Validated

- ✓ MCP server with HTTP (Streamable HTTP, port 8080) and stdio transports — v1.0
- ✓ API key authentication via `Authorization: Bearer` or `X-API-Key` headers — v1.0
- ✓ Automatic session reconnection on connection expiry — v1.0
- ✓ VM lifecycle tools: list, power on/off, reboot, delete, create from template — v1.0
- ✓ Snapshot management: create, list, revert, delete snapshots — v1.0
- ✓ Datastore operations: list datastores, browse files, upload files — v1.0
- ✓ Guest operations: run commands, list/upload/download files in guest — v1.0
- ✓ OVA/OVF deployment tool — v1.0
- ✓ Docker containerized deployment — v1.0
- ✓ Layered architecture: transport → MCP → tool handlers → VMware operations — v1.0
- ✓ All 31 MCP tools classified as ESXi-compatible, needs-rewrite, or vCenter-only-remove — v1.0
- ✓ vCenter-only tools removed (`list_datastore_clusters`) — v1.0
- ✓ 8 tools rewritten to use ESXi-compatible pyVmomi patterns — v1.0
- ✓ `clone_vm` rewrites to use `ovftool` subprocess (replaced vCenter-only `CloneVM_Task`) — v1.0
- ✓ All config keys renamed `VCENTER_*` → `ESXI_*` — v1.0
- ✓ `_connect_vcenter()` renamed to `_connect_esxi()`; datacenter/cluster init removed — v1.0
- ✓ All user-facing docs updated for ESXi-only (README, config.yaml.sample, docker-entrypoint.sh, CLAUDE.md) — v1.0

### Active

- [ ] Replace bare `Exception` catches with specific pyVmomi fault types (QUAL-01)
- [ ] Fix authentication flag (`manager.authenticated`) — currently never set to `True` (QUAL-02)
- [ ] Replace busy-wait loops with `pyVmomi.tools.tasks.wait_for_task()` or sleep-based polling (QUAL-03)
- [ ] Add timeout to `_ensure_connected()` session check (QUAL-04)
- [ ] `reboot_vm` tool — graceful guest restart via VMware Tools, then hard reset fallback (FEAT-01)
- [ ] `list_resource_pools` tool — ESXi resource pool visibility (FEAT-02)

### Out of Scope

- vCenter support — pivoting to ESXi-only; dual-mode detection not needed
- Datacenter management tools — vCenter-only concept, no ESXi equivalent
- Cluster management tools — vCenter-only concept, no ESXi equivalent
- Distributed virtual switch (DVS) tools — vCenter-only; standard vSwitches exist on ESXi but DVS does not
- Backwards compatibility with `VCENTER_*` config keys — greenfield usage, breaking changes acceptable

## Context

**Shipped v1.0** with 2,371 LOC Python.
**Tech stack:** Python + pyVmomi — no new dependencies added during pivot.
**Current state:** Fully ESXi-only. 30 MCP tools, all working against standalone ESXi hosts.

Key pyVmomi patterns established during v1.0:
- ESXi VM folder: `host_system = rootFolder.childEntity[0].host[0]; vm_folder = host_system.vm`
- ESXi ContainerView lookups: `CreateContainerView(rootFolder, [vim.Datastore/Network/ResourcePool], True)` + `Destroy()`
- ESXi dcPath: `ha-datacenter` literal (ESXi built-in pseudo-datacenter name)
- `clone_vm` uses `ovftool vi://` subprocess with `--acceptAllEulas`, 600s timeout

## Constraints

- **Tech Stack**: Python + pyVmomi — no new dependencies; all ESXi rewriting done within existing library
- **API Compatibility**: pyVmomi `SmartConnect()` works with standalone ESXi on port 443 — no protocol changes
- **Breaking Changes**: Acceptable — config key renames, removed tools, greenfield usage

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| ESXi-only (drop vCenter support) | Simplifies codebase, matches actual use case | ✓ Good — clean pivot, no dual-mode complexity |
| Remove vCenter-only tools entirely | Cleaner than returning "not supported" errors | ✓ Good — 30 tools all work, no dead endpoints |
| Rename VCENTER_* config keys to ESXI_* | User-facing clarity, no compatibility burden | ✓ Good — docs now accurate and unambiguous |
| `clone_vm` via `ovftool` subprocess | `CloneVM_Task` is vCenter-only, no ESXi equivalent | ✓ Good — requires `ovftool` installed, documented |
| `ha-datacenter` literal for OVF dcPath | ESXi built-in pseudo-datacenter name | ✓ Good — undocumented but reliable on standalone ESXi |
| `host_system.vm` as VM folder for creates | `datacenter_obj.vmFolder` requires vCenter | ✓ Good — consistent pattern across all create/clone/deploy |

---
*Last updated: 2026-03-04 after v1.0 milestone*
