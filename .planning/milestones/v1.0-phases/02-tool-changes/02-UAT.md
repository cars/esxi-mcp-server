---
status: diagnosed
phase: 02-tool-changes
source: [02-06-SUMMARY.md, 02-07-SUMMARY.md]
started: 2026-03-03T16:00:00Z
updated: 2026-03-03T16:15:00Z
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
  root_cause: "vim.vm.ConfigSpec never sets .files — configSpec.files is null when CreateVM_Task is called. ESXi requires vim.vm.FileInfo(vmPathName='[datastore-name]') on the spec."
  artifacts:
    - path: "esxi_mcp_server/vmware_manager.py"
      lines: "467"
      issue: "vm_spec = vim.vm.ConfigSpec(...) never assigns vm_spec.files; fix: add vm_spec.files = vim.vm.FileInfo(vmPathName=f'[{datastore_obj.name}]') after line 467"
  missing:
    - "vm_spec.files = vim.vm.FileInfo(vmPathName=f'[{datastore_obj.name}]') in create_vm after ConfigSpec construction"
  debug_session: ".planning/debug/create-vm-vmpathname-invalid.md"

- truth: "create_vm_custom completes successfully against a standalone ESXi host"
  status: failed
  reason: "User reported: vmodl.fault.InvalidArgument: A specified parameter was not correct: configSpec.files.vmPathName — vSphere API expects [datastore-name] or [datastore-name] folder/file.vmx format"
  severity: major
  test: 2
  root_cause: "Identical to create_vm: vim.vm.ConfigSpec at line 605 never sets .files. Fix is the same one-liner after ConfigSpec construction."
  artifacts:
    - path: "esxi_mcp_server/vmware_manager.py"
      lines: "605"
      issue: "vm_spec = vim.vm.ConfigSpec(...) never assigns vm_spec.files; fix: add vm_spec.files = vim.vm.FileInfo(vmPathName=f'[{datastore_obj.name}]') after line 605"
  missing:
    - "vm_spec.files = vim.vm.FileInfo(vmPathName=f'[{datastore_obj.name}]') in create_vm_custom after ConfigSpec construction"
  debug_session: ".planning/debug/create-vm-custom-vmpathname.md"

- truth: "clone_vm successfully clones a VM on a standalone ESXi host via ovftool"
  status: failed
  reason: "User reported: ovftool clone failed (exit 1) with empty error output — ovftool executes but exits with code 1; stderr/stdout not surfaced in the error message, making the actual failure reason invisible"
  severity: major
  test: 5
  root_cause: "Three bugs: (1) ovftool writes errors to stdout not stderr — exception only includes result.stderr which is empty; (2) dest_url includes /{new_name} suffix which ESXi interprets as a non-existent datacenter path — should be vi://user:pass@host with no path; (3) missing --acceptAllEuals causes interactive hang in non-interactive subprocess."
  artifacts:
    - path: "esxi_mcp_server/vmware_manager.py"
      lines: "550-553"
      issue: "dest_url ends with /{new_name} — wrong for standalone ESXi; should be vi://user:pass@host with no path component"
    - path: "esxi_mcp_server/vmware_manager.py"
      lines: "574-576"
      issue: "Exception only includes result.stderr which is empty; ovftool errors go to stdout — must include result.stdout"
    - path: "esxi_mcp_server/vmware_manager.py"
      lines: "555"
      issue: "cmd list missing --acceptAllEulas — ovftool prompts interactively and hangs until timeout"
  missing:
    - "Fix dest_url to remove /{new_name}: dest_url = f'vi://{user}:{pass}@{host}'"
    - "Fix error raise to include stdout: combined = (result.stdout + result.stderr).strip(); raise Exception(f'ovftool clone failed (exit {result.returncode}): {combined}')"
    - "Add --acceptAllEulas to cmd list"
  debug_session: ".planning/debug/clone-vm-silent-failure.md"
