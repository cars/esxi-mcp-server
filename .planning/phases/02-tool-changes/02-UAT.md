---
status: diagnosed
phase: 02-tool-changes
source: [02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md, 02-04-SUMMARY.md, 02-05-SUMMARY.md]
started: 2026-03-03T14:15:00Z
updated: 2026-03-03T14:15:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Server starts without AttributeError
expected: Start the server pointing at your ESXi host. It should reach the SmartConnect call without raising AttributeError. Previously (before plan 02-05), the server crashed immediately with "AttributeError: 'Config' object has no attribute 'vcenter_host'" because _connect_vcenter() referenced the old field name. Now it should connect (or fail with a real connection error like auth failure / host unreachable — not an AttributeError).
result: pass

### 2. list_datastore_clusters tool is gone
expected: Calling the `list_datastore_clusters` MCP tool should return an error indicating the tool is unknown/not registered — not a result set. The tool registry now has 30 tools; this vCenter-only (vim.StoragePod) tool was removed entirely.
result: pass

### 3. create_vm works on ESXi
expected: Calling `create_vm` against a standalone ESXi host should complete successfully. The method now uses `host_system.vm` (from rootFolder.childEntity[0].host[0]) as the VM folder and CreateContainerView(rootFolder) for datastore/network lookups — no datacenter or cluster objects required.
result: issue
reported: "The listing operations work fine, but VM creation fails. This appears to be an issue with the MCP server's VM creation logic — on a standalone ESXi host (no vCenter cluster), it can't resolve the host/resource pool for placement. The terse 'host' error suggests it's failing during host lookup."
severity: blocker

### 4. clone_vm works on ESXi
expected: Calling `clone_vm` against a standalone ESXi host should complete without referencing datacenter objects. The fallback VM folder is now `host_system.vm` instead of `datacenter_obj.vmFolder`.
result: issue
reported: "vmodl.fault.NotSupported: The operation is not supported on the object."
severity: blocker

### 5. create_vm_custom works on ESXi
expected: Calling `create_vm_custom` against a standalone ESXi host should complete successfully using the same ContainerView(rootFolder) pattern as create_vm — no datacenter_obj or cluster references.
result: issue
reported: "similar error to the clone vm one"
severity: blocker

### 6. deploy_ovf works on ESXi
expected: Calling `deploy_ovf` with a valid OVF template against a standalone ESXi host should complete. The method now uses CreateContainerView(rootFolder, [vim.Datastore]) for datastore, CreateContainerView(rootFolder, [vim.ResourcePool]) for resource pool, and ImportVApp(importSpec, host_system.vm) for folder — no datacenter object.
result: issue
reported: "the same type of host error occurs when trying to run the deploy_ovf"
severity: blocker

### 7. deploy_ova works on ESXi
expected: Calling `deploy_ova` with a valid OVA file against a standalone ESXi host should complete. Uses identical pattern to deploy_ovf: rootFolder ContainerViews + ImportVApp(host_system.vm).
result: issue
reported: "the same host error occurs."
severity: blocker

### 8. upload_file_to_datastore uses ha-datacenter
expected: Calling `upload_file_to_datastore` should use `dcPath: ha-datacenter` (ESXi's built-in pseudo-datacenter name). The upload HTTP request should succeed — not return a 404 or authentication error related to the dcPath parameter.
result: pass
reason: "Static code inspection confirmed: dcPath: 'ha-datacenter' at vmware_manager.py:976; URL uses self.config.esxi_host at line 978."

### 9. Config accepts VCENTER_HOST env var
expected: Setting the `VCENTER_HOST` environment variable (or `esxi_host` key in config.yaml) should configure the host the server connects to. The `VCENTER_HOST` env var name is preserved for backward compatibility while the internal Config attribute is `esxi_host`.
result: pass
reason: "Static code inspection confirmed: VCENTER_HOST maps to esxi_host in env_map (config.py:55); esxi_host is the required Config field (config.py:12, 78)."

## Summary

total: 9
passed: 4
issues: 5
pending: 0
skipped: 0

## Gaps

- truth: "create_vm completes successfully against a standalone ESXi host"
  status: failed
  reason: "User reported: The listing operations work fine, but VM creation fails. This appears to be an issue with the MCP server's VM creation logic — on a standalone ESXi host (no vCenter cluster), it can't resolve the host/resource pool for placement. The terse 'host' error suggests it's failing during host lookup."
  severity: blocker
  test: 3
  root_cause: "vm_folder = host_system.vm is vim.VirtualMachine[] (a list), not a vim.Folder; calling CreateVM_Task on it causes NotSupported. Additionally, host_system = rootFolder.childEntity[0].host[0] is wrong — childEntity[0] is a vim.Datacenter which has no .host attribute. Fix: use self.compute_resource.host[0] for host_system and self.datacenter_obj.vmFolder for vm_folder; store self.compute_resource in _connect_vcenter."
  artifacts:
    - path: "esxi_mcp_server/vmware_manager.py"
      lines: "517-521"
      issue: "host_system = rootFolder.childEntity[0].host[0] — vim.Datacenter has no .host; vm_folder = host_system.vm is VirtualMachine[], not vim.Folder; CreateVM_Task on VirtualMachine[] raises NotSupported"
    - path: "esxi_mcp_server/vmware_manager.py"
      lines: "~96 (_connect_vcenter)"
      issue: "compute_resource is a local variable, not stored as self.compute_resource — must be persisted for call sites to use"
  missing:
    - "In _connect_vcenter, after self.resource_pool = compute_resource.resourcePool, add: self.compute_resource = compute_resource"
    - "In create_vm: replace host_system/vm_folder lines with: host_system = self.compute_resource.host[0]; vm_folder = self.datacenter_obj.vmFolder"
  debug_session: ""

- truth: "clone_vm completes against a standalone ESXi host"
  status: failed
  reason: "User reported: vmodl.fault.NotSupported: The operation is not supported on the object."
  severity: blocker
  test: 4
  root_cause: "CloneVM_Task is a vCenter-only API — standalone ESXi does not implement it and always returns vmodl.fault.NotSupported regardless of arguments. Cannot be fixed; must be removed like list_datastore_clusters."
  artifacts:
    - path: "esxi_mcp_server/vmware_manager.py"
      issue: "clone_vm calls VirtualMachine.Clone() (CloneVM_Task) which is vCenter-exclusive"
    - path: "esxi_mcp_server/mcp_server.py"
      issue: "clone_vm tool definition must be removed from tools dict and tool_handler_map"
    - path: "esxi_mcp_server/tools.py"
      issue: "clone_vm delegation method must be removed"
  missing:
    - "Remove clone_vm from vmware_manager.py, mcp_server.py, and tools.py (same pattern as list_datastore_clusters removal in plan 02-01)"
  debug_session: ""

- truth: "create_vm_custom completes successfully against a standalone ESXi host"
  status: failed
  reason: "User reported: similar error to the clone vm one (vmodl.fault.NotSupported)"
  severity: blocker
  test: 5
  root_cause: "Same wrong folder reference as create_vm: vm_folder = host_system.vm is vim.VirtualMachine[], not vim.Folder. CreateVM_Task IS supported on standalone ESXi when called on a proper vim.Folder — this is fixable (unlike clone_vm)."
  artifacts:
    - path: "esxi_mcp_server/vmware_manager.py"
      lines: "635-638"
      issue: "host_system = rootFolder.childEntity[0].host[0] — wrong traversal; vm_folder = host_system.vm — VirtualMachine[] not vim.Folder; CreateVM_Task on wrong object raises NotSupported"
  missing:
    - "In create_vm_custom: replace host_system/vm_folder lines with: host_system = self.compute_resource.host[0]; vm_folder = self.datacenter_obj.vmFolder"
  debug_session: ""

- truth: "deploy_ovf completes against a standalone ESXi host"
  status: failed
  reason: "User reported: the same type of host error occurs when trying to run the deploy_ovf"
  severity: blocker
  test: 6
  root_cause: "Same wrong host_system traversal path (rootFolder.childEntity[0].host[0] — vim.Datacenter has no .host). Also, ImportVApp second arg is host_system.vm (VirtualMachine[] list) instead of self.datacenter_obj.vmFolder (vim.Folder)."
  artifacts:
    - path: "esxi_mcp_server/vmware_manager.py"
      lines: "1063-1065"
      issue: "host_system = rootFolder.childEntity[0].host[0] wrong; ImportVApp(importSpec, host_system.vm) passes VirtualMachine[] as folder — must be vim.Folder"
  missing:
    - "Replace host_system lookup with self.compute_resource.host[0]"
    - "Change ImportVApp call to: resource_pool.ImportVApp(import_spec.importSpec, self.datacenter_obj.vmFolder, host=host_system)"
  debug_session: ""

- truth: "deploy_ova completes against a standalone ESXi host"
  status: failed
  reason: "User reported: the same host error occurs."
  severity: blocker
  test: 7
  root_cause: "Identical issue to deploy_ovf: wrong host_system traversal and ImportVApp folder argument is VirtualMachine[] instead of vim.Folder."
  artifacts:
    - path: "esxi_mcp_server/vmware_manager.py"
      lines: "1180-1182"
      issue: "host_system = rootFolder.childEntity[0].host[0] wrong; ImportVApp(importSpec, host_system.vm) passes VirtualMachine[] as folder"
  missing:
    - "Replace host_system lookup with self.compute_resource.host[0]"
    - "Change ImportVApp call to: resource_pool.ImportVApp(import_spec.importSpec, self.datacenter_obj.vmFolder, host=host_system)"
  debug_session: ""
