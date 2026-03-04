---
phase: 02-tool-changes
verified: 2026-03-04T01:00:00Z
status: human_needed
score: 6/6 requirements satisfied
re_verification: true
  previous_status: passed
  previous_score: 6/6 requirements satisfied
  previous_verified: 2026-03-03T23:30:00Z
  gaps_closed:
    - "vim.vm.FileInfo added to create_vm and create_vm_custom ConfigSpecs (plan 02-08, commit 5bfa111)"
    - "clone_vm dest_url trailing path removed — vi://user:pass@host with no /{new_name} (plan 02-08, commit 128f6c1)"
    - "clone_vm --acceptAllEulas added to ovftool cmd list — prevents interactive hang (plan 02-08, commit 128f6c1)"
    - "clone_vm error handler now uses combined = result.stdout + result.stderr — surfaces ovftool diagnostics (plan 02-08, commit 128f6c1)"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "create_vm against live standalone ESXi with vim.vm.FileInfo set"
    expected: "VM created without vmodl.fault.InvalidArgument on configSpec.files.vmPathName"
    why_human: "ESXi CreateVM_Task FileInfo behavior requires live ESXi host; cannot mock pyVmomi fault behavior"
  - test: "create_vm_custom against live standalone ESXi with vim.vm.FileInfo set"
    expected: "Custom VM created without vmodl.fault.InvalidArgument"
    why_human: "Same reason as create_vm — live ESXi required"
  - test: "clone_vm with ovftool installed, against live ESXi, using corrected dest_url"
    expected: "Clone completes within 600s; VM appears in ESXi inventory with new name"
    why_human: "ovftool subprocess requires live ESXi host and ovftool binary on PATH; vi:// URL authentication cannot be tested offline"
  - test: "clone_vm without ovftool on PATH"
    expected: "RuntimeError raised with message containing 'ovftool not found on PATH'"
    why_human: "Cannot install/uninstall ovftool in automated environment"
  - test: "deploy_ovf and deploy_ova against live standalone ESXi"
    expected: "Deployment completes without AttributeError or NotSupported; VM appears under datacenter vmFolder"
    why_human: "self.compute_resource.host[0] indexing and ImportVApp behavior require live ESXi"
  - test: "upload_file_to_datastore with ha-datacenter dcPath"
    expected: "File upload succeeds; no HTTP 404 on the datastore URL"
    why_human: "ESXi pseudo-datacenter naming behavior requires live host"
---

# Phase 2: Tool Changes Verification Report

**Phase Goal:** Every MCP tool exposed by the server either works correctly against a standalone ESXi host or has been removed.
**Verified:** 2026-03-04T01:00:00Z
**Status:** human_needed
**Re-verification:** Yes — fourth pass, incorporating plan 02-08 (vim.vm.FileInfo + clone_vm ovftool fixes) executed after the previous VERIFICATION.md (2026-03-03T23:30:00Z).

## Re-verification Summary

The previous VERIFICATION.md (after plans 02-06 and 02-07) reported `status: passed`. However, UAT (02-UAT.md, commit 58fc2d4) revealed three additional runtime bugs requiring plan 02-08:

**Plan 02-08 — FileInfo + clone_vm ovftool fixes (commits 5bfa111, 128f6c1):**

1. `create_vm` and `create_vm_custom` were raising `vmodl.fault.InvalidArgument` on `configSpec.files.vmPathName` because ESXi's `CreateVM_Task` requires `configSpec.files` to be set. Plan 02-08 added `vm_spec.files = vim.vm.FileInfo(vmPathName=f"[{datastore_obj.name}]")` to both methods.

2. `clone_vm` dest_url had a trailing `/{new_name}` path component — ESXi interprets path as a datacenter name, causing lookup failure on standalone hosts. Removed.

3. `clone_vm` was missing `--acceptAllEulas` in the ovftool cmd, causing it to hang interactively until the 600s timeout. Added.

4. `clone_vm` error handler was reporting empty error messages because ovftool writes diagnostics to stdout, not stderr. Fixed by combining both streams: `combined = result.stdout + result.stderr`.

All four fixes are confirmed in the actual codebase. All 6 Phase 2 requirements remain satisfied. Automated checks are complete; 6 items require human verification against a live ESXi host before UAT can be closed.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `list_datastore_clusters` is absent from the MCP tool registry | VERIFIED | Zero grep matches across vmware_manager.py, mcp_server.py, tools.py |
| 2 | `create_vm` uses `self.compute_resource.host[0]` and `self.datacenter_obj.vmFolder` | VERIFIED | Lines 519-520 confirmed |
| 3 | `create_vm` ConfigSpec includes `vim.vm.FileInfo(vmPathName='[datastore-name]')` | VERIFIED | Line 468: `vm_spec.files = vim.vm.FileInfo(vmPathName=f"[{datastore_obj.name}]")` |
| 4 | `create_vm_custom` uses `self.compute_resource.host[0]` and `self.datacenter_obj.vmFolder` | VERIFIED | Lines 660-661 confirmed |
| 5 | `create_vm_custom` ConfigSpec includes `vim.vm.FileInfo(vmPathName='[datastore-name]')` | VERIFIED | Line 609: `vm_spec.files = vim.vm.FileInfo(vmPathName=f"[{datastore_obj.name}]")` |
| 6 | `clone_vm` uses ovftool subprocess instead of CloneVM_Task | VERIFIED | Lines 534-582: shutil.which, subprocess.run with timeout=600; CloneVM_Task appears only in docstring |
| 7 | `clone_vm` raises RuntimeError when ovftool not on PATH | VERIFIED | Lines 540-544: shutil.which guard raises RuntimeError with install instructions |
| 8 | `clone_vm` dest_url is `vi://user:pass@host` with no trailing path | VERIFIED | Lines 551-554: no `/{new_name}`; confirmed by commit 128f6c1 diff |
| 9 | `clone_vm` cmd list includes `--acceptAllEulas` | VERIFIED | Line 559: `"--acceptAllEulas"` present after `"--noSSLVerify"` |
| 10 | `clone_vm` error handler uses combined stdout+stderr | VERIFIED | Line 577: `combined = (result.stdout + result.stderr).strip()`; line 579 raises with combined |
| 11 | `deploy_ovf` calls `ImportVApp(importSpec, self.datacenter_obj.vmFolder, host=host_system)` | VERIFIED | Lines 1088-1090 confirmed |
| 12 | `deploy_ova` calls `ImportVApp(importSpec, self.datacenter_obj.vmFolder, host=host_system)` | VERIFIED | Lines 1205-1207 confirmed |
| 13 | `self.compute_resource` stored in `_connect_vcenter` at line 97 | VERIFIED | Line 97: `self.compute_resource = compute_resource` |
| 14 | `upload_file_to_datastore` uses `"ha-datacenter"` literal for dcPath | VERIFIED | Line 1001: `"dcPath": "ha-datacenter"` with explanatory comment at line 999-1000 |
| 15 | `_build_traversal_spec` returns only `[folder_to_child]`; no datacenter traversal specs | VERIFIED | Line 1387: `return [folder_to_child]`; no dcToVmFolder/dcToHostFolder variables |
| 16 | `_connect_vcenter` uses `self.config.esxi_host` at both SSL and standard connection paths | VERIFIED | Lines 47 and 54 confirmed; zero `vcenter_host` attribute accesses remain |
| 17 | Module parses without syntax errors | VERIFIED | `ast.parse()` returns clean; `python3 -c "from esxi_mcp_server.vmware_manager import VMwareManager"` outputs ok |

**Score:** 17/17 truths verified; 6 flagged for human follow-up due to live-host dependency

### Notes on ROADMAP Success Criteria vs. Actual Implementation

The ROADMAP (written before UAT) stated two success criteria whose letter differs from implementation:

**SC3 — "clone_vm tool removed":** Plans 02-07 and 02-08 instead rewrote clone_vm using ovftool subprocess (a superior outcome — the tool is retained and functional on ESXi). The tool is registered at mcp_server.py lines 40 and 358. The goal intent — "CloneVM_Task will not cause a NotSupported error on standalone ESXi" — is satisfied.

**SC5 — "No remaining tool references vim.Datacenter, vim.ClusterComputeResource, or vim.dvs.*":** These types appear at lines 68, 75 (`vim.Datacenter`), 84 (`vim.ClusterComputeResource`), and 282, 506, 511, 648, 652 (`vim.dvs.*`). Context:
- `vim.Datacenter` and `vim.ClusterComputeResource` at lines 67-95 are in `_connect_vcenter()` for datacenter and compute resource resolution. On standalone ESXi, the `else` branch (lines 73-75, 92-93) finds the ha-datacenter and the lone ComputeResource. These references are necessary for ESXi compatibility.
- `vim.dvs.*` references at lines 282, 506, 511, 648, 652 are defensive `isinstance` type checks. On standalone ESXi, networks are standard `vim.Network` objects — the DVS branch is never taken. Presence of these checks does not block ESXi functionality.

Both are non-blocking for phase goal achievement.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `esxi_mcp_server/vmware_manager.py` | vim.vm.FileInfo at lines 468, 609; clone_vm dest_url no path (lines 551-554); --acceptAllEulas (line 559); combined error (line 577); self.compute_resource at line 97; create_vm/create_vm_custom/deploy_ovf/deploy_ova host+vmFolder; ha-datacenter line 1001; _build_traversal_spec line 1387; esxi_host lines 47, 54 | VERIFIED | All patterns confirmed; syntax clean |
| `esxi_mcp_server/mcp_server.py` | list_datastore_clusters removed; clone_vm registered; 30 tools total | VERIFIED | 30 Tool() definitions; clone_vm at lines 40 and 358; no list_datastore_clusters |
| `esxi_mcp_server/tools.py` | list_datastore_clusters removed; clone_vm delegation present | VERIFIED | clone_vm delegation at lines 30-33; no list_datastore_clusters |
| `esxi_mcp_server/config.py` | esxi_host field; vcenter_user/vcenter_password present | VERIFIED | `esxi_host: str` line 12; required_keys at line 78 includes esxi_host |
| `Dockerfile` | ovftool installation comment block | VERIFIED | Previously confirmed in plan 02-07 (commit 7f4c2ff); not re-checked this pass (unchanged) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `create_vm` ConfigSpec (line 467) | `CreateVM_Task` (line 523) | `vm_spec.files = vim.vm.FileInfo(vmPathName=...)` at line 468 | VERIFIED | FileInfo set before CreateVM_Task call |
| `create_vm_custom` ConfigSpec (line 608) | `CreateVM_Task` (line 663) | `vm_spec.files = vim.vm.FileInfo(vmPathName=...)` at line 609 | VERIFIED | FileInfo set before CreateVM_Task call |
| `_connect_vcenter` (line 97) | create_vm, create_vm_custom, deploy_ovf, deploy_ova | `self.compute_resource = compute_resource` | VERIFIED | 4 call sites: `self.compute_resource.host[0]` at lines 519, 660, 1088, 1205 |
| `clone_vm` shutil.which (line 540) | subprocess.run (line 567) | `ovftool_path` variable | VERIFIED | Line 567 uses ovftool_path; guard at lines 541-545 |
| `clone_vm` dest_url (lines 551-554) | subprocess cmd (line 562) | no trailing path — vi://user:pass@host | VERIFIED | Line 553 ends at `{self.config.esxi_host}` with no further path |
| `clone_vm` cmd list (line 559) | subprocess.run | `"--acceptAllEulas"` after `"--noSSLVerify"` | VERIFIED | Line 559 confirmed |
| `clone_vm` error handler (line 577) | Exception message (line 579) | `combined = result.stdout + result.stderr` | VERIFIED | Both stdout and stderr captured; raised with exit code |
| `deploy_ovf` (lines 1088-1090) | ImportVApp | `self.datacenter_obj.vmFolder, host=host_system` | VERIFIED | Correct vim.Folder and host placement hint |
| `deploy_ova` (lines 1205-1207) | ImportVApp | `self.datacenter_obj.vmFolder, host=host_system` | VERIFIED | Identical to deploy_ovf pattern |
| `upload_file_to_datastore` params dict (line 1001) | HTTP PUT | `"dcPath": "ha-datacenter"` | VERIFIED | Line 1001 confirmed |
| `_build_traversal_spec` return (line 1387) | caller at line 1300 | `return [folder_to_child]` | VERIFIED | No vCenter datacenter traversal specs |

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| RMVL-01 | 02-01 | `list_datastore_clusters` removed — vCenter-only StoragePod | SATISFIED | Zero grep matches in all three server files; 30 Tool() definitions in mcp_server.py |
| RWRT-01 | 02-02, 02-06, 02-08 | `create_vm` rewritten for ESXi host folder and resource pool | SATISFIED | Lines 519-520: compute_resource.host[0], datacenter_obj.vmFolder; line 468: vim.vm.FileInfo |
| RWRT-02 | 02-02, 02-07, 02-08 | `clone_vm` rewritten for ESXi-compatible operation (ovftool) | SATISFIED | Lines 534-582: ovftool subprocess; no CloneVM_Task; dest_url no path; --acceptAllEulas; combined error |
| RWRT-03 | 02-02, 02-06, 02-08 | `create_vm_custom` rewritten for ESXi-compatible placement | SATISFIED | Lines 660-661: compute_resource.host[0], datacenter_obj.vmFolder; line 609: vim.vm.FileInfo |
| RWRT-04 | 02-03, 02-06 | `deploy_ovf` and `deploy_ova` verified for standalone ESXi | SATISFIED | Lines 1088-1090, 1205-1207: ImportVApp with datacenter_obj.vmFolder and host_system |
| RWRT-05 | 02-04, 02-05 | Remaining tools with datacenter/cluster references updated | SATISFIED | ha-datacenter literal line 1001; _build_traversal_spec [folder_to_child] line 1387; esxi_host lines 47, 54 |

**Score:** 6/6 requirements satisfied

**Orphaned requirements:** None. All 6 Phase 2 requirement IDs (RMVL-01, RWRT-01 through RWRT-05) appear in plan frontmatter. REQUIREMENTS.md traceability table marks all 6 as Complete for Phase 2. No Phase 2 requirements in REQUIREMENTS.md are unaccounted for.

### Commit Verification

| Commit | Plan | Description | In git log |
|--------|------|-------------|-----------|
| `da5968d` | 02-06 | feat: store self.compute_resource in _connect_vcenter | Yes |
| `5d61e49` | 02-06 | fix: host_system and vm_folder in create_vm and create_vm_custom | Yes |
| `db4f041` | 02-06 | fix: host_system and ImportVApp folder in deploy_ovf and deploy_ova | Yes |
| `83bf306` | 02-06 | fix: clone_vm fallback path (superseded by plan 02-07) | Yes |
| `df96a2c` | 02-07 | feat: rewrite clone_vm to use ovftool subprocess | Yes |
| `7f4c2ff` | 02-07 | chore: add ovftool installation comment to Dockerfile | Yes |
| `5bfa111` | 02-08 | fix: add vim.vm.FileInfo to create_vm and create_vm_custom ConfigSpecs | Yes |
| `128f6c1` | 02-08 | fix: fix clone_vm ovftool dest_url, --acceptAllEulas, and error output | Yes |

### Anti-Patterns Found

None. No TODO/FIXME/XXX/HACK/PLACEHOLDER comments in modified files. No stub returns. No empty handlers. The `CloneVM_Task` mention at line 536 is in a docstring explaining why ovftool is used — not executable code.

### Human Verification Required

#### 1. create_vm Against Live ESXi (vim.vm.FileInfo)

**Test:** Call `create_vm` with a name, CPU count, memory, and datastore; point the server at a standalone ESXi host.
**Expected:** VM is created without raising `vmodl.fault.InvalidArgument` on `configSpec.files.vmPathName`; new VM appears in ESXi inventory.
**Why human:** ESXi CreateVM_Task FileInfo requirement cannot be validated without a running ESXi host. Cannot mock pyVmomi fault behavior in an offline environment.

#### 2. create_vm_custom Against Live ESXi (vim.vm.FileInfo)

**Test:** Call `create_vm_custom` with name, cpus, memory_mb, and disk_size_gb parameters.
**Expected:** VM created without `vmodl.fault.InvalidArgument`; VM appears in inventory with specified configuration.
**Why human:** Same reason as create_vm — live ESXi required.

#### 3. clone_vm With ovftool Against Live ESXi (corrected dest_url)

**Test:** Call `clone_vm` with source VM name and new name, with ovftool on PATH and server pointed at standalone ESXi.
**Expected:** Clone completes within 600s; cloned VM appears in inventory with new name; no "datacenter not found" error from the removed trailing path.
**Why human:** Requires live ESXi and ovftool binary. vi:// URL auth and --acceptAllEulas behavior require actual ovftool subprocess execution.

#### 4. clone_vm Without ovftool on PATH

**Test:** Call `clone_vm` when ovftool is not installed.
**Expected:** RuntimeError raised with message containing "ovftool not found on PATH" and install instructions.
**Why human:** Cannot install/uninstall ovftool in the automated verification environment.

#### 5. deploy_ovf / deploy_ova Against Live ESXi

**Test:** Deploy a small OVF/OVA file to a standalone ESXi host.
**Expected:** Deployment completes without AttributeError or NotSupported; VM appears in inventory under datacenter vmFolder.
**Why human:** `self.compute_resource.host[0]` indexing assumes one ComputeResource with one host — cannot validate without running vSphere environment. ImportVApp behavior with vim.Folder requires live ESXi.

#### 6. upload_file_to_datastore With ha-datacenter dcPath

**Test:** Upload a file to an ESXi datastore via the MCP tool.
**Expected:** Upload succeeds; no HTTP 404 on the datastore URL with `dcPath: ha-datacenter`.
**Why human:** ESXi pseudo-datacenter naming behavior requires a live host. Code comment at line 999-1000 notes that removing dcPath entirely may be required if a 404 occurs.

## Gaps Summary

No gaps. All 6 Phase 2 requirements (RMVL-01, RWRT-01 through RWRT-05) are satisfied in the actual codebase. Plan 02-08 resolved the three UAT-diagnosed bugs (missing vim.vm.FileInfo on CreateVM_Task ConfigSpec in create_vm and create_vm_custom; wrong dest_url, missing --acceptAllEulas, and empty error output in clone_vm). Phase 2 goal is achieved: every MCP tool either works correctly against a standalone ESXi host at the code level or has been removed. Six items remain for human verification against a live ESXi host but do not block phase completion.

---
_Verified: 2026-03-04T01:00:00Z_
_Verifier: Claude (gsd-verifier)_
