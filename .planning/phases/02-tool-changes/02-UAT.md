---
status: complete
phase: 02-tool-changes
source: [02-06-SUMMARY.md, 02-07-SUMMARY.md]
started: 2026-03-03T16:00:00Z
updated: 2026-03-03T16:10:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. create_vm works on ESXi
expected: Calling `create_vm` against a standalone ESXi host should complete successfully. Uses `self.compute_resource.host[0]` for host placement and `self.datacenter_obj.vmFolder` as the VM folder. No AttributeError or NotSupported error.
result: issue
reported: "vmodl.fault.InvalidArgument: A specified parameter was not correct: configSpec.files.vmPathName — same root cause as create_vm_custom (vmPathName not built in correct [datastore-name] format)"
severity: major

### 2. create_vm_custom works on ESXi
expected: Calling `create_vm_custom` against a standalone ESXi host should complete successfully. Same two-line fix as create_vm: `self.compute_resource.host[0]` + `self.datacenter_obj.vmFolder`. No NotSupported error.
result: issue
reported: "vmodl.fault.InvalidArgument: A specified parameter was not correct: configSpec.files.vmPathName — vSphere API expects [datastore-name] or [datastore-name] folder/file.vmx format"
severity: major

### 3. deploy_ovf works on ESXi
expected: Calling `deploy_ovf` with a valid OVF template should complete. `ImportVApp` now receives `self.datacenter_obj.vmFolder` as the folder argument and `host=host_system` as keyword arg. Host is resolved via `self.compute_resource.host[0]`.
result: pass

### 4. deploy_ova works on ESXi
expected: Calling `deploy_ova` with a valid OVA file should complete. Identical fix to deploy_ovf: `self.compute_resource.host[0]` for host, `self.datacenter_obj.vmFolder` for ImportVApp folder arg.
result: pass

### 5. clone_vm uses ovftool subprocess
expected: Calling `clone_vm` against a standalone ESXi host should use `ovftool` as a subprocess (not `CloneVM_Task`). If ovftool is on PATH it should attempt the clone. If ovftool is not found, it should raise a clear RuntimeError with install instructions — not a vmodl.fault.NotSupported.
result: issue
reported: "ovftool clone failed (exit 1) with empty error output — ovftool is found on PATH and executes but exits with code 1; stderr/stdout not captured or returned properly, making it impossible to diagnose the actual ovftool failure reason"
severity: major

## Summary

total: 5
passed: 2
issues: 3
pending: 0
skipped: 0

## Gaps

- truth: "create_vm completes successfully against a standalone ESXi host"
  status: failed
  reason: "User reported: vmodl.fault.InvalidArgument: A specified parameter was not correct: configSpec.files.vmPathName — vmPathName not built in correct [datastore-name] format"
  severity: major
  test: 1
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "create_vm_custom completes successfully against a standalone ESXi host"
  status: failed
  reason: "User reported: vmodl.fault.InvalidArgument: A specified parameter was not correct: configSpec.files.vmPathName — vSphere API expects [datastore-name] or [datastore-name] folder/file.vmx format"
  severity: major
  test: 2
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "clone_vm successfully clones a VM on a standalone ESXi host via ovftool"
  status: failed
  reason: "User reported: ovftool clone failed (exit 1) with empty error output — ovftool executes but exits with code 1; stderr/stdout not surfaced in the error message, making the actual failure reason invisible"
  severity: major
  test: 5
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
