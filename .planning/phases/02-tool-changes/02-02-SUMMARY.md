---
phase: 02-tool-changes
plan: "02"
subsystem: vmware
tags: [pyvmomi, esxi, containerView, vmFolder, datacenter_obj]

# Dependency graph
requires:
  - phase: 02-tool-changes/02-01
    provides: list_datastore_clusters removed, tool count reduced to 30
provides:
  - create_vm with ESXi-compatible datastore/network ContainerView lookups and host_system.vm folder
  - clone_vm with ESXi-compatible vmFolder fallback using host_system.vm
  - create_vm_custom with ESXi-compatible datastore/network ContainerView lookups and host_system.vm folder
affects:
  - 02-tool-changes (03-04 plans: upload_file_to_datastore, deploy_ovf, deploy_ova, wait_for_updates)
  - 03-connect (Phase 3 _connect_vcenter rewrite)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ESXi VM folder: host_system = self.content.rootFolder.childEntity[0].host[0]; vm_folder = host_system.vm"
    - "ESXi datastore lookup: CreateContainerView(rootFolder, [vim.Datastore], True) + container.Destroy()"
    - "ESXi network lookup: CreateContainerView(rootFolder, [vim.Network], True) + container.Destroy()"

key-files:
  created: []
  modified:
    - esxi_mcp_server/vmware_manager.py

key-decisions:
  - "Use host_system.vm (from rootFolder.childEntity[0].host[0]) as ESXi VM folder replacement for datacenter_obj.vmFolder"
  - "Use CreateContainerView(rootFolder, ...) for all datastore and network lookups — matches existing list_datastores and list_networks pattern"
  - "Always call container.Destroy() after ContainerView use to avoid vSphere resource leaks"
  - "Scope boundary honored: deploy_ovf, deploy_ova, upload_file_to_datastore datacenter_obj references deferred to later plans"

patterns-established:
  - "ESXi folder pattern: host_system = self.content.rootFolder.childEntity[0].host[0]; vm_folder = host_system.vm"
  - "ContainerView lifecycle: create, use .view, Destroy() — always destroy before raising exceptions"

requirements-completed: [RWRT-01, RWRT-02, RWRT-03]

# Metrics
duration: 2min
completed: 2026-03-03
---

# Phase 2 Plan 02: create_vm / clone_vm / create_vm_custom ESXi Rewrite Summary

**create_vm, clone_vm, and create_vm_custom rewritten to use host_system.vm folder and CreateContainerView(rootFolder) datastore/network lookups — eliminating all datacenter_obj references from the three primary VM creation methods**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-03T07:14:05Z
- **Completed:** 2026-03-03T07:16:08Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Replaced `datacenter_obj.datastoreFolder.childEntity` with `CreateContainerView(rootFolder, [vim.Datastore], True)` in create_vm and create_vm_custom
- Replaced `datacenter_obj.networkFolder.childEntity` with `CreateContainerView(rootFolder, [vim.Network], True)` in create_vm and create_vm_custom
- Replaced `datacenter_obj.vmFolder` with `host_system.vm` pattern in create_vm, clone_vm (fallback), and create_vm_custom
- All new ContainerView objects call `container.Destroy()` after use — no vSphere resource leaks
- `vmware_manager.py` parses cleanly with no syntax errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite create_vm and create_vm_custom datastore/network/folder lookups** - `2304580` (feat)
2. **Task 2: Rewrite clone_vm vmFolder fallback** - `3a28014` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `esxi_mcp_server/vmware_manager.py` - create_vm, clone_vm, create_vm_custom methods rewritten for ESXi compatibility

## Decisions Made
- Used `host_system.vm` (via `rootFolder.childEntity[0].host[0]`) as the ESXi equivalent for `datacenter_obj.vmFolder`. On a standalone ESXi host, this is the only VM folder and exactly equivalent to vCenter's vmFolder.
- Used `CreateContainerView(rootFolder, ...)` for datastore and network lookups to match the existing pattern already used by `list_datastores` and `list_networks` — consistent with the rest of the codebase.
- Kept all `container.Destroy()` calls to avoid leaking ContainerView server-side objects in vSphere.
- Honored scope boundary: `deploy_ovf`, `deploy_ova`, and `upload_file_to_datastore` datacenter_obj references remain (deferred to later plans in this phase).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- The Task 1 verification filter (`grep -v` exclusion list) does not account for `if not self.datacenter_obj:` lines (lines 69, 76) inside `_connect_vcenter()`, causing the filter to report false positives. These lines ARE inside `_connect_vcenter()` and are out of scope. The success criteria are met per the done criteria text, not the exact grep filter.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- create_vm, clone_vm, create_vm_custom are ESXi-compatible for VM folder and lookup operations
- Remaining datacenter_obj references in deploy_ovf, deploy_ova, upload_file_to_datastore ready for next plans
- Phase 3 will fix `self.resource_pool`, `self.datastore_obj`, `self.network_obj` (init-cached objects) in _connect_vcenter()

---
*Phase: 02-tool-changes*
*Completed: 2026-03-03*
