# ESXi MCP Server — Tool Audit

**Date:** 2026-03-02
**Auditor:** Phase 1 plan execution
**Source:** esxi_mcp_server/vmware_manager.py (verified line numbers)

---

## Classification Summary

- ESXi-compatible: 22 tools
- needs-rewrite: 8 tools
- vCenter-only-remove: 1 tool
- **Total: 31 tools**

---

## Classification Table

| # | Tool (MCP name) | Method | Classification | vCenter Objects Used | Primary Reason |
|---|-----------------|--------|----------------|---------------------|----------------|
| 1 | `create_vm` | `create_vm()` | needs-rewrite | `self.datacenter_obj.datastoreFolder.childEntity` (line 450), `self.datacenter_obj.networkFolder.childEntity` (line 455), `self.datacenter_obj.vmFolder` (line 512) | Datastore and network lookup + VM folder placement go through datacenter_obj |
| 2 | `clone_vm` | `clone_vm()` | needs-rewrite | `self.datacenter_obj.vmFolder` (line 534, fallback) | Falls back to `datacenter_obj.vmFolder` when template.parent is not a Folder |
| 3 | `delete_vm` | `delete_vm()` | ESXi-compatible | None | Uses `find_vm()` + `vm.Destroy_Task()` only |
| 4 | `power_on_vm` | `power_on_vm()` | ESXi-compatible | None | Uses `find_vm()` + `vm.PowerOnVM_Task()` only |
| 5 | `power_off_vm` | `power_off_vm()` | ESXi-compatible | None | Uses `find_vm()` + `vm.PowerOffVM_Task()` only |
| 6 | `list_vms` | `list_vms()` | ESXi-compatible | None | Uses `CreateContainerView(rootFolder, [vim.VirtualMachine], True)` only |
| 7 | `get_vm_details` | `get_vm_details()` | ESXi-compatible | None | Reads VM object properties only; no datacenter reference |
| 8 | `get_vm_performance` | `get_vm_performance()` | ESXi-compatible | None | Uses `content.perfManager` (available on ESXi) and VM quickStats |
| 9 | `get_vm_summary_stats` | `get_vm_summary_stats()` | ESXi-compatible | None | Reads VM `quickStats` and `summary.storage` only |
| 10 | `create_vm_custom` | `create_vm_custom()` | needs-rewrite | `self.datacenter_obj.datastoreFolder.childEntity` (line 560), `self.datacenter_obj.networkFolder.childEntity` (line 565), `self.datacenter_obj.vmFolder` (line 622) | Same pattern as `create_vm` — datacenter used for datastore/network lookup and VM folder |
| 11 | `list_templates` | `list_templates()` | ESXi-compatible | None | Uses `CreateContainerView(rootFolder, [vim.VirtualMachine], True)` + template flag |
| 12 | `list_datastores` | `list_datastores()` | ESXi-compatible | None | Uses `CreateContainerView(rootFolder, [vim.Datastore], True)` |
| 13 | `list_datastore_clusters` | `list_datastore_clusters()` | vCenter-only-remove | `vim.StoragePod` (line 686) | `vim.StoragePod` (Storage DRS cluster) is a vCenter-only concept; does not exist on standalone ESXi |
| 14 | `list_networks` | `list_networks()` | ESXi-compatible | None | Uses `CreateContainerView(rootFolder, [vim.Network], True)`; DVS isinstance check is defensive/graceful |
| 15 | `list_hosts` | `list_hosts()` | ESXi-compatible | None | Uses `CreateContainerView(rootFolder, [vim.HostSystem], True)` |
| 16 | `get_host_details` | `get_host_details()` | ESXi-compatible | None | Reads host object properties only via `find_host()` |
| 17 | `get_host_performance_metrics` | `get_host_performance_metrics()` | ESXi-compatible | None | Reads `host.summary.quickStats` only |
| 18 | `get_host_hardware_health` | `get_host_hardware_health()` | ESXi-compatible | None | Reads `host.runtime.healthSystemRuntime` only |
| 19 | `get_host_performance` | `get_host_performance()` | ESXi-compatible | None | Reads host hardware and quickStats properties via `find_host()` |
| 20 | `list_performance_counters` | `list_performance_counters()` | ESXi-compatible | None | Uses `content.perfManager.perfCounter` (available on ESXi) |
| 21 | `create_snapshot` | `create_snapshot()` | ESXi-compatible | None | Uses `vm.CreateSnapshot()` directly |
| 22 | `remove_snapshot` | `remove_snapshot()` | ESXi-compatible | None | Uses `snapshot.snapshot.RemoveSnapshot_Task()` |
| 23 | `revert_snapshot` | `revert_snapshot()` | ESXi-compatible | None | Uses `snapshot.snapshot.RevertToSnapshot_Task()` |
| 24 | `list_snapshots` | `list_snapshots()` | ESXi-compatible | None | Reads `vm.snapshot.rootSnapshotList` tree |
| 25 | `remove_all_snapshots` | `remove_all_snapshots()` | ESXi-compatible | None | Uses `vm.RemoveAllSnapshots()` directly |
| 26 | `execute_program_in_vm` | `execute_program_in_vm()` | ESXi-compatible | None | Uses `content.guestOperationsManager.processManager` (available on ESXi) |
| 27 | `upload_file_to_vm` | `upload_file_to_vm()` | needs-rewrite | `self.config.vcenter_host` in URL substitution (line 940) | Config key will be renamed to `esxi_host` in Phase 3; URL substitution must use the new key |
| 28 | `upload_file_to_datastore` | `upload_file_to_datastore()` | needs-rewrite | `self.datacenter_obj.name` as `dcPath` param (line 976); `self.config.vcenter_host` in upload URL (line 978) | `dcPath` must change to `"ha-datacenter"` (ESXi pseudo-datacenter); config key rename |
| 29 | `deploy_ovf` | `deploy_ovf()` | needs-rewrite | `self.datacenter_obj.datastoreFolder.childEntity` (line 1026), `CreateContainerView(self.datacenter_obj, ...)` (line 1037-1038), `self.datacenter_obj.vmFolder` (line 1061), `self.config.vcenter_host` (line 1072) | ImportVApp needs host.vm folder; datastore/resource-pool lookup uses datacenter; config key rename |
| 30 | `deploy_ova` | `deploy_ova()` | needs-rewrite | `self.datacenter_obj.datastoreFolder.childEntity` (line 1140), `CreateContainerView(self.datacenter_obj, ...)` (line 1150-1151), `self.datacenter_obj.vmFolder` (line 1174), `self.config.vcenter_host` (line 1220) | Same pattern as `deploy_ovf` |
| 31 | `wait_for_updates` | `wait_for_updates()` / `_build_traversal_spec()` | needs-rewrite | `vim.Datacenter` traversal paths in `_build_traversal_spec()`: `dcToVmFolder` (lines 1349–1355), `dcToHostFolder` (lines 1358–1364) | TraversalSpec walks Datacenter.vmFolder and Datacenter.hostFolder paths that don't exist on ESXi |

---

## Notes on Classification Decisions

### `list_networks` — ESXi-compatible despite DVS isinstance check
The method (lines 271–288) checks `isinstance(net, vim.dvs.DistributedVirtualPortgroup)` to provide VLAN info for distributed portgroups. On standalone ESXi there are no DVS portgroups, so this branch simply never fires. The code is already defensive and ESXi-compatible as-is. No rewrite needed.

### `clone_vm` — only the vmFolder fallback needs changing
The primary folder assignment (`vm_folder = template_vm.parent`, line 532) is ESXi-compatible. Only the fallback path at line 534 that sets `vm_folder = self.datacenter_obj.vmFolder` when `template_vm.parent` is not a `vim.Folder` requires a rewrite.

### Tools using `self.resource_pool`, `self.datastore_obj`, `self.network_obj` — NOT needs-rewrite
These init-cached objects (`self.resource_pool`, `self.datastore_obj`, `self.network_obj`) will be fixed by the Phase 3 rewrite of `_connect_vcenter()`. Tool methods that only reference these cached objects (e.g., `clone_vm` line 536–537, many others) are **ESXi-compatible pending the Phase 3 init rewrite** and are classified accordingly. Only tool methods with **additional** direct `datacenter_obj` references in their own body are classified as needs-rewrite.

---

## Rewrite Specifications

### `create_vm`

**Method:** `create_vm()` lines 444–525

| Location | Current Expression | Change To |
|----------|--------------------|-----------|
| line 450 | `self.datacenter_obj.datastoreFolder.childEntity` | `content.viewManager.CreateContainerView(content.rootFolder, [vim.Datastore], True).view` (filter by name) |
| line 455 | `self.datacenter_obj.networkFolder.childEntity` | `content.viewManager.CreateContainerView(content.rootFolder, [vim.Network], True).view` (filter by name) |
| line 512 | `vm_folder = self.datacenter_obj.vmFolder` | `host_system = self.content.rootFolder.childEntity[0].host[0]; vm_folder = host_system.vm` |

**ESXi pattern (Pattern 3 from RESEARCH.md):**
```python
# ESXi: get host VM folder
host_system = self.content.rootFolder.childEntity[0].host[0]
vm_folder = host_system.vm  # vim.Folder on ESXi
# resource pool from init rewrite (self.resource_pool already ESXi-compatible after Phase 3)
task = vm_folder.CreateVM_Task(config=vm_spec, pool=self.resource_pool)
```

---

### `clone_vm`

**Method:** `clone_vm()` lines 527–549

| Location | Current Expression | Change To |
|----------|--------------------|-----------|
| line 534 | `vm_folder = self.datacenter_obj.vmFolder` (fallback) | `host_system = self.content.rootFolder.childEntity[0].host[0]; vm_folder = host_system.vm` |

**Note:** The primary path (`vm_folder = template_vm.parent` at line 532) is already ESXi-compatible. Only the fallback needs to change. `self.resource_pool` at line 536 and `self.datastore_obj` at line 537 will be fixed by the Phase 3 `_connect_vcenter()` rewrite.

---

### `create_vm_custom`

**Method:** `create_vm_custom()` lines 551–633

| Location | Current Expression | Change To |
|----------|--------------------|-----------|
| line 560 | `self.datacenter_obj.datastoreFolder.childEntity` | `content.viewManager.CreateContainerView(content.rootFolder, [vim.Datastore], True).view` (filter by name) |
| line 565 | `self.datacenter_obj.networkFolder.childEntity` | `content.viewManager.CreateContainerView(content.rootFolder, [vim.Network], True).view` (filter by name) |
| line 622 | `vm_folder = self.datacenter_obj.vmFolder` | `host_system = self.content.rootFolder.childEntity[0].host[0]; vm_folder = host_system.vm` |

**Pattern:** Identical to `create_vm` above. Same ESXi replacement pattern applies.

---

### `upload_file_to_vm`

**Method:** `upload_file_to_vm()` lines 905–949

| Location | Current Expression | Change To |
|----------|--------------------|-----------|
| line 940 | `url = re.sub(r"^https://\*:", f"https://{self.config.vcenter_host}:", url)` | `url = re.sub(r"^https://\*:", f"https://{self.config.esxi_host}:", url)` |

**Phase 3 dependency:** This change assumes Phase 3 has already renamed `config.vcenter_host` to `config.esxi_host`. If Phase 2 is implemented before Phase 3, the Phase 2 implementor must either: (a) rename the config key simultaneously, or (b) keep `vcenter_host` temporarily and note it for Phase 3 cleanup.

**Open question:** Verify on live ESXi that `InitiateFileTransferToGuest` returns a URL with `*` as the host placeholder. This is the same pattern as vCenter and expected to work identically, but should be confirmed during Phase 2 testing.

---

### `upload_file_to_datastore`

**Method:** `upload_file_to_datastore()` lines 951–1006

| Location | Current Expression | Change To |
|----------|--------------------|-----------|
| line 976 | `"dcPath": self.datacenter_obj.name` | `"dcPath": "ha-datacenter"` (ESXi pseudo-datacenter name) OR omit the key entirely |
| line 978 | `http_url = f"https://{self.config.vcenter_host}:443{resource}"` | `http_url = f"https://{self.config.esxi_host}:443{resource}"` |

**Phase 3 dependency:** `self.config.vcenter_host` → `self.config.esxi_host` rename (same as `upload_file_to_vm`).

**Open question (requires live ESXi testing):** The correct value for `dcPath` on a standalone ESXi host is uncertain:
- **Option A:** `"ha-datacenter"` — ESXi's built-in pseudo-datacenter name used in its datastore HTTP API
- **Option B:** Omit `dcPath` entirely — ESXi may accept the upload request without it
- Recommendation: Try Option A first (`"ha-datacenter"`); fall back to Option B if 404 is returned. Document the working option after Phase 2 testing on live ESXi.

---

### `deploy_ovf`

**Method:** `deploy_ovf()` lines 1008–1105

| Location | Current Expression | Change To |
|----------|--------------------|-----------|
| line 1026 | `for ds in self.datacenter_obj.datastoreFolder.childEntity:` | `container = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.Datastore], True)` then iterate `container.view` |
| line 1037–1038 | `container = self.content.viewManager.CreateContainerView(self.datacenter_obj, [vim.ResourcePool], True)` | `container = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.ResourcePool], True)` |
| line 1061 | `lease = resource_pool.ImportVApp(import_spec.importSpec, self.datacenter_obj.vmFolder)` | `host_system = self.content.rootFolder.childEntity[0].host[0]; lease = resource_pool.ImportVApp(import_spec.importSpec, host_system.vm)` |
| line 1072 | `url = lease.info.deviceUrl[0].url.replace('*', self.config.vcenter_host)` | `url = lease.info.deviceUrl[0].url.replace('*', self.config.esxi_host)` |

**Phase 3 dependency:** `self.config.vcenter_host` → `self.config.esxi_host` rename.

**ESXi equivalent pattern (Pattern 5 from RESEARCH.md):**
```python
# ESXi: use host.vm as the ImportVApp folder argument
host_system = self.content.rootFolder.childEntity[0].host[0]
lease = resource_pool.ImportVApp(import_spec.importSpec, host_system.vm)
```

---

### `deploy_ova`

**Method:** `deploy_ova()` lines 1107–1246

| Location | Current Expression | Change To |
|----------|--------------------|-----------|
| line 1140 | `for ds in self.datacenter_obj.datastoreFolder.childEntity:` | `container = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.Datastore], True)` then iterate `container.view` |
| line 1150–1151 | `container = self.content.viewManager.CreateContainerView(self.datacenter_obj, [vim.ResourcePool], True)` | `container = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.ResourcePool], True)` |
| line 1174 | `lease = resource_pool.ImportVApp(import_spec.importSpec, self.datacenter_obj.vmFolder)` | `host_system = self.content.rootFolder.childEntity[0].host[0]; lease = resource_pool.ImportVApp(import_spec.importSpec, host_system.vm)` |
| line 1220 | `url = device_url.url.replace('*', self.config.vcenter_host)` | `url = device_url.url.replace('*', self.config.esxi_host)` |

**Pattern:** Identical to `deploy_ovf` above. Same ESXi replacement pattern applies.

---

### `wait_for_updates`

**Method:** `wait_for_updates()` lines 1248–1334 + `_build_traversal_spec()` lines 1336–1372

| Location | Current Expression | Change To |
|----------|--------------------|-----------|
| lines 1349–1355 | `dc_to_vmfolder = TraversalSpec(name='dcToVmFolder', type=vim.Datacenter, path='vmFolder', ...)` | Remove this TraversalSpec entirely |
| lines 1358–1364 | `dc_to_hostfolder = TraversalSpec(name='dcToHostFolder', type=vim.Datacenter, path='hostFolder', ...)` | Remove this TraversalSpec entirely |
| lines 1366–1370 | `folder_to_child.selectSet = [..., SelectionSpec(name='dcToVmFolder'), SelectionSpec(name='dcToHostFolder')]` | Remove the two datacenter SelectionSpec entries; keep `SelectionSpec(name='folderToChild')` only |

**Current `_build_traversal_spec()` returns:** `[folder_to_child, dc_to_vmfolder, dc_to_hostfolder]`

**ESXi replacement:** On ESXi, `content.rootFolder` directly contains `vim.ComputeResource` (no `vim.Datacenter` wrapping). The `folderToChild` traversal on `rootFolder` is sufficient:

```python
def _build_traversal_spec(self):
    """Build traversal spec for property collector (ESXi-compatible)."""
    from pyVmomi import vmodl

    # On ESXi: rootFolder -> ComputeResource (direct child, no Datacenter)
    # folderToChild traversal is sufficient — remove dcToVmFolder and dcToHostFolder
    folder_to_child = vmodl.query.PropertyCollector.TraversalSpec(
        name='folderToChild',
        type=vim.Folder,
        path='childEntity',
        skip=False,
        selectSet=[vmodl.query.PropertyCollector.SelectionSpec(name='folderToChild')]
    )

    return [folder_to_child]
```

**Open question (requires live ESXi testing):** Verify that the simplified `folderToChild`-only traversal spec correctly discovers all `VirtualMachine` and `HostSystem` objects on ESXi. The current spec was written for a Datacenter-wrapped hierarchy. On ESXi, the rootFolder → ComputeResource → host/vm path should be reachable with folderToChild alone, but this needs validation against the actual ESXi object tree during Phase 2 testing.

---

## Phase 2 Implementation Notes

### Open Questions Requiring Live ESXi Testing

1. **`upload_file_to_datastore` — `dcPath` parameter value on ESXi**
   - **What is known:** vCenter requires `dcPath` set to the datacenter name. On ESXi standalone, the pseudo-datacenter name is `"ha-datacenter"`.
   - **What is uncertain:** Whether ESXi requires `dcPath` at all, or whether it can be omitted. ESXi's datastore HTTP API behavior with this parameter is not verified.
   - **Recommended approach:** Implement with `"ha-datacenter"` as the dcPath value (Option A). If upload returns 404, try omitting the parameter entirely (Option B). Document which option works after live ESXi testing.
   - **Relevant code:** lines 973–978 in `upload_file_to_datastore()`

2. **`wait_for_updates` — simplified traversal spec on ESXi**
   - **What is known:** The current traversal spec explicitly walks `vim.Datacenter.vmFolder` and `vim.Datacenter.hostFolder`. These Datacenter properties do not exist on standalone ESXi.
   - **What is uncertain:** Whether `folderToChild`-only traversal on `rootFolder` is sufficient to discover all VMs and hosts in the ESXi object tree. The ESXi object model is `rootFolder → ComputeResource`, and it is unclear whether `folderToChild` traverses into ComputeResource.childEntity or needs additional traversal specs.
   - **Recommended approach:** Replace with `folderToChild`-only traversal as specified in the rewrite spec above. Validate by calling `wait_for_updates` against a live ESXi host and confirming VMs and hosts appear in the update set.
   - **Relevant code:** `_build_traversal_spec()` lines 1336–1372

3. **`upload_file_to_vm` — URL format returned by `InitiateFileTransferToGuest` on ESXi**
   - **What is known:** On vCenter, `InitiateFileTransferToGuest` returns a URL with `*` as the host, which is replaced with `config.vcenter_host`. The `*` wildcard behavior is a vSphere API convention.
   - **What is uncertain:** Whether standalone ESXi returns the same URL format with `*` as the host placeholder, or whether it returns a different format.
   - **Recommended approach:** Implement the config key rename (`vcenter_host` → `esxi_host`) as the only change. Test on live ESXi to confirm the URL replacement `re.sub(r"^https://\*:", ...)` still applies.
   - **Relevant code:** line 940 in `upload_file_to_vm()`

### Phase 3 Config Key Dependency

The following tools reference `self.config.vcenter_host` which will be renamed to `self.config.esxi_host` in Phase 3:
- `upload_file_to_vm` (line 940)
- `upload_file_to_datastore` (line 978)
- `deploy_ovf` (line 1072)
- `deploy_ova` (line 1220)

**Dependency flag:** Phase 2 implementors have two options:
- **Option A (recommended):** Implement the Phase 2 rewrite using `self.config.esxi_host` directly, AND rename the config key in `config.py` as part of the same change. This collapses the Phase 3 config rename into Phase 2 for these four methods.
- **Option B:** Implement Phase 2 using `self.config.vcenter_host` temporarily, and let Phase 3 complete the rename. This leaves broken references until Phase 3 but avoids scope creep in Phase 2.

Whichever option is chosen, the decision must be consistent across all four affected methods.
