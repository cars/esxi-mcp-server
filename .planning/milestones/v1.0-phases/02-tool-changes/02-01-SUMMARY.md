---
phase: 02-tool-changes
plan: 01
subsystem: api
tags: [vmware, mcp, esxi, tool-removal, vim.StoragePod]

# Dependency graph
requires:
  - phase: 01-audit
    provides: Classification of list_datastore_clusters as vCenter-only-remove (vim.StoragePod)
provides:
  - list_datastore_clusters removed from vmware_manager.py, mcp_server.py, and tools.py
  - Tool registry reduced from 31 to 30 tools
  - No vim.StoragePod references remain in the codebase
affects: [02-tool-changes, 03-connect-rewrite]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - esxi_mcp_server/vmware_manager.py
    - esxi_mcp_server/mcp_server.py
    - esxi_mcp_server/tools.py

key-decisions:
  - "Deleted list_datastore_clusters entirely rather than stubbing — vim.StoragePod has no ESXi equivalent"

patterns-established: []

requirements-completed: [RMVL-01]

# Metrics
duration: 1min
completed: 2026-03-03
---

# Phase 2 Plan 01: Remove list_datastore_clusters Summary

**Deleted the vCenter-only list_datastore_clusters tool (vim.StoragePod) from all three layers — vmware_manager.py, mcp_server.py, and tools.py — reducing the tool registry from 31 to 30 ESXi-compatible tools**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-03T07:10:51Z
- **Completed:** 2026-03-03T07:11:41Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Removed `VMwareManager.list_datastore_clusters()` method including all `vim.StoragePod` usage
- Removed tool definition entry from `mcp_server.py` tools dict
- Removed handler map entry from `mcp_server.py` tool_handler_map
- Removed `ToolHandlers.list_datastore_clusters()` delegation method from tools.py
- All three files verified syntactically valid via Python AST check
- Both tools dict and tool_handler_map confirmed at 30 entries each

## Task Commits

Each task was committed atomically:

1. **Task 1: Delete list_datastore_clusters from all three files** - `51232ec` (feat)
2. **Task 2: Verify server imports cleanly** - verification only, no code changes

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `esxi_mcp_server/vmware_manager.py` - Removed list_datastore_clusters method (lines 682-696)
- `esxi_mcp_server/mcp_server.py` - Removed tool definition and handler map entry
- `esxi_mcp_server/tools.py` - Removed delegation method (lines 89-92)

## Decisions Made

- Deleted entirely rather than stubbing with a "not supported" error — per audit classification, vim.StoragePod has no ESXi equivalent and the tool cannot function at all against standalone ESXi

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02-01 complete; list_datastore_clusters is fully eliminated from the codebase
- Ready to proceed with 02-02 through 02-04 (remaining tool changes per ROADMAP)
- No blockers or concerns

## Self-Check: PASSED

- FOUND: .planning/phases/02-tool-changes/02-01-SUMMARY.md
- FOUND: commit 51232ec (feat(02-01): remove list_datastore_clusters tool)
- FOUND: 30 tools in mcp_server.py tools dict
- FOUND: 30 entries in mcp_server.py tool_handler_map
- FOUND: zero occurrences of list_datastore_clusters or StoragePod in the three modified files

---
*Phase: 02-tool-changes*
*Completed: 2026-03-03*
