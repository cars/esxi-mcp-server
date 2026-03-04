---
phase: 02-tool-changes
plan: "08"
subsystem: vmware
tags: [pyVmomi, esxi, ovftool, create_vm, clone_vm, vim.vm.FileInfo]

# Dependency graph
requires:
  - phase: 02-tool-changes
    provides: clone_vm rewritten to ovftool subprocess (plan 07)
provides:
  - vim.vm.FileInfo on ConfigSpec in create_vm and create_vm_custom (fixes InvalidArgument fault)
  - clone_vm ovftool dest_url with no trailing path component
  - clone_vm --acceptAllEulas flag prevents interactive hang
  - clone_vm combined stdout+stderr in error messages
affects: [UAT, testing, phase-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ESXi CreateVM_Task requires configSpec.files = vim.vm.FileInfo(vmPathName='[datastore]')"
    - "ovftool dest_url must be vi://user:pass@host with NO path — name set via --name flag"
    - "ovftool requires --acceptAllEulas to prevent interactive prompt hang"
    - "ovftool error messages appear on stdout not stderr — combine both streams"

key-files:
  created: []
  modified:
    - esxi_mcp_server/vmware_manager.py

key-decisions:
  - "vim.vm.FileInfo vmPathName uses bracketed datastore name format: '[datastore-name]'"
  - "dest_url has NO path component — standalone ESXi interprets path as datacenter name"
  - "--acceptAllEulas added immediately after --noSSLVerify in ovftool cmd list"
  - "combined = (result.stdout + result.stderr).strip() used for error reporting"

patterns-established:
  - "ConfigSpec.files must be set before any device change operations on ESXi"
  - "ovftool subprocess error handling must capture stdout (not just stderr)"

requirements-completed: [RWRT-01, RWRT-02]

# Metrics
duration: 1min
completed: 2026-03-04
---

# Phase 02 Plan 08: UAT Gap Closure Summary

**Fixed three UAT-diagnosed bugs in vmware_manager.py: vim.vm.FileInfo on ConfigSpec for create_vm/create_vm_custom, and three interrelated ovftool bugs (wrong dest_url, missing --acceptAllEulas, empty stderr error) in clone_vm**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-04T00:27:59Z
- **Completed:** 2026-03-04T00:28:30Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- create_vm and create_vm_custom now set `configSpec.files = vim.vm.FileInfo(vmPathName='[datastore-name]')`, eliminating vmodl.fault.InvalidArgument on startup
- clone_vm dest_url no longer has a trailing `/{new_name}` path component — standalone ESXi no longer misinterprets it as a datacenter name
- clone_vm --acceptAllEulas prevents ovftool from hanging interactively waiting for user input
- clone_vm error messages now combine stdout+stderr so failures produce meaningful diagnostic output

## Task Commits

Each task was committed atomically:

1. **Task 1: Add vim.vm.FileInfo to create_vm and create_vm_custom ConfigSpecs** - `5bfa111` (fix)
2. **Task 2: Fix clone_vm ovftool invocation — dest_url, --acceptAllEulas, error output** - `128f6c1` (fix)

## Files Created/Modified

- `esxi_mcp_server/vmware_manager.py` - Three targeted bug fixes: FileInfo on ConfigSpec (2 locations), dest_url no trailing path, --acceptAllEulas flag, combined stdout+stderr error

## Decisions Made

- vim.vm.FileInfo vmPathName uses the bracketed datastore name format `[datastore-name]` which is the vSphere canonical datastore path prefix
- dest_url must be `vi://user:pass@host` with NO trailing path — ESXi treats path component as datacenter name causing lookup failure on standalone hosts
- --acceptAllEulas placed immediately after --noSSLVerify in the cmd list (consistent positioning)
- Error handler combines `result.stdout + result.stderr` because ovftool writes diagnostic messages to stdout rather than stderr

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All three UAT-identified bugs are now fixed in vmware_manager.py
- create_vm, create_vm_custom, and clone_vm should now function correctly against standalone ESXi
- Ready for UAT re-validation to confirm all five must_have truths pass
- Phase 3 (_connect_vcenter rewrite, vcenter_user/vcenter_password rename) can proceed

---
*Phase: 02-tool-changes*
*Completed: 2026-03-04*
