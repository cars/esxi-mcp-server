# Roadmap: ESXi MCP Server (Standalone ESXi Pivot)

## Overview

The project pivots from a vCenter-centric MCP server to one that works exclusively against a standalone ESXi host. The work flows in four phases: first audit every tool to know what to fix, then remove and rewrite the tools themselves, then rename all internal code and config to reflect ESXi instead of vCenter, and finally update all user-facing documentation. Each phase builds directly on the previous — no safe tool rewriting without the audit, no clean rename without tools already fixed.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Audit** - Classify all 31 MCP tools and document ESXi vs vCenter API differences
- [x] **Phase 2: Tool Changes** - Remove vCenter-only tools and rewrite tools that use vCenter-specific API objects (gap closure in progress)
- [x] **Phase 3: Code and Config Rename** - Rename config keys, method names, and internal references from vCenter to ESXi (completed 2026-03-04)
- [x] **Phase 4: Documentation** - Update all user-facing documentation to reflect the standalone ESXi pivot (completed 2026-03-04)

## Phase Details

### Phase 1: Audit
**Goal**: Every MCP tool is classified and any required rewrite is documented before a single line of production code changes
**Depends on**: Nothing (first phase)
**Requirements**: AUDIT-01, AUDIT-02
**Success Criteria** (what must be TRUE):
  1. A written classification exists for each of the 31 tools: ESXi-compatible, needs-rewrite, or vCenter-only-remove
  2. For every tool marked needs-rewrite, the specific vCenter objects used and their ESXi equivalents are documented
  3. The audit output can be referenced directly to drive Phase 2 work without requiring code re-inspection
**Plans**: 1 plan

Plans:
- [x] 01-01-PLAN.md — Verify tool classifications against live source and produce complete AUDIT.md with classification table and rewrite specs

### Phase 2: Tool Changes
**Goal**: Every MCP tool exposed by the server either works correctly against a standalone ESXi host or has been removed
**Depends on**: Phase 1
**Requirements**: RMVL-01, RWRT-01, RWRT-02, RWRT-03, RWRT-04, RWRT-05
**Success Criteria** (what must be TRUE):
  1. `list_datastore_clusters` tool no longer exists in the server's tool registry
  2. `create_vm` and `create_vm_custom` use host resource pool and datacenter vmFolder — no wrong childEntity[0].host traversal
  3. `clone_vm` tool removed — CloneVM_Task is vCenter-only, no ESXi equivalent
  4. `deploy_ovf` and `deploy_ova` complete successfully when pointed at a standalone ESXi host
  5. No remaining tool in vmware_manager.py, mcp_server.py, or tools.py references `vim.Datacenter`, `vim.ClusterComputeResource`, or `vim.dvs.*` objects
**Plans**: 8 plans

Plans:
- [x] 02-01-PLAN.md — Remove list_datastore_clusters from vmware_manager.py, mcp_server.py, and tools.py
- [x] 02-02-PLAN.md — Rewrite create_vm, clone_vm, create_vm_custom to use ESXi host folder and ContainerView lookups
- [x] 02-03-PLAN.md — Rewrite deploy_ovf and deploy_ova to use ESXi-compatible datastore/resource pool/folder patterns
- [x] 02-04-PLAN.md — Fix upload_file_to_datastore dcPath and simplify _build_traversal_spec for ESXi
- [x] 02-05-PLAN.md — Gap closure: fix _connect_vcenter() to reference self.config.esxi_host (two-line fix, RWRT-05)
- [x] 02-06-PLAN.md — Gap closure: fix wrong host traversal in create_vm, create_vm_custom, deploy_ovf, deploy_ova (store self.compute_resource; use datacenter_obj.vmFolder)
- [x] 02-07-PLAN.md — Gap closure: rewrite clone_vm to use ovftool vi:// subprocess (CloneVM_Task is vCenter-only)
- [x] 02-08-PLAN.md — Gap closure: fix vim.vm.FileInfo missing from create_vm/create_vm_custom; fix clone_vm dest_url, --acceptAllEulas, error output

### Phase 3: Code and Config Rename
**Goal**: All internal identifiers — config keys, environment variables, method names, comments, and log messages — use ESXi terminology instead of vCenter
**Depends on**: Phase 2
**Requirements**: CONF-01, CONF-02, CONF-03, CONF-04, CODE-01, CODE-02, CODE-03, CODE-04
**Success Criteria** (what must be TRUE):
  1. Server starts successfully using `ESXI_HOST`, `ESXI_USER`, `ESXI_PASSWORD`, and `ESXI_INSECURE` environment variables
  2. `VCENTER_DATACENTER` and `VCENTER_CLUSTER` environment variables are not read or referenced anywhere in the codebase
  3. `_connect_vcenter()` method does not exist; `_connect_esxi()` is used at all call sites
  4. No `vcenter` string appears in config field names, log output, or in-code docstrings (excluding git history and out-of-scope files)
**Plans**: 2 plans

Plans:
- [x] 03-01-PLAN.md — Rename Config dataclass fields and env_map: ESXI_* keys, esxi_user/esxi_password fields, remove datacenter/cluster
- [ ] 03-02-PLAN.md — Rename _connect_vcenter to _connect_esxi, remove datacenter/cluster branches, update field refs and comments

### Phase 4: Documentation
**Goal**: Every piece of user-facing documentation accurately describes the ESXi-only server with correct config key names, tool list, and connection instructions
**Depends on**: Phase 3
**Requirements**: DOCS-01, DOCS-02, DOCS-03, DOCS-04
**Success Criteria** (what must be TRUE):
  1. README.md describes standalone ESXi connection and lists only the tools that remain after Phase 2 removals
  2. `config.yaml.sample` shows only `ESXI_*` variable names with ESXi-appropriate comments; no `VCENTER_*` keys present
  3. `docker-entrypoint.sh` generates config using `ESXI_*` environment variable names; a container started with `ESXI_HOST` set connects successfully
  4. `CLAUDE.md` reflects the updated tool count, removed tools, and renamed config keys so future Claude sessions start with accurate context
**Plans**: 4 plans

Plans:
- [ ] 04-01-PLAN.md — Update README.md: ESXi-only description, esxi_* config YAML, ESXI_* env vars table, ovftool note for clone_vm
- [ ] 04-02-PLAN.md — Replace config.yaml.sample: esxi_host/esxi_user/esxi_password YAML keys, remove datacenter/cluster fields
- [ ] 04-03-PLAN.md — Update docker-entrypoint.sh: ESXI_* env var names throughout, remove datacenter/cluster conditionals
- [ ] 04-04-PLAN.md — Update CLAUDE.md: 30 tools (not 31), ESXi-only description, ESXI_* config keys, connects to ESXi

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Audit | 1/1 | Complete | 2026-03-02 |
| 2. Tool Changes | 8/8 | Complete | 2026-03-04 |
| 3. Code and Config Rename | 2/2 | Complete   | 2026-03-04 |
| 4. Documentation | 4/4 | Complete    | 2026-03-04 |
