---
phase: 02-tool-changes
plan: 04
subsystem: vmware
tags: [pyvmomi, esxi, config, url-substitution, traversal-spec, datacenter]

# Dependency graph
requires:
  - phase: 02-tool-changes
    provides: "deploy_ovf and deploy_ova ESXi-compatible (host_system.vm as ImportVApp folder)"
provides:
  - "upload_file_to_datastore uses ha-datacenter literal for dcPath"
  - "_build_traversal_spec ESXi-compatible (folder_to_child only, no Datacenter traversal)"
  - "Config.esxi_host field (was vcenter_host); VCENTER_HOST env var maps to esxi_host"
  - "All 4 URL substitution lines use self.config.esxi_host"
  - "RWRT-05 fully satisfied; Phase 2 complete"
affects: [03-connect, config-rename-phase-3]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ESXi dcPath: use ha-datacenter literal (ESXi built-in pseudo-datacenter name)"
    - "ESXi traversal: rootFolder -> ComputeResource directly (no vim.Datacenter wrapper)"
    - "Config rename: VCENTER_HOST env var kept for backward compat; Python attr is esxi_host"

key-files:
  created: []
  modified:
    - esxi_mcp_server/vmware_manager.py
    - esxi_mcp_server/config.py

key-decisions:
  - "ha-datacenter literal replaces self.datacenter_obj.name for ESXi dcPath (ESXi has no user-named datacenter)"
  - "_build_traversal_spec simplified to folder_to_child only — ESXi has no vim.Datacenter in object tree"
  - "VCENTER_HOST env var kept for backward compatibility; Python attribute renamed to esxi_host (Option A)"
  - "vcenter_user and vcenter_password field renames deferred to Phase 3 (_connect_vcenter rewrite scope)"

patterns-established:
  - "ESXi URL host substitution: self.config.esxi_host replaces wildcard (*) in device URLs"
  - "ESXi folder traversal: single folderToChild spec sufficient (no Datacenter wrapper to traverse)"

requirements-completed:
  - RWRT-05

# Metrics
duration: 1min
completed: 2026-03-03
---

# Phase 02 Plan 04: ESXi dcPath, traversal spec, and config rename Summary

**ESXi-compatible dcPath literal (ha-datacenter), simplified traversal spec (folder_to_child only), and vcenter_host -> esxi_host config rename completing RWRT-05 and all Phase 2 changes**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-03T07:24:51Z
- **Completed:** 2026-03-03T07:25:51Z
- **Tasks:** 3 (2 with commits, 1 verification-only)
- **Files modified:** 2

## Accomplishments
- Fixed `upload_file_to_datastore` to use `"ha-datacenter"` literal for `dcPath` instead of `self.datacenter_obj.name` (ESXi does not have user-named datacenters)
- Simplified `_build_traversal_spec` to return `[folder_to_child]` only — removed `dc_to_vmfolder` and `dc_to_hostfolder` Datacenter traversal specs that have no equivalent in ESXi's object tree
- Renamed `Config.vcenter_host` to `Config.esxi_host`; `VCENTER_HOST` env var still maps to `esxi_host` for backward compatibility; all 4 URL substitution lines updated
- Verified zero `datacenter_obj` references outside `_connect_vcenter` — all Phase 2 rewrites complete

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix upload_file_to_datastore dcPath and simplify _build_traversal_spec** - `6392684` (fix)
2. **Task 2: Verify no datacenter_obj remains outside _connect_vcenter** - verification only, no commit
3. **Task 3: Rename vcenter_host to esxi_host in config.py and update 4 URL references** - `2cf1996` (feat)

**Plan metadata:** (docs commit — created after self-check)

## Files Created/Modified
- `esxi_mcp_server/vmware_manager.py` - dcPath literal, simplified traversal spec, 4 URL substitution renames
- `esxi_mcp_server/config.py` - Config dataclass field vcenter_host -> esxi_host; env_map and required_keys updated

## Decisions Made
- `ha-datacenter` literal chosen for `dcPath` because ESXi doesn't expose a user-named datacenter; comment added noting alternative of omitting key if HTTP 404 occurs
- `_build_traversal_spec` collapse to single `folder_to_child` spec because ESXi root folder contains `ComputeResource` directly without `vim.Datacenter` wrapper
- `VCENTER_HOST` env var name preserved (backward compatible); only the Python attribute name changes to `esxi_host`
- `vcenter_user` and `vcenter_password` config renames scoped to Phase 3 alongside `_connect_vcenter` rewrite

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Task 2 verification grep produced a false FAIL because `if not self.datacenter_obj:` conditionals weren't covered by the grep exclusion patterns. Line-number check confirmed all references were within `_connect_vcenter` (lines 38-127). True result: PASS.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All Phase 2 code changes complete (RMVL-01, RWRT-01 through RWRT-05)
- Phase 3 (`_connect_vcenter` rewrite) can begin; it will:
  - Replace the vCenter-style connect logic with ESXi-direct `SmartConnect`
  - Rename `vcenter_user` and `vcenter_password` config fields
  - Update `self.config.vcenter_host` references on lines 47, 54 to `self.config.esxi_host`
  - Remove `self.datacenter_obj` entirely (init + `_connect_vcenter` body)

## Self-Check: PASSED

- FOUND: esxi_mcp_server/vmware_manager.py
- FOUND: esxi_mcp_server/config.py
- FOUND: .planning/phases/02-tool-changes/02-04-SUMMARY.md
- FOUND commit: 6392684 (fix dcPath + traversal spec)
- FOUND commit: 2cf1996 (config rename + URL substitutions)
- FOUND: ha-datacenter dcPath literal in vmware_manager.py
- FOUND: return [folder_to_child] in _build_traversal_spec
- FOUND: esxi_host: str in config.py
- FOUND: 4 esxi_host references in vmware_manager.py

---
*Phase: 02-tool-changes*
*Completed: 2026-03-03*
