# Phase 1: Audit - Research

**Researched:** 2026-03-02
**Domain:** pyVmomi vSphere API — ESXi vs vCenter object compatibility
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AUDIT-01 | All 31 MCP tools classified as ESXi-compatible, needs-rewrite, or vCenter-only-remove | Full tool-by-tool analysis below; classification table in Architecture Patterns section |
| AUDIT-02 | pyVmomi API differences documented for each tool requiring rewrite (vCenter objects → ESXi equivalents) | Documented per-tool in Code Examples section with exact line numbers |
</phase_requirements>

---

## Summary

This phase is a **code reading and classification exercise**, not a coding task. The deliverable is a written audit document that classifies all 31 MCP tools and documents the specific pyVmomi API differences for every tool needing a rewrite. No production code changes occur in Phase 1.

The codebase was designed for vCenter and uses vCenter-specific object hierarchy (datacenter → cluster → resource pool → vmFolder) throughout `VMwareManager.__init__()` (lines 64–127) and in several tool methods. ESXi standalone hosts expose a simplified object tree — there is no `vim.Datacenter` wrapping resources; instead everything hangs off a single `vim.ComputeResource` returned directly from `content.rootFolder`. The distinction drives every classification decision.

Of 31 tools: **22 are ESXi-compatible as-is** (they operate through `content.viewManager`, VM/host object methods, or guest operations that work identically on standalone ESXi), **8 need rewrite** (they reference `datacenter_obj`, `datacenter_obj.vmFolder`, `datacenter_obj.datastoreFolder`, or the traversal spec explicitly walks `vim.Datacenter` paths), and **1 must be removed** (`list_datastore_clusters` uses `vim.StoragePod` which does not exist on standalone ESXi).

**Primary recommendation:** Read `vmware_manager.py` line by line, classify each tool method against the criterion "does this reference `self.datacenter_obj`, `self.resource_pool` as set during `_connect_vcenter()`, or any `vim.ClusterComputeResource`/`vim.StoragePod`?", and produce the classification table + per-tool rewrite notes in a single audit document.

---

## Standard Stack

This phase produces a **Markdown document**, not code. No new libraries are needed.

### Core (Audit Tooling)
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| pyVmomi | >=7.0 (installed) | Source of truth for API object types | Already in requirements.txt |
| Python grep / code reading | n/a | Identify all references to vCenter objects | Direct code inspection is authoritative |

### Supporting References
| Resource | Version | Purpose | When to Use |
|----------|---------|---------|-------------|
| pyVmomi API docs | current | Confirm which vim objects exist on ESXi vs vCenter | For any uncertain API call |
| VMware vSphere API Reference | 7.x/8.x | Authoritative source on object availability per host type | Cross-check classifications |

### No Installation Required

This phase involves no new dependencies. The audit is a documentation task.

---

## Architecture Patterns

### Audit Document Structure

The output of this phase is a single Markdown file (e.g., `AUDIT.md` in the phase directory) with:

1. **Classification table** — one row per tool, three columns: Tool Name | Classification | Reason
2. **Rewrite specs** — one subsection per `needs-rewrite` tool with: vCenter objects used, their line numbers, ESXi equivalents

### Pattern 1: vCenter vs ESXi Object Hierarchy

**What:** The fundamental API difference driving all classifications.

**vCenter hierarchy (current code assumes):**
```
content.rootFolder
  └── vim.Datacenter          (datacenter_obj)
        ├── .vmFolder         (where VMs are created)
        ├── .hostFolder
        │     └── vim.ClusterComputeResource  (or vim.ComputeResource)
        │           └── .resourcePool
        ├── .datastoreFolder
        └── .networkFolder
```

**ESXi standalone hierarchy (what actually exists):**
```
content.rootFolder
  └── vim.ComputeResource     (direct child — no Datacenter wrapping)
        ├── .resourcePool     (host resource pool — usable directly)
        └── .host[0]          (the HostSystem)
              └── .vm         (host's VM folder — used for CreateVM_Task)
```

**Key difference:** On ESXi, `content.rootFolder.childEntity[0]` is a `vim.ComputeResource` directly, not a `vim.Datacenter`. There is no `datacenter_obj.vmFolder` — VMs must be created in `host.vm` (the host's VM folder) or via the `ResourcePool.CreateVM_Task()` path.

**Source:** pyVmomi community samples, VMware KB articles on standalone ESXi API access (MEDIUM confidence — verified against known API behavior from pyVmomi source).

### Pattern 2: ESXi-Compatible API Calls (no changes needed)

These pyVmomi calls work identically on standalone ESXi and vCenter:

```python
# Source: vmware_manager.py — confirmed ESXi-compatible patterns

# Container views — work on ESXi (rootFolder traversal is host-aware)
container = content.viewManager.CreateContainerView(
    content.rootFolder, [vim.VirtualMachine], True)

# VM power operations — work on ESXi
task = vm.PowerOnVM_Task()
task = vm.PowerOffVM_Task()
task = vm.Destroy_Task()

# Snapshot operations — work on ESXi
task = vm.CreateSnapshot(name, desc, memory, quiesce)
task = vm.snapshot.RemoveAllSnapshots()

# Guest operations — work on ESXi (VMware Tools)
content.guestOperationsManager.processManager.StartProgramInGuest(vm, creds, spec)
content.guestOperationsManager.fileManager.InitiateFileTransferToGuest(...)

# Performance data — perfManager available on ESXi
content.perfManager.perfCounter
content.perfManager.QueryStats(querySpec=[query])

# Property collector — available on ESXi
content.propertyCollector.WaitForUpdatesEx(version, opts)
```

### Pattern 3: ESXi VM Folder and Resource Pool (rewrite target)

On ESXi standalone, VM creation must use the host's vm property as folder:

```python
# Source: ESXi API pattern (MEDIUM confidence — verified against pyVmomi samples)

# Get the host directly from rootFolder
host_system = content.rootFolder.childEntity[0].host[0]
# Use host's vm property as the folder for CreateVM_Task
vm_folder = host_system.vm  # This is a vim.Folder on ESXi

# OR use the ComputeResource's resourcePool for the pool argument
compute_resource = content.rootFolder.childEntity[0]  # vim.ComputeResource on ESXi
resource_pool = compute_resource.resourcePool

# CreateVM_Task on ESXi (same API call, different folder source)
task = vm_folder.CreateVM_Task(config=vm_spec, pool=resource_pool)
```

### Pattern 4: Datastore and Network on ESXi (no datacenter wrapper)

```python
# Source: ESXi API pattern (MEDIUM confidence)

# Datastore: accessible via host's datastore property, or via ContainerView
datastores = host_system.datastore  # List of vim.Datastore objects

# OR via container view (already ESXi-compatible in list_datastores)
container = content.viewManager.CreateContainerView(
    content.rootFolder, [vim.Datastore], True)

# Network: accessible via host's network property
networks = host_system.network  # List of vim.Network objects
```

### Pattern 5: OVF/OVA Deployment on ESXi

The `deploy_ovf` and `deploy_ova` methods use `resource_pool.ImportVApp(spec, datacenter_obj.vmFolder)`. On ESXi:
- `resource_pool` becomes the host's resource pool (same access pattern)
- `datacenter_obj.vmFolder` must become the host's `vm` folder property

```python
# Source: vmware_manager.py lines 1060-1061 and 1173-1174 (current vCenter code)
lease = resource_pool.ImportVApp(
    import_spec.importSpec, self.datacenter_obj.vmFolder)  # MUST CHANGE

# ESXi equivalent:
host_system = content.rootFolder.childEntity[0].host[0]
lease = resource_pool.ImportVApp(
    import_spec.importSpec, host_system.vm)  # ESXi: use host.vm as folder
```

### Pattern 6: upload_file_to_datastore on ESXi

The `dcPath` parameter in the datastore HTTP upload URL is vCenter-specific:

```python
# Source: vmware_manager.py lines 974-978 (current code)
params = {
    "dsName": datastore.name,
    "dcPath": self.datacenter_obj.name  # VENTER-SPECIFIC — remove or set to "ha-datacenter"
}
# On ESXi, the dcPath is "ha-datacenter" (the ESXi pseudo-datacenter name)
# OR omit dcPath entirely — ESXi only has one datacenter context
```

### Anti-Patterns to Avoid

- **Classifying by tool name alone:** Some tools (e.g., `list_datastores`) look vCenter-specific but are already ESXi-compatible because they use ContainerView on rootFolder, not `datacenter_obj`.
- **Over-classifying `needs-rewrite`:** Tools that only reference `self.resource_pool` or `self.datastore_obj` via the cached init values are fine — the rewrite is in `_connect_vcenter()`, not in the tool methods themselves.
- **Missing secondary datacenter references:** `deploy_ovf`, `deploy_ova`, `upload_file_to_datastore`, and `wait_for_updates` each have secondary datacenter references in addition to the ones fixed by `_connect_vcenter()` rewrite.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Discovering vCenter vs ESXi API differences | Custom test harness | Read existing pyVmomi code + known docs | The differences are well-documented; runtime testing requires live ESXi access |
| Audit document format | Complex tooling | Simple Markdown table | Planner just needs structured classifications the executor can follow |

**Key insight:** This is a documentation phase. The "standard stack" is code reading + Markdown writing. No clever tooling adds value.

---

## Complete Tool Classification

This is the primary research output — the full classification for all 31 tools.

### Classification Definitions
- **ESXi-compatible**: Works on standalone ESXi without any changes to the tool method itself (changes to `_connect_vcenter()` may still be needed in Phase 3)
- **needs-rewrite**: The tool method itself contains references to vCenter-specific objects (`datacenter_obj`, `datacenter_obj.vmFolder`, `datacenter_obj.datastoreFolder`, etc.) that must be changed
- **vCenter-only-remove**: Uses a pyVmomi object type (`vim.StoragePod`) that does not exist on standalone ESXi; no rewrite possible

### Full Classification Table

| # | Tool | Classification | vCenter Objects Used | Primary Reason |
|---|------|----------------|---------------------|----------------|
| 1 | `create_vm` | needs-rewrite | `datacenter_obj.vmFolder` (line 512), `datacenter_obj.datastoreFolder` (line 450), `datacenter_obj.networkFolder` (line 455) | VM folder and datastore/network lookup go through datacenter |
| 2 | `clone_vm` | needs-rewrite | `datacenter_obj.vmFolder` (line 534, fallback), `self.resource_pool` (line 536) | Falls back to `datacenter_obj.vmFolder` when template.parent is not a Folder |
| 3 | `delete_vm` | ESXi-compatible | None | Uses `find_vm()` + `vm.Destroy_Task()` only |
| 4 | `power_on_vm` | ESXi-compatible | None | Uses `find_vm()` + `vm.PowerOnVM_Task()` only |
| 5 | `power_off_vm` | ESXi-compatible | None | Uses `find_vm()` + `vm.PowerOffVM_Task()` only |
| 6 | `list_vms` | ESXi-compatible | None | Uses `CreateContainerView(rootFolder, [vim.VirtualMachine], True)` |
| 7 | `get_vm_details` | ESXi-compatible | None | Reads VM properties only; no datacenter reference |
| 8 | `get_vm_performance` | ESXi-compatible | None | Uses `content.perfManager` (available on ESXi) |
| 9 | `get_vm_summary_stats` | ESXi-compatible | None | Reads VM `quickStats` only |
| 10 | `create_vm_custom` | needs-rewrite | `datacenter_obj.vmFolder` (line 622), `datacenter_obj.datastoreFolder` (line 560), `datacenter_obj.networkFolder` (line 565) | Same pattern as `create_vm` |
| 11 | `list_templates` | ESXi-compatible | None | Uses `CreateContainerView(rootFolder, [vim.VirtualMachine], True)` + template flag |
| 12 | `list_datastores` | ESXi-compatible | None | Uses `CreateContainerView(rootFolder, [vim.Datastore], True)` |
| 13 | `list_datastore_clusters` | vCenter-only-remove | `vim.StoragePod` (line 686) | `vim.StoragePod` is a vCenter-only concept; ESXi has no StoragePod |
| 14 | `list_networks` | ESXi-compatible | None | Uses `CreateContainerView(rootFolder, [vim.Network], True)` |
| 15 | `list_hosts` | ESXi-compatible | None | Uses `CreateContainerView(rootFolder, [vim.HostSystem], True)` |
| 16 | `get_host_details` | ESXi-compatible | None | Reads host object properties only |
| 17 | `get_host_performance_metrics` | ESXi-compatible | None | Reads `host.summary.quickStats` only |
| 18 | `get_host_hardware_health` | ESXi-compatible | None | Reads `host.runtime.healthSystemRuntime` only |
| 19 | `get_host_performance` | ESXi-compatible | None | Reads host hardware/quickStats properties |
| 20 | `list_performance_counters` | ESXi-compatible | None | Uses `content.perfManager.perfCounter` (available on ESXi) |
| 21 | `create_snapshot` | ESXi-compatible | None | Uses `vm.CreateSnapshot()` directly |
| 22 | `remove_snapshot` | ESXi-compatible | None | Uses `snapshot.RemoveSnapshot_Task()` |
| 23 | `revert_snapshot` | ESXi-compatible | None | Uses `snapshot.RevertToSnapshot_Task()` |
| 24 | `list_snapshots` | ESXi-compatible | None | Reads VM snapshot tree properties |
| 25 | `remove_all_snapshots` | ESXi-compatible | None | Uses `vm.RemoveAllSnapshots()` |
| 26 | `execute_program_in_vm` | ESXi-compatible | None | Uses `content.guestOperationsManager` (available on ESXi) |
| 27 | `upload_file_to_vm` | needs-rewrite | `self.config.vcenter_host` in URL (line 940) | URL substitution uses config key that will be renamed to `esxi_host`; also verify guestOps URL format on ESXi |
| 28 | `upload_file_to_datastore` | needs-rewrite | `self.datacenter_obj.name` in params (line 976) | Uses `dcPath` param set to datacenter name; on ESXi must use `ha-datacenter` or omit |
| 29 | `deploy_ovf` | needs-rewrite | `self.datacenter_obj.vmFolder` (line 1061), `self.datacenter_obj.datastoreFolder` (line 1026), datacenter search for resource pool (line 1038) | ImportVApp needs host.vm folder; datastore/rp lookup uses datacenter |
| 30 | `deploy_ova` | needs-rewrite | `self.datacenter_obj.vmFolder` (line 1174), `self.datacenter_obj.datastoreFolder` (line 1140), datacenter for rp search (line 1151) | Same pattern as `deploy_ovf` |
| 31 | `wait_for_updates` | needs-rewrite | `_build_traversal_spec()` uses `vim.Datacenter` traversal paths (lines 1349-1364) | TraversalSpec walks `dcToVmFolder` and `dcToHostFolder` — these Datacenter paths don't exist on ESXi |

### Summary Counts
- **ESXi-compatible**: 22 tools (delete_vm, power_on_vm, power_off_vm, list_vms, get_vm_details, get_vm_performance, get_vm_summary_stats, list_templates, list_datastores, list_networks, list_hosts, get_host_details, get_host_performance_metrics, get_host_hardware_health, get_host_performance, list_performance_counters, create_snapshot, remove_snapshot, revert_snapshot, list_snapshots, remove_all_snapshots, execute_program_in_vm)
- **needs-rewrite**: 8 tools (create_vm, clone_vm, create_vm_custom, upload_file_to_vm, upload_file_to_datastore, deploy_ovf, deploy_ova, wait_for_updates)
- **vCenter-only-remove**: 1 tool (list_datastore_clusters)

---

## Code Examples

### Rewrite Specs — Exact vCenter Objects and ESXi Equivalents

#### create_vm (lines 444–525)
```python
# CURRENT — vCenter objects:
#   line 450: self.datacenter_obj.datastoreFolder.childEntity  → datastore lookup via datacenter
#   line 455: self.datacenter_obj.networkFolder.childEntity    → network lookup via datacenter
#   line 512: vm_folder = self.datacenter_obj.vmFolder         → VM placement folder
#   line 515: vm_folder.CreateVM_Task(config=vm_spec, pool=self.resource_pool)

# ESXi EQUIVALENT:
#   Datastore: use CreateContainerView(rootFolder, [vim.Datastore], True) and filter by name
#   Network: use CreateContainerView(rootFolder, [vim.Network], True) and filter by name
#   VM folder: host_system = content.rootFolder.childEntity[0].host[0]; vm_folder = host_system.vm
#   Resource pool: compute_resource = content.rootFolder.childEntity[0]; pool = compute_resource.resourcePool
```

#### clone_vm (lines 527–549)
```python
# CURRENT — vCenter objects:
#   line 534: vm_folder = self.datacenter_obj.vmFolder   (fallback when parent not a Folder)
#   line 536: resource_pool = template_vm.resourcePool or self.resource_pool

# ESXi EQUIVALENT:
#   vm_folder fallback: host_system.vm  (the host's VM folder)
#   self.resource_pool already ESXi-compatible after _connect_vcenter() rewrite
```

#### create_vm_custom (lines 551–633)
```python
# CURRENT — vCenter objects:
#   line 560: self.datacenter_obj.datastoreFolder.childEntity
#   line 565: self.datacenter_obj.networkFolder.childEntity
#   line 622: vm_folder = self.datacenter_obj.vmFolder
#   line 624: vm_folder.CreateVM_Task(config=vm_spec, pool=self.resource_pool)

# ESXi EQUIVALENT: identical pattern to create_vm above
```

#### upload_file_to_vm (lines 905–949)
```python
# CURRENT — vCenter object:
#   line 940: url = re.sub(r"^https://\*:", f"https://{self.config.vcenter_host}:", url)
#   (uses config.vcenter_host which will be renamed to config.esxi_host in Phase 3)

# ESXi EQUIVALENT:
#   After Phase 3 config rename: change self.config.vcenter_host → self.config.esxi_host
#   The guestOperationsManager URL pattern is identical on ESXi; no other changes needed
#   NOTE: classify as needs-rewrite because the config key reference changes
```

#### upload_file_to_datastore (lines 951–1006)
```python
# CURRENT — vCenter object:
#   line 976: "dcPath": self.datacenter_obj.name  → datacenter name in HTTP upload params

# ESXi EQUIVALENT:
#   On ESXi standalone, the pseudo-datacenter name is always "ha-datacenter"
#   Option A: hardcode "ha-datacenter" as the dcPath value
#   Option B: omit dcPath (ESXi may accept requests without it — verify)
#   line 978: http_url also uses self.config.vcenter_host → rename to self.config.esxi_host
```

#### deploy_ovf (lines 1008–1105)
```python
# CURRENT — vCenter objects:
#   line 1026: self.datacenter_obj.datastoreFolder.childEntity  → datastore lookup
#   line 1038: CreateContainerView(self.datacenter_obj, [vim.ResourcePool], True)  → rp search
#   line 1061: resource_pool.ImportVApp(spec, self.datacenter_obj.vmFolder)  → folder arg
#   line 1072: url uses self.config.vcenter_host

# ESXi EQUIVALENT:
#   Datastore: use CreateContainerView(rootFolder, [vim.Datastore], True) and filter by name
#   Resource pool search: use CreateContainerView(rootFolder, [vim.ResourcePool], True)
#   ImportVApp folder: host_system.vm  (host's VM folder)
#   URL: self.config.esxi_host (after Phase 3 rename)
```

#### deploy_ova (lines 1107–1246)
```python
# CURRENT — vCenter objects:
#   line 1140: self.datacenter_obj.datastoreFolder.childEntity  → datastore lookup
#   line 1151: CreateContainerView(self.datacenter_obj, [vim.ResourcePool], True)  → rp search
#   line 1174: resource_pool.ImportVApp(spec, self.datacenter_obj.vmFolder)  → folder arg
#   line 1220: url uses self.config.vcenter_host

# ESXi EQUIVALENT: identical pattern to deploy_ovf above
```

#### wait_for_updates (lines 1248–1334) + _build_traversal_spec (lines 1336–1372)
```python
# CURRENT — vCenter objects in _build_traversal_spec():
#   lines 1349-1356: TraversalSpec for vim.Datacenter → vmFolder  (dcToVmFolder)
#   lines 1358-1364: TraversalSpec for vim.Datacenter → hostFolder (dcToHostFolder)
#   These traversal specs walk through Datacenter objects that don't exist on ESXi

# ESXi EQUIVALENT:
#   Remove dcToVmFolder and dcToHostFolder traversal specs
#   On ESXi, rootFolder directly contains ComputeResource; fold traversal can stop at rootFolder → childEntity
#   Simplified traversal: folderToChild traversal on rootFolder is sufficient
#   The property collector itself (WaitForUpdatesEx) works on ESXi — only the traversal path changes
```

---

## Common Pitfalls

### Pitfall 1: Confusing init-time vCenter objects with tool-method vCenter objects
**What goes wrong:** The `_connect_vcenter()` method (lines 38–127) sets `self.datacenter_obj`, `self.resource_pool`, `self.datastore_obj`, and `self.network_obj`. Many tools use these cached objects (e.g., `self.resource_pool`) which look like vCenter references but will be fixed when Phase 3 rewrites `_connect_vcenter()`. Classifying those tools as `needs-rewrite` is wrong — only tools that have **additional** direct datacenter references inside their own method body need rewriting.
**How to avoid:** Classify each tool method body independently. If the only datacenter reference is `self.resource_pool` or `self.datastore_obj` (cached from init), that tool is ESXi-compatible pending the init rewrite.
**Warning signs:** Over-counting needs-rewrite tools.

### Pitfall 2: Missing secondary datacenter references in deploy_ methods
**What goes wrong:** `deploy_ovf` and `deploy_ova` have multiple datacenter references — one in the datastore lookup loop, one in the resource pool ContainerView, and one in the ImportVApp call. Missing any of them leaves a broken method.
**How to avoid:** Grep for `datacenter_obj` across the entire file, not just in _connect_vcenter().
**Warning signs:** A deploy_ rewrite that only fixes the vmFolder argument but leaves the datastoreFolder.childEntity loop.

### Pitfall 3: list_networks DVS classification
**What goes wrong:** `list_networks` checks for `vim.dvs.DistributedVirtualPortgroup` (line 281). DVS portgroups are a vCenter-only concept, but the code handles them gracefully with an `isinstance` check and falls back. The tool still works on ESXi (it just won't find any DVS portgroups, which is correct). This does NOT require rewriting — it's already defensive.
**How to avoid:** Recognize that isinstance checks with graceful fallback are ESXi-compatible patterns.

### Pitfall 4: vim.StoragePod vs vim.Datastore confusion
**What goes wrong:** Misclassifying `list_datastore_clusters` as `needs-rewrite` instead of `vCenter-only-remove`. There is no ESXi equivalent for StoragePod/datastore clusters — they are a vCenter DRS storage concept.
**How to avoid:** Know that RMVL-01 in REQUIREMENTS.md explicitly calls for removal, not rewrite.

### Pitfall 5: upload_file_to_datastore dcPath behavior on ESXi
**What goes wrong:** Assuming the upload URL params work identically. On ESXi standalone, there is a pseudo-datacenter named `ha-datacenter` that must be used in place of the real datacenter name, or the `dcPath` parameter may need to be omitted entirely.
**Warning signs:** Upload returns 404 or authentication errors during Phase 2 testing.
**How to avoid:** Document this uncertainty in the audit; note that testing on live ESXi is needed to confirm the correct value.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact for This Phase |
|--------------|------------------|--------------|----------------------|
| vCenter-centric VMware automation | ESXi standalone API access | Phase 1 decision | Drives all tool classifications |
| `_connect_vcenter()` resolves datacenter/cluster | Must resolve host directly from rootFolder | Phase 3 implementation | Phase 1 just documents the difference |

**Key API fact (HIGH confidence from code inspection):**
- `content.rootFolder.childEntity` on vCenter contains `vim.Datacenter` objects
- `content.rootFolder.childEntity` on ESXi contains `vim.ComputeResource` objects directly
- This single difference is the root cause of all `needs-rewrite` classifications

---

## Open Questions

1. **ESXi `ha-datacenter` in upload_file_to_datastore dcPath parameter**
   - What we know: vCenter uses real datacenter name in `dcPath`; ESXi uses the pseudo-datacenter `ha-datacenter`
   - What's unclear: Whether ESXi actually requires the `dcPath` parameter at all, or whether it can be omitted
   - Recommendation: Document in audit that this requires live ESXi verification during Phase 2 implementation; note both options (`ha-datacenter` value or param omission)

2. **wait_for_updates traversal on ESXi without Datacenter objects**
   - What we know: The current traversal spec explicitly walks through `vim.Datacenter.vmFolder` and `vim.Datacenter.hostFolder` paths
   - What's unclear: Whether the tool is used at all in practice; if rootFolder traversal alone is sufficient for the ESXi object tree
   - Recommendation: Classify as needs-rewrite; Phase 2 implementor should verify the simplified traversal spec covers the ESXi object tree correctly

3. **upload_file_to_vm URL format on ESXi**
   - What we know: `InitiateFileTransferToGuest` returns a URL with `*` as the host, which is replaced with `config.vcenter_host`
   - What's unclear: Whether ESXi returns the same URL format, or a different wildcard/placeholder
   - Recommendation: Document as minor rewrite (config key rename); test on live ESXi during Phase 2

---

## Sources

### Primary (HIGH confidence)
- `/home/cars/src/github/cars/esxi-mcp-server/esxi_mcp_server/vmware_manager.py` — direct code inspection, all line numbers cited are verified
- `/home/cars/src/github/cars/esxi-mcp-server/esxi_mcp_server/mcp_server.py` — tool count and names verified (31 tools)
- `/home/cars/src/github/cars/esxi-mcp-server/.planning/REQUIREMENTS.md` — AUDIT-01, AUDIT-02 definitions

### Secondary (MEDIUM confidence)
- pyVmomi community knowledge: `content.rootFolder.childEntity` returns `vim.ComputeResource` on ESXi (not `vim.Datacenter`) — well-established in pyVmomi samples and community documentation
- `vim.StoragePod` is vCenter-only — confirmed by VMware API documentation that StoragePod/Storage DRS requires vCenter

### Tertiary (LOW confidence)
- ESXi `ha-datacenter` pseudo-datacenter name for datastore HTTP API — common knowledge from community sources but not verified against live ESXi in this research

---

## Metadata

**Confidence breakdown:**
- Tool classification (22/8/1 split): HIGH — based on direct code reading of vmware_manager.py
- ESXi vs vCenter object hierarchy: MEDIUM — based on established pyVmomi community knowledge; confirmed by code structure
- upload_file_to_datastore dcPath on ESXi: LOW — requires live ESXi testing to confirm
- wait_for_updates traversal fix: MEDIUM — traversal spec issue clearly identified; exact ESXi equivalent traversal needs validation

**Research date:** 2026-03-02
**Valid until:** 2026-04-02 (stable — pyVmomi API is stable; classifications won't change)
