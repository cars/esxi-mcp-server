---
phase: 02-tool-changes
plan: "05"
subsystem: infra
tags: [vmware, esxi, pyVmomi, config, attribute-rename]

# Dependency graph
requires:
  - phase: 02-tool-changes
    plan: "04"
    provides: "Config.vcenter_host renamed to Config.esxi_host; 4 URL substitution sites updated"
provides:
  - "_connect_vcenter() references self.config.esxi_host at both SmartConnect call sites (lines 47 and 54)"
  - "Server can reach SmartConnect without AttributeError on startup"
  - "RWRT-05 gap fully closed: no remaining vcenter_host attribute access anywhere in vmware_manager.py"
affects: [03-connect-rewrite, 04-cleanup]

# Tech tracking
tech-stack:
  added: []
  patterns: []

key-files:
  created: []
  modified:
    - esxi_mcp_server/vmware_manager.py

key-decisions:
  - "Two-line targeted fix only — vcenter_user and vcenter_password renames remain deferred to Phase 3 per earlier decision"

patterns-established: []

requirements-completed: [RWRT-05]

# Metrics
duration: 1min
completed: 2026-03-03
---

# Phase 2 Plan 5: Fix vcenter_host in _connect_vcenter Summary

**Two-line fix replacing self.config.vcenter_host with self.config.esxi_host in _connect_vcenter(), closing the AttributeError that blocked all server startup since plan 02-04 renamed the Config field**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-03T14:06:40Z
- **Completed:** 2026-03-03T14:07:08Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Fixed AttributeError: 'Config' object has no attribute 'vcenter_host' that prevented server startup
- Updated _connect_vcenter() SSL path (line 47) and standard path (line 54) to reference self.config.esxi_host
- Zero remaining vcenter_host attribute accesses in vmware_manager.py (confirmed by grep returning empty)
- All 6 esxi_host references now consistent: lines 47, 54 (SmartConnect), 938, 978, 1076, 1228 (URL substitutions from plan 02-04)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix vcenter_host references in _connect_vcenter** - `5255734` (fix)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `esxi_mcp_server/vmware_manager.py` - Lines 47 and 54 changed from self.config.vcenter_host to self.config.esxi_host; no other changes

## Decisions Made

None - followed plan as specified. vcenter_user and vcenter_password renames remain deferred to Phase 3 (_connect_vcenter rewrite) per existing decision in STATE.md.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The fix was straightforward: two character substitutions at exactly the lines identified by the plan.

## Verification Results

```
grep -n "self.config.vcenter_host" vmware_manager.py | wc -l
0

grep -n "self.config.esxi_host" vmware_manager.py
47:                    host=self.config.esxi_host,
54:                    host=self.config.esxi_host,
938:        url = re.sub(r"^https://\*:", f"https://{self.config.esxi_host}:", url)
978:        http_url = f"https://{self.config.esxi_host}:443{resource}"
1076:            url = lease.info.deviceUrl[0].url.replace('*', self.config.esxi_host)
1228:                        url = device_url.url.replace('*', self.config.esxi_host)

grep -n "vcenter_host" vmware_manager.py
(no output — zero remaining references)
```

All 3 verification criteria from the plan pass.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 2 is now fully complete with no broken attribute references remaining
- _connect_vcenter() will successfully call SmartConnect with self.config.esxi_host
- Phase 3 (_connect_vcenter rewrite) can proceed: vcenter_user/vcenter_password renames, removing datacenter/cluster init-cache logic, ESXi-specific connection handling

---
*Phase: 02-tool-changes*
*Completed: 2026-03-03*
