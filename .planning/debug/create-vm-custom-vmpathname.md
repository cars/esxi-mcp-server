---
status: resolved
trigger: "Investigate root cause of vmodl.fault.InvalidArgument: configSpec.files.vmPathName in create_vm_custom"
created: 2026-03-03T00:00:00Z
updated: 2026-03-03T00:00:00Z
---

## Current Focus

hypothesis: ConfigSpec is missing a `files` attribute entirely; vmPathName is never set, so ESXi rejects the spec with InvalidArgument
test: Read create_vm_custom and create_vm completely
expecting: Neither function sets configSpec.files.vmPathName
next_action: COMPLETE - root cause confirmed

## Symptoms

expected: CreateVM_Task succeeds and the VM is created on the datastore
actual: vmodl.fault.InvalidArgument fault pointing to configSpec.files.vmPathName
errors: "vmodl.fault.InvalidArgument: configSpec.files.vmPathName"
reproduction: Call create_vm_custom (or create_vm) against a standalone ESXi host
started: Always broken on standalone ESXi (vCenter may be more permissive)

## Eliminated

- hypothesis: vmPathName is set but formatted incorrectly (e.g., wrong brackets or path separators)
  evidence: grep for vmPathName, VirtualMachineFileInfo, and configSpec.files all return no matches — the field is never set at all
  timestamp: 2026-03-03

## Evidence

- timestamp: 2026-03-03
  checked: vmware_manager.py lines 580-668 (create_vm_custom)
  found: vim.vm.ConfigSpec is constructed on line 605 with only name, memoryMB, numCPUs, guestId. No `files` attribute is ever assigned.
  implication: ESXi requires configSpec.files.vmPathName to know where to store the .vmx file. Without it, ESXi raises InvalidArgument.

- timestamp: 2026-03-03
  checked: vmware_manager.py lines 445-532 (create_vm)
  found: Identical omission — configSpec is built the same way, no `files` attribute.
  implication: Both create_vm and create_vm_custom share the same root cause.

- timestamp: 2026-03-03
  checked: datastore_obj resolution
  found: datastore_obj is a pyVmomi vim.Datastore object. Its .name attribute gives the human-readable datastore name (e.g., "datastore1").
  implication: The correct vmPathName value is "[datastore_name]" — brackets around the datastore name — which tells ESXi to auto-place the .vmx within the datastore's root. Optionally "[datastore_name] vm-name/vm-name.vmx" for explicit placement.

## Resolution

root_cause: |
  Neither create_vm nor create_vm_custom sets configSpec.files (a vim.vm.FileInfo object).
  Standalone ESXi requires configSpec.files.vmPathName to locate the .vmx file.
  vCenter is sometimes permissive and infers it, but ESXi always enforces it.
  The ConfigSpec on line 605 (create_vm_custom) and line 467 (create_vm) never include a `files` attribute.

fix: |
  Add a vim.vm.FileInfo assignment immediately after constructing vm_spec in both functions.
  For standalone ESXi the minimal valid value is "[datastore_name]" (bracket-enclosed datastore name,
  no path — ESXi will auto-place the .vmx). The datastore name is available via datastore_obj.name.

  In create_vm (line 467) after the ConfigSpec line:
      vm_spec.files = vim.vm.FileInfo(vmPathName=f"[{datastore_obj.name}]")

  In create_vm_custom (line 605) after the ConfigSpec line:
      vm_spec.files = vim.vm.FileInfo(vmPathName=f"[{datastore_obj.name}]")

  The value passed is currently: (nothing — field absent)
  The correct value is: "[datastore1]"  (where datastore1 is datastore_obj.name)

verification: confirmed by code trace — field is entirely absent, not malformed
files_changed:
  - esxi_mcp_server/vmware_manager.py
