---
phase: 01-audit
plan: 01
subsystem: audit
tags: [vmware, pyVmomi, vSphere, ESXi, vCenter, mcp-tools, classification]

# Dependency graph
requires: []
provides:
  - "Complete tool classification table: 22 ESXi-compatible, 8 needs-rewrite, 1 vCenter-only-remove"
  - "Per-tool rewrite specs with verified line numbers for all 8 needs-rewrite tools"
  - "ESXi equivalents documented for all vCenter-specific pyVmomi expressions"
  - "Phase 2 implementation notes flagging open questions requiring live ESXi testing"
affects:
  - 02-rewrite
  - 03-init-rewrite

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Classification criterion: direct datacenter_obj reference in tool method body (not init-cached objects)"
    - "ESXi VM folder access via content.rootFolder.childEntity[0].host[0].vm"
    - "ESXi resource pool access via content.rootFolder.childEntity[0].resourcePool"
    - "ESXi datastore/network lookup via CreateContainerView(rootFolder, ...) instead of datacenter folder traversal"

key-files:
  created:
    - .planning/phases/01-audit/AUDIT.md
  modified: []

key-decisions:
  - "Init-cached objects (self.resource_pool, self.datastore_obj, self.network_obj) are NOT needs-rewrite in tool methods — they will be fixed by the Phase 3 _connect_vcenter() rewrite"
  - "list_datastore_clusters classified vCenter-only-remove (vim.StoragePod has no ESXi equivalent)"
  - "list_networks classified ESXi-compatible despite vim.dvs check — isinstance guard is already defensive/graceful"
  - "clone_vm needs-rewrite only for the datacenter_obj.vmFolder fallback (line 534), not the primary folder path"
  - "deploy_ovf and deploy_ova have 3 datacenter references each (datastoreFolder, ContainerView, ImportVApp vmFolder)"
  - "upload_file_to_datastore dcPath value on ESXi is uncertain — ha-datacenter or omit; requires live testing"
  - "Phase 2 implementors must decide whether to rename vcenter_host config key in Phase 2 or defer to Phase 3"

patterns-established:
  - "Audit classification criterion: only direct datacenter_obj references in tool method body (not init-time cached objects) trigger needs-rewrite"
  - "AUDIT.md is the authoritative reference for Phase 2 — verified line numbers, current expressions, ESXi equivalents"

requirements-completed: [AUDIT-01, AUDIT-02]

# Metrics
duration: 2min
completed: 2026-03-02
---

# Phase 1 Plan 01: Audit Tool Classification Summary

**Verified audit of all 31 MCP tools against live vmware_manager.py source — 22 ESXi-compatible, 8 needs-rewrite (with per-tool rewrite specs), 1 vCenter-only-remove**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-03T06:40:23Z
- **Completed:** 2026-03-03T06:42:40Z
- **Tasks:** 2 (both tasks included in single AUDIT.md write)
- **Files modified:** 1

## Accomplishments

- Created `.planning/phases/01-audit/AUDIT.md` with a verified 31-row classification table, confirmed against live `vmware_manager.py` source code with exact line numbers
- Produced rewrite specifications for all 8 needs-rewrite tools, each with a table mapping current vCenter expression + line number to ESXi equivalent
- Documented 3 open questions requiring live ESXi testing (dcPath value, wait_for_updates traversal, upload URL format) in Phase 2 Implementation Notes section
- Flagged the Phase 3 config key rename dependency (`vcenter_host` → `esxi_host`) affecting 4 methods across deploy and upload tools

## Task Commits

Each task was committed atomically:

1. **Task 1: Verify tool classifications and produce AUDIT.md classification table** - `5427d85` (feat)
2. **Task 2: Append per-tool rewrite specs** - included in `5427d85` (both tasks written in single file creation; no additional file changes for Task 2)

**Plan metadata:** (see final commit below)

## Files Created/Modified

- `.planning/phases/01-audit/AUDIT.md` — Complete audit document: 31-row classification table, 8 per-tool rewrite specs with verified line numbers, Phase 2 implementation notes

## Decisions Made

- **Classification criterion rigor:** Only direct `datacenter_obj` references inside a tool method body qualify for `needs-rewrite`. Tools using `self.resource_pool`, `self.datastore_obj`, or `self.network_obj` (all set in `_connect_vcenter()` init) are classified ESXi-compatible, because the Phase 3 init rewrite fixes those references at the source.

- **`list_networks` stays ESXi-compatible:** The method checks for `vim.dvs.DistributedVirtualPortgroup` (line 281), but this is a defensive isinstance check — on ESXi with no DVS portgroups, it simply never fires. No rewrite needed.

- **`clone_vm` needs-rewrite scope is narrow:** Only line 534 (the fallback to `self.datacenter_obj.vmFolder`) requires changing. The primary folder assignment (`template_vm.parent`) is already ESXi-compatible.

- **`deploy_ovf` and `deploy_ova` have 3 datacenter references each:** The rewrite spec documents all three (datastoreFolder lookup, ContainerView root, ImportVApp vmFolder argument) to prevent incomplete fixes in Phase 2.

- **Phase 3 config rename dependency flagged explicitly:** Four methods (`upload_file_to_vm`, `upload_file_to_datastore`, `deploy_ovf`, `deploy_ova`) reference `self.config.vcenter_host`. The AUDIT.md documents both options for Phase 2 implementors (rename in Phase 2 or defer to Phase 3).

## Deviations from Plan

None — plan executed exactly as written. Classification counts match research (22/8/1 split confirmed by live code reading). No discrepancies found between the research document (01-RESEARCH.md) line number estimates and the actual live code (all line numbers verified ±0–2 lines of the research estimates).

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- AUDIT.md is complete and ready for Phase 2 implementors to execute against without re-reading `vmware_manager.py`
- All 8 needs-rewrite tools have verified line numbers and ESXi equivalent expressions
- 3 open questions flagged for live ESXi testing during Phase 2 implementation
- Phase 3 config rename dependency documented

---
*Phase: 01-audit*
*Completed: 2026-03-02*
