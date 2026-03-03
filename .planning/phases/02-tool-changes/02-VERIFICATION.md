---
phase: 02-tool-changes
verified: 2026-03-03T23:30:00Z
status: passed
score: 6/6 requirements satisfied
re_verification: true
  previous_status: passed
  previous_score: 4/4 success criteria verified
  previous_verified: 2026-03-03T14:30:00Z
  gaps_closed:
    - "Host traversal bug: rootFolder.childEntity[0].host[0] replaced with self.compute_resource.host[0] in create_vm, create_vm_custom, deploy_ovf, deploy_ova (plan 02-06)"
    - "vm_folder type bug: host_system.vm (VirtualMachine[] list) replaced with self.datacenter_obj.vmFolder (vim.Folder) in create_vm, create_vm_custom, and ImportVApp calls (plan 02-06)"
    - "self.compute_resource stored in _connect_vcenter for clean call-site access (plan 02-06)"
    - "clone_vm CloneVM_Task (vCenter-only API) replaced with ovftool subprocess vi:// transfer (plan 02-07)"
    - "Dockerfile updated with ovftool installation comment block (plan 02-07)"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "deploy_ovf / deploy_ova against a live standalone ESXi host"
    expected: "Deployment completes without AttributeError or NotSupported; VM appears in inventory under datacenter vmFolder"
    why_human: "self.compute_resource.host[0] indexing (assumes one ComputeResource, one host) requires live ESXi to validate"
  - test: "clone_vm with ovftool installed on the server host"
    expected: "Clone completes within 600s; cloned VM appears in ESXi inventory with specified new name"
    why_human: "ovftool subprocess and vi:// URL authentication require live ESXi and ovftool binary on PATH"
  - test: "clone_vm without ovftool on PATH"
    expected: "Tool returns RuntimeError with message 'ovftool not found on PATH' and install instructions"
    why_human: "Cannot install/uninstall ovftool in automated verification environment"
  - test: "upload_file_to_datastore with ha-datacenter dcPath"
    expected: "File upload succeeds with dcPath=ha-datacenter; no HTTP 404"
    why_human: "ESXi pseudo-datacenter name behavior cannot be verified without a live host"
---

# Phase 2: Tool Changes Verification Report

**Phase Goal:** Make all 31 MCP tools work correctly against a standalone ESXi host (not vCenter) by removing vCenter-only tools and rewriting ESXi-incompatible operations.
**Verified:** 2026-03-03T23:30:00Z
**Status:** passed
**Re-verification:** Yes — third pass, incorporating plans 02-06 and 02-07 which were executed after the previous VERIFICATION.md (2026-03-03T14:30:00Z).

## Re-verification Summary

The previous VERIFICATION.md (after plan 02-05) reported `status: passed`. However, UAT revealed two additional runtime bugs that required further gap closure plans:

**Plan 02-06 — Host traversal fix (commits da5968d, 5d61e49, db4f041, 83bf306):**
The previous verification incorrectly marked SC2 and SC3 as VERIFIED — it recorded the old `rootFolder.childEntity[0].host[0]` and `host_system.vm` patterns as correct, but these caused `AttributeError` at runtime (`childEntity[0]` is a `vim.Datacenter` with no `.host` attribute) and `NotSupported` from `CreateVM_Task`/`ImportVApp` (because `host_system.vm` is a `VirtualMachine[]` list, not a `vim.Folder`). Plan 02-06 stored `self.compute_resource` in `_connect_vcenter` and fixed all four affected methods.

**Plan 02-07 — clone_vm ovftool rewrite (commits df96a2c, 7f4c2ff):**
`CloneVM_Task` is a vCenter-only API that always returns `NotSupported` on standalone ESXi. `clone_vm` was rewritten to use VMware's `ovftool` CLI via `vi://` → `vi://` subprocess transfer. The tool remains registered; it raises `RuntimeError` with install instructions if ovftool is not on PATH.

This re-verification confirms both sets of changes are in place, all 6 Phase 2 requirements are satisfied, and no regressions were introduced.

## Goal Achievement

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| RMVL-01 | 02-01 | `list_datastore_clusters` removed — vCenter-only StoragePod | SATISFIED | Zero occurrences of `list_datastore_clusters`/`StoragePod` across all three server files; tool registry at 30 entries (30 Tool() definitions, 30 handler map lambdas) |
| RWRT-01 | 02-02, 02-06 | `create_vm` rewritten for ESXi host folder and resource pool | SATISFIED | Lines 518-519: `host_system = self.compute_resource.host[0]`; `vm_folder = self.datacenter_obj.vmFolder`; CreateVM_Task on line 521 receives a proper vim.Folder |
| RWRT-02 | 02-02, 02-07 | `clone_vm` rewritten for ESXi-compatible operation | SATISFIED | Lines 534-579: ovftool subprocess; `shutil.which` check; vi:// URLs using `self.config.esxi_host`; no `CloneVM_Task`/`template_vm.Clone`; tool still registered at mcp_server.py lines 40 and 358 |
| RWRT-03 | 02-02, 02-06 | `create_vm_custom` rewritten for ESXi-compatible placement | SATISFIED | Lines 656-657: `host_system = self.compute_resource.host[0]`; `vm_folder = self.datacenter_obj.vmFolder` |
| RWRT-04 | 02-03, 02-06 | `deploy_ovf` and `deploy_ova` verified for standalone ESXi; datacenter/cluster removed | SATISFIED | deploy_ovf lines 1084-1086: `host_system = self.compute_resource.host[0]`; `ImportVApp(import_spec.importSpec, self.datacenter_obj.vmFolder, host=host_system)`. deploy_ova lines 1201-1203: identical pattern |
| RWRT-05 | 02-04, 02-05 | Remaining tools with datacenter/cluster references updated to ESXi equivalents | SATISFIED | `ha-datacenter` literal at line 997; `_build_traversal_spec` returns `[folder_to_child]` only (line 1383); `_connect_vcenter` lines 47 and 54 use `self.config.esxi_host`; zero `vcenter_host` attribute accesses remain |

**Score:** 6/6 requirements satisfied

**Orphaned requirements:** None. All 6 Phase 2 requirement IDs (RMVL-01, RWRT-01 through RWRT-05) appear in plan frontmatter and are accounted for. REQUIREMENTS.md traceability table marks all 6 as Complete for Phase 2.

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `list_datastore_clusters` is absent from the MCP tool registry | VERIFIED | Zero grep matches across vmware_manager.py, mcp_server.py, tools.py |
| 2 | `create_vm` uses `self.compute_resource.host[0]` and `self.datacenter_obj.vmFolder` | VERIFIED | Lines 518-519 confirmed; no `rootFolder.childEntity` or `host_system.vm` in method body |
| 3 | `create_vm_custom` uses `self.compute_resource.host[0]` and `self.datacenter_obj.vmFolder` | VERIFIED | Lines 656-657 confirmed |
| 4 | `deploy_ovf` calls `ImportVApp(importSpec, self.datacenter_obj.vmFolder, host=host_system)` | VERIFIED | Lines 1084-1086 confirmed |
| 5 | `deploy_ova` calls `ImportVApp(importSpec, self.datacenter_obj.vmFolder, host=host_system)` | VERIFIED | Lines 1201-1203 confirmed |
| 6 | `clone_vm` uses ovftool subprocess instead of CloneVM_Task | VERIFIED | Lines 534-579: shutil.which, subprocess.run with timeout=600, vi:// URLs; zero functional `CloneVM_Task` references |
| 7 | `clone_vm` raises RuntimeError with install instructions when ovftool not on PATH | VERIFIED | Lines 540-544: `shutil.which("ovftool")` guard raises `RuntimeError("ovftool not found on PATH...")` |
| 8 | `self.compute_resource` stored in `_connect_vcenter` at line 97 | VERIFIED | Line 97: `self.compute_resource = compute_resource` immediately after `self.resource_pool` assignment at line 96 |
| 9 | `upload_file_to_datastore` uses `"ha-datacenter"` literal for dcPath | VERIFIED | Line 997: `"dcPath": "ha-datacenter"` with explanatory comment |
| 10 | `_build_traversal_spec` returns only `[folder_to_child]`; no datacenter traversal specs | VERIFIED | Line 1383: `return [folder_to_child]`; no `dcToVmFolder`/`dcToHostFolder` variables |
| 11 | `_connect_vcenter` uses `self.config.esxi_host` at both SSL and standard connection paths | VERIFIED | Lines 47 and 54 confirmed; zero `vcenter_host` attribute accesses in vmware_manager.py |
| 12 | Server module imports without error | VERIFIED | `python3 -c "from esxi_mcp_server.vmware_manager import VMwareManager; print('ok')"` outputs `ok` |
| 13 | Dockerfile contains ovftool installation comment block | VERIFIED | Lines 35-41: 5 comment lines covering download URL, COPY instruction, and chmod |

**Score:** 13/13 truths verified; 4 flagged for human follow-up due to live-host dependency

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `esxi_mcp_server/vmware_manager.py` | All rewrites applied: self.compute_resource at line 97; create_vm/create_vm_custom lines 518-519/656-657; deploy_ovf/deploy_ova lines 1084-1086/1201-1203; clone_vm ovftool lines 534-579; ha-datacenter line 997; _build_traversal_spec line 1383; esxi_host lines 47,54 | VERIFIED | All patterns confirmed; module imports cleanly |
| `esxi_mcp_server/mcp_server.py` | list_datastore_clusters removed; clone_vm registered; 30 tools total | VERIFIED | 30 Tool() definitions, 30 handler lambdas; clone_vm at lines 40 and 358; no list_datastore_clusters |
| `esxi_mcp_server/tools.py` | list_datastore_clusters removed; clone_vm delegation present | VERIFIED | clone_vm delegation at lines 30-33; no list_datastore_clusters |
| `esxi_mcp_server/config.py` | esxi_host field; vcenter_user/vcenter_password present (Phase 3 renames these); required_keys includes esxi_host | VERIFIED | `esxi_host: str` line 12; `vcenter_user`/`vcenter_password` lines 13-14; required_keys at line 78 |
| `Dockerfile` | ovftool comment block before Python packages copy step | VERIFIED | Lines 35-41 with 5-line comment block |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `_connect_vcenter` (line 97) | create_vm, create_vm_custom, deploy_ovf, deploy_ova call sites | `self.compute_resource = compute_resource` | VERIFIED | 4 call sites confirmed: `self.compute_resource.host[0]` at lines 518, 656, 1084, 1201 |
| `create_vm` vm_folder (line 519) | `CreateVM_Task` (line 521) | `vm_folder = self.datacenter_obj.vmFolder` | VERIFIED | Line 521: `task = vm_folder.CreateVM_Task(config=vm_spec, pool=self.resource_pool)` |
| `create_vm_custom` vm_folder (line 657) | `CreateVM_Task` (line 660) | `vm_folder = self.datacenter_obj.vmFolder` | VERIFIED | Line 660 uses vm_folder from line 657 |
| `deploy_ovf` (lines 1084-1086) | `ImportVApp` with vim.Folder | `self.datacenter_obj.vmFolder, host=host_system` | VERIFIED | Signature confirmed; host= keyword passes host placement hint |
| `deploy_ova` (lines 1201-1203) | `ImportVApp` with vim.Folder | `self.datacenter_obj.vmFolder, host=host_system` | VERIFIED | Identical to deploy_ovf pattern |
| `clone_vm` shutil.which (line 539) | subprocess.run (line 565) | `ovftool_path` variable | VERIFIED | Line 565 uses `ovftool_path` from line 539; RuntimeError guard at lines 540-544 |
| `clone_vm` vi:// URLs (lines 546-553) | `self.config.esxi_host` | `self.config.vcenter_user`, `self.config.vcenter_password`, `self.config.esxi_host` | VERIFIED | All three are valid Config fields (vcenter_user/vcenter_password renamed in Phase 3) |
| `upload_file_to_datastore` params dict | `"ha-datacenter"` literal | `"dcPath": "ha-datacenter"` | VERIFIED | Line 997 confirmed |
| `_build_traversal_spec` return | caller at line 1296 | `return [folder_to_child]` | VERIFIED | Line 1383 return; line 1296: `selectSet=self._build_traversal_spec()` |

### Commit Verification

| Commit | Plan | Description | In git log |
|--------|------|-------------|-----------|
| `da5968d` | 02-06 | feat: store self.compute_resource in _connect_vcenter | Yes |
| `5d61e49` | 02-06 | fix: host_system and vm_folder in create_vm and create_vm_custom | Yes |
| `db4f041` | 02-06 | fix: host_system and ImportVApp folder in deploy_ovf and deploy_ova | Yes |
| `83bf306` | 02-06 | fix: clone_vm fallback path (moot — 02-07 replaced clone_vm entirely) | Yes |
| `df96a2c` | 02-07 | feat: rewrite clone_vm to use ovftool subprocess | Yes |
| `7f4c2ff` | 02-07 | chore: add ovftool installation comment to Dockerfile | Yes |

### Anti-Patterns Found

None. No TODO/FIXME/XXX/HACK/PLACEHOLDER comments in modified files. No stub return values. No empty handlers. The `CloneVM_Task` mention in `clone_vm`'s docstring (`"ESXi-compatible; CloneVM_Task requires vCenter"`) is explanatory text in a string literal, not executable code — not a stub.

### Human Verification Required

#### 1. deploy_ovf / deploy_ova Against Live ESXi

**Test:** Point a running server at a standalone ESXi host and deploy a simple OVF/OVA file.
**Expected:** Deployment completes without AttributeError or NotSupported errors; new VM appears in ESXi inventory under the datacenter vmFolder.
**Why human:** Requires live ESXi. The `self.compute_resource.host[0]` indexing assumes exactly one ComputeResource containing one host — this assumption cannot be validated without a running vSphere environment. Also verifies that `datacenter_obj.vmFolder` is a writable vim.Folder on ESXi.

#### 2. clone_vm With ovftool on PATH Against Live ESXi

**Test:** Call `clone_vm` with a known source VM name and a new name, with ovftool installed on the server host.
**Expected:** Clone completes within 600 seconds; cloned VM appears in ESXi inventory with the specified new name.
**Why human:** Requires live ESXi and ovftool binary. Also validates vi:// URL authentication and `--noSSLVerify` handling with ESXi self-signed TLS certificates.

#### 3. clone_vm Without ovftool Installed

**Test:** Call `clone_vm` when ovftool is not on PATH.
**Expected:** Tool returns a clear error containing "ovftool not found on PATH" with install instructions.
**Why human:** Cannot install/uninstall ovftool in the automated verification environment.

#### 4. upload_file_to_datastore With ha-datacenter dcPath

**Test:** Upload a file to an ESXi datastore via the MCP tool.
**Expected:** Upload succeeds; no HTTP 404 on the datastore URL with `dcPath: ha-datacenter`.
**Why human:** ESXi pseudo-datacenter naming behavior cannot be verified without a live host. Code comment at line 996 notes that removing dcPath entirely may be required if a 404 occurs.

## Gaps Summary

No gaps. All 6 Phase 2 requirements (RMVL-01, RWRT-01 through RWRT-05) are satisfied in the actual codebase. Plans 02-06 and 02-07 resolved the runtime bugs discovered during UAT (host traversal AttributeError, vm_folder type mismatch, clone_vm vCenter-only API). Phase 2 goal is achieved: every MCP tool either works correctly against a standalone ESXi host at the code level or has been removed. Four items remain for human verification against a live ESXi host but do not block phase completion.

---
_Verified: 2026-03-03T23:30:00Z_
_Verifier: Claude (gsd-verifier)_
