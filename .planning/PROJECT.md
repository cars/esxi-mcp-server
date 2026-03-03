# ESXi MCP Server (Standalone ESXi Pivot)

## What This Is

An MCP (Model Control Protocol) server for managing VMware infrastructure via pyVmomi, being refactored from vCenter-centric to standalone ESXi-only operation. It exposes MCP tools for VM lifecycle, snapshots, host management, guest operations, and OVA/OVF deployment — all targeting a direct ESXi host connection without requiring vCenter.

## Core Value

Every MCP tool must work against a standalone ESXi host with no vCenter required.

## Requirements

### Validated

- ✓ MCP server with HTTP (Streamable HTTP, port 8080) and stdio transports — existing
- ✓ API key authentication via `Authorization: Bearer` or `X-API-Key` headers — existing
- ✓ Automatic session reconnection on connection expiry — existing
- ✓ VM lifecycle tools: list, power on/off, reboot, delete, create from template — existing
- ✓ Snapshot management: create, list, revert, delete snapshots — existing
- ✓ Datastore operations: list datastores, browse files, upload files — existing
- ✓ Guest operations: run commands, list/upload/download files in guest — existing
- ✓ OVA/OVF deployment tool — existing
- ✓ Docker containerized deployment — existing
- ✓ Layered architecture: transport → MCP → tool handlers → VMware operations — existing

### Active

- [ ] Audit all 31 MCP tools and classify each as ESXi-compatible or vCenter-only
- [ ] Remove tools that require vCenter-only constructs (datacenters, clusters, distributed virtual switches)
- [ ] Rewrite tools with vCenter-specific pyVmomi API calls to use ESXi-compatible equivalents
- [ ] Rename all config keys from `VCENTER_*` to `ESXI_*` (ESXI_HOST, ESXI_USER, ESXI_PASSWORD, etc.)
- [ ] Rename internal code references: `_connect_vcenter` → `_connect_esxi`, config field names, comments, docstrings
- [ ] Simplify startup connection logic: remove datacenter/cluster resolution (not applicable to standalone ESXi)
- [ ] Update all user-facing documentation: README, config.yaml.sample, docker-entrypoint.sh, CLAUDE.md

### Out of Scope

- vCenter support — pivoting to ESXi-only; dual-mode detection not needed
- Datacenter management tools — vCenter-only concept, no ESXi equivalent
- Cluster management tools — vCenter-only concept, no ESXi equivalent
- Distributed virtual switch (DVS) tools — vCenter-only; standard vSwitches exist on ESXi but DVS does not
- Backwards compatibility with existing `VCENTER_*` config keys — greenfield usage, breaking changes acceptable

## Context

The project was originally built assuming a vCenter-managed environment. pyVmomi supports both vCenter and standalone ESXi connections via `SmartConnect()` — the host simply needs to be an ESXi IP/hostname rather than vCenter. Many tools will work as-is; the audit will identify which ones use vCenter-specific objects (like `ComputeResource`, `Datacenter`, `ClusterComputeResource`, `DistributedVirtualSwitch`) vs ESXi-compatible objects (like `HostSystem`, `VirtualMachine`, `Datastore`, `ResourcePool`).

Key pyVmomi distinction:
- ESXi-compatible: `vim.HostSystem`, `vim.VirtualMachine`, `vim.Datastore`, `vim.ResourcePool`, `vim.Network`
- vCenter-only: `vim.Datacenter`, `vim.ClusterComputeResource`, `vim.dvs.*`, `vim.ComputeResource` (when used for cluster abstraction)

## Constraints

- **Tech Stack**: Python + pyVmomi — no new dependencies; all ESXi rewriting done within existing library
- **API Compatibility**: pyVmomi `SmartConnect()` works with standalone ESXi on port 443 — no protocol changes
- **Breaking Changes**: Acceptable — config key renames, removed tools, greenfield usage

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| ESXi-only (drop vCenter support) | Simplifies codebase, matches actual use case | — Pending |
| Remove vCenter-only tools entirely | Cleaner than returning "not supported" errors | — Pending |
| Rename VCENTER_* config keys to ESXI_* | User-facing clarity, no compatibility burden | — Pending |

---
*Last updated: 2026-03-02 after initialization*
