# Phase 2: Tool Changes - Research

**Researched:** 2026-03-02
**Domain:** pyVmomi vSphere API — vCenter-only tool removal and ESXi-compatible rewrites
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RMVL-01 | `list_datastore_clusters` tool removed — vCenter-only StoragePod concept, no ESXi equivalent | AUDIT.md confirms `vim.StoragePod` does not exist on standalone ESXi; removal affects 3 files (vmware_manager.py:682–696, mcp_server.py:146–150 + 374, tools.py:89–92) |
| RWRT-01 | `create_vm` rewritten to use ESXi host folder and host resource pool | AUDIT.md line-number-precise spec: lines 450, 455, 512 in vmware_manager.py; ESXi pattern uses `content.rootFolder.childEntity[0].host[0].vm` as folder |
| RWRT-02 | `clone_vm` rewritten to use ESXi-compatible folder and resource pool | AUDIT.md: only line 534 fallback needs changing; primary path at line 532 is already ESXi-compatible |
| RWRT-03 | `create_vm_custom` rewritten to use ESXi-compatible placement | AUDIT.md: lines 560, 565, 622 — identical pattern to `create_vm`; same ESXi replacement applies |
| RWRT-04 | `deploy_ovf` and `deploy_ova` verified to work on standalone ESXi | AUDIT.md: 4 changes each; ImportVApp folder must be `host_system.vm`; datastore/rp lookup must use `content.rootFolder` not `datacenter_obj` |
| RWRT-05 | Any remaining tools referencing `datacenter`, `cluster`, or `ComputeResource` updated | AUDIT.md: `upload_file_to_datastore` (dcPath param + URL), `upload_file_to_vm` (URL config key), `wait_for_updates` (`_build_traversal_spec` removes Datacenter traversal specs) |
</phase_requirements>

---

## Summary

Phase 2 is a **pure code modification task** with a complete, line-number-precise specification already produced by Phase 1. The AUDIT.md is the authoritative implementation guide — this research supplements it with the contextual knowledge needed to execute the changes correctly and avoid common mistakes.

The work divides cleanly into three categories: (1) one tool removal (`list_datastore_clusters` — delete from all three files), (2) three VM creation rewrites that share an identical ESXi pattern (`create_vm`, `clone_vm`, `create_vm_custom`), and (3) four miscellaneous rewrites with distinct concerns (`upload_file_to_vm`, `upload_file_to_datastore`, `deploy_ovf`/`deploy_ova`, `wait_for_updates`/`_build_traversal_spec`). The total change surface is approximately 20 targeted line substitutions across 3 files.

A critical scoping decision must be made before implementation: whether to also rename `self.config.vcenter_host` → `self.config.esxi_host` in `config.py` as part of Phase 2 (collapsing part of Phase 3 scope), or to leave those references temporarily broken and fix them in Phase 3. The AUDIT.md flags this as "Option A (recommended): rename simultaneously" for `upload_file_to_vm`, `upload_file_to_datastore`, `deploy_ovf`, and `deploy_ova`. The research below treats Option A as the correct choice and documents what that entails.

**Primary recommendation:** Execute changes in order — removal first, then three VM creation rewrites (all share the same ESXi pattern), then the four miscellaneous rewrites. Confirm the `_connect_vcenter()` init method is NOT modified in Phase 2 (that is Phase 3 scope); only individual tool method bodies are changed.

---

## Standard Stack

This phase modifies existing Python code. No new dependencies are required.

### Core
| Library | Version | Purpose | Already Present |
|---------|---------|---------|-----------------|
| pyVmomi | >=7.0 | vSphere API object model (`vim.*`, `vmodl.*`) | Yes — in requirements.txt |
| Python 3.11 | 3.11 | Runtime | Yes — Dockerfile |

### No New Installations Required

All changes are within the existing pyVmomi API surface. No new pip packages needed.

---

## Architecture Patterns

### Files Modified in Phase 2

Three files are modified. The modification pattern for each tool is:

```
vmware_manager.py  — the actual API call changes (primary)
mcp_server.py      — tool definition + handler map entry (only for removal)
tools.py           — handler method (only for removal)
```

Rewrites only touch `vmware_manager.py`. Removal touches all three.

### Pattern 1: Tool Removal (RMVL-01)

**What:** Remove `list_datastore_clusters` entirely from all three files.
**When to use:** Tool uses `vim.StoragePod` — a vCenter-only type with no ESXi equivalent.

Delete these three blocks:

**vmware_manager.py lines 682–696:**
```python
# DELETE THIS ENTIRE METHOD:
def list_datastore_clusters(self) -> list:
    """List all datastore clusters (StoragePods)."""
    clusters = []
    container = self.content.viewManager.CreateContainerView(
        self.content.rootFolder, [vim.StoragePod], True)
    for pod in container.view:
        cluster_info = {
            "name": pod.name,
            "capacity_gb": round(pod.summary.capacity / (1024**3), 2) if pod.summary else 0,
            "free_space_gb": round(pod.summary.freeSpace / (1024**3), 2) if pod.summary else 0,
            "datastores": [ds.name for ds in pod.childEntity if isinstance(ds, vim.Datastore)]
        }
        clusters.append(cluster_info)
    container.Destroy()
    return clusters
```

**mcp_server.py:** Remove the `"list_datastore_clusters"` entry from the `tools` dict (lines 146–150) AND remove the corresponding entry from `tool_handler_map` (line 374).

**tools.py:** Remove the `list_datastore_clusters` method (lines 89–92).

### Pattern 2: ESXi VM Folder Replacement (RWRT-01, RWRT-02, RWRT-03)

**What:** Replace `self.datacenter_obj.vmFolder` with the ESXi host's `vm` folder property.

**ESXi equivalent (HIGH confidence — verified against pyVmomi API):**
```python
# Source: vmware_manager.py — ESXi object tree pattern from Phase 1 RESEARCH.md
# On ESXi: content.rootFolder.childEntity[0] is vim.ComputeResource (not vim.Datacenter)
# The host system is accessed via compute_resource.host[0]
# The host's VM folder is host_system.vm (this is a vim.Folder object)

host_system = self.content.rootFolder.childEntity[0].host[0]
vm_folder = host_system.vm  # vim.Folder — ESXi equivalent of datacenter_obj.vmFolder
```

**ESXi datastore lookup replacement (for `create_vm` and `create_vm_custom`):**
```python
# Replace: self.datacenter_obj.datastoreFolder.childEntity (filtered by name)
# With: ContainerView on rootFolder
container = self.content.viewManager.CreateContainerView(
    self.content.rootFolder, [vim.Datastore], True)
datastore_obj = next(
    (ds for ds in container.view if ds.name == datastore), None)
container.Destroy()
```

**ESXi network lookup replacement (for `create_vm` and `create_vm_custom`):**
```python
# Replace: self.datacenter_obj.networkFolder.childEntity (filtered by name)
# With: ContainerView on rootFolder
container = self.content.viewManager.CreateContainerView(
    self.content.rootFolder, [vim.Network], True)
network_obj = next(
    (net for net in container.view if net.name == network), None)
container.Destroy()
```

**Important:** `self.resource_pool` used in `create_vm` (line 515), `clone_vm` (line 536), and `create_vm_custom` (line 624) is set by `_connect_vcenter()` during init. This cached value is NOT fixed in Phase 2 — it remains broken until Phase 3 rewrites `_connect_vcenter()`. The three VM creation tools will only be fully functional end-to-end after Phase 3 completes. Phase 2 corrects the folder/lookup references; Phase 3 corrects the resource pool source.

### Pattern 3: deploy_ovf and deploy_ova Rewrites (RWRT-04)

Both methods share identical structure. Apply the same 4-change pattern to each:

**Change 1 — Datastore lookup (lines 1026 / 1140):**
```python
# REMOVE:
for ds in self.datacenter_obj.datastoreFolder.childEntity:
    if isinstance(ds, vim.Datastore) and ds.name == datastore_name:
        ...

# REPLACE WITH:
container = self.content.viewManager.CreateContainerView(
    self.content.rootFolder, [vim.Datastore], True)
for ds in container.view:
    if ds.name == datastore_name:
        ...
container.Destroy()
```

**Change 2 — Resource pool lookup (lines 1037–1038 / 1150–1151):**
```python
# REMOVE:
container = self.content.viewManager.CreateContainerView(
    self.datacenter_obj, [vim.ResourcePool], True)

# REPLACE WITH:
container = self.content.viewManager.CreateContainerView(
    self.content.rootFolder, [vim.ResourcePool], True)
```

**Change 3 — ImportVApp folder argument (lines 1061 / 1174):**
```python
# REMOVE:
lease = resource_pool.ImportVApp(
    import_spec.importSpec, self.datacenter_obj.vmFolder)

# REPLACE WITH:
host_system = self.content.rootFolder.childEntity[0].host[0]
lease = resource_pool.ImportVApp(
    import_spec.importSpec, host_system.vm)
```

**Change 4 — URL host substitution (lines 1072 / 1220) — Option A: rename config key now:**
```python
# deploy_ovf line 1072:
# REMOVE: url = lease.info.deviceUrl[0].url.replace('*', self.config.vcenter_host)
# REPLACE WITH: url = lease.info.deviceUrl[0].url.replace('*', self.config.esxi_host)

# deploy_ova line 1220:
# REMOVE: url = device_url.url.replace('*', self.config.vcenter_host)
# REPLACE WITH: url = device_url.url.replace('*', self.config.esxi_host)
```

### Pattern 4: upload_file_to_vm Rewrite (RWRT-05, partial)

**What:** Line 940 only — URL host substitution config key rename.

```python
# REMOVE (line 940):
url = re.sub(r"^https://\*:", f"https://{self.config.vcenter_host}:", url)

# REPLACE WITH (Option A — rename config key now):
url = re.sub(r"^https://\*:", f"https://{self.config.esxi_host}:", url)
```

### Pattern 5: upload_file_to_datastore Rewrite (RWRT-05, partial)

**What:** Two changes — dcPath parameter and URL host.

```python
# REMOVE (line 976):
"dcPath": self.datacenter_obj.name

# REPLACE WITH (Option A — use ESXi pseudo-datacenter name):
"dcPath": "ha-datacenter"

# REMOVE (line 978):
http_url = f"https://{self.config.vcenter_host}:443{resource}"

# REPLACE WITH (Option A — rename config key now):
http_url = f"https://{self.config.esxi_host}:443{resource}"
```

### Pattern 6: wait_for_updates / _build_traversal_spec Rewrite (RWRT-05, partial)

**What:** Remove the two Datacenter traversal specs from `_build_traversal_spec()` and simplify `folder_to_child.selectSet`.

```python
# SOURCE: vmware_manager.py lines 1336–1372
# CURRENT: returns [folder_to_child, dc_to_vmfolder, dc_to_hostfolder]
# ESXi REPLACEMENT: returns [folder_to_child] only

def _build_traversal_spec(self):
    """Build traversal spec for property collector (ESXi-compatible)."""
    from pyVmomi import vmodl

    # On ESXi: rootFolder -> ComputeResource (direct child, no Datacenter wrapper)
    # folderToChild traversal is sufficient; remove dcToVmFolder and dcToHostFolder
    folder_to_child = vmodl.query.PropertyCollector.TraversalSpec(
        name='folderToChild',
        type=vim.Folder,
        path='childEntity',
        skip=False,
        selectSet=[vmodl.query.PropertyCollector.SelectionSpec(name='folderToChild')]
    )

    return [folder_to_child]
```

**Key:** The `selectSet` on `folder_to_child` in the current code references `dcToVmFolder` and `dcToHostFolder`. In the ESXi replacement, `folder_to_child` only references itself (recursive folderToChild traversal).

### Pattern 7: Config Key Rename (Option A — in-scope for Phase 2)

If Option A is chosen (rename `vcenter_host` to `esxi_host` in Phase 2), the following changes are required in `config.py` and `vmware_manager.py`:

**config.py — rename field and env var mapping:**
```python
# Config dataclass: vcenter_host -> esxi_host (and vcenter_user, vcenter_password)
@dataclass
class Config:
    esxi_host: str       # was: vcenter_host
    esxi_user: str       # was: vcenter_user
    esxi_password: str   # was: vcenter_password
    ...

# env_map: add ESXI_HOST -> esxi_host mapping (at minimum for the host key)
# Phase 2 scope: rename only host, user, password; defer datacenter/cluster/datastore/network to Phase 3
```

**vmware_manager.py — connect call uses new field names:**
```python
# Lines 47, 54: self.config.vcenter_host -> self.config.esxi_host
# Lines 49, 56: self.config.vcenter_user -> self.config.esxi_user
# Lines 50: self.config.vcenter_password -> self.config.esxi_password  (already named pwd)
```

**Note:** If the planner chooses Option B (keep `vcenter_host` temporarily), the four URL substitution changes in upload_file_to_vm, upload_file_to_datastore, deploy_ovf, and deploy_ova should use `self.config.vcenter_host` and be left for Phase 3 to update. Document the choice in the plan so Phase 3 knows what remains.

### Anti-Patterns to Avoid

- **Touching `_connect_vcenter()` init logic in Phase 2:** The datacenter_obj, resource_pool, datastore_obj, and network_obj resolution in `_connect_vcenter()` lines 64–127 is Phase 3 scope. Do NOT modify it in Phase 2. Tools that rely on `self.datastore_obj` and `self.resource_pool` from init will remain partially broken until Phase 3 — this is expected and acceptable.
- **Missing the Container view Destroy() call:** When adding ContainerView-based lookups, always call `container.Destroy()` after use to release server-side resources. The existing list_datastores pattern in the codebase shows this correctly.
- **Removing the DVS isinstance check from create_vm / create_vm_custom:** The `isinstance(network_obj, vim.dvs.DistributedVirtualPortgroup)` branch in create_vm (lines 499–505) and create_vm_custom (lines 610–615) is defensive code that is harmless on ESXi (never fires). Leave it in place — do not remove it.
- **Assuming host[0] always exists:** The pattern `content.rootFolder.childEntity[0].host[0]` assumes a single ComputeResource with at least one host. On a properly configured standalone ESXi host this is always true. But add a guard or let it fail naturally — do not add complex fallback logic.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Datastore lookup without datacenter | Custom traversal logic | `CreateContainerView(rootFolder, [vim.Datastore], True)` | Already used by `list_datastores`; works identically on ESXi |
| Network lookup without datacenter | Custom traversal | `CreateContainerView(rootFolder, [vim.Network], True)` | Already used by `list_networks`; works identically on ESXi |
| Resource pool search without datacenter | Custom tree walk | `CreateContainerView(rootFolder, [vim.ResourcePool], True)` | Standard pyVmomi pattern; rootFolder traversal covers all ESXi resource pools |

**Key insight:** The project already uses `CreateContainerView(rootFolder, ...)` for listing VMs, datastores, networks, hosts. The rewrites simply extend this established pattern to the four tool methods that currently use `datacenter_obj` as the container root instead of `rootFolder`.

---

## Common Pitfalls

### Pitfall 1: Modifying _connect_vcenter() scope creep
**What goes wrong:** Implementor notices `_connect_vcenter()` also uses `datacenter_obj` (lines 64–127) and "fixes" it during Phase 2.
**Why it happens:** The method looks broken, and it is — but it's Phase 3 scope. Touching it in Phase 2 could accidentally break the `self.resource_pool` and `self.datastore_obj` that 22 ESXi-compatible tools depend on.
**How to avoid:** Limit Phase 2 changes strictly to the tool method bodies listed in AUDIT.md. `_connect_vcenter()` remains unchanged until Phase 3.
**Warning signs:** Editing lines 64–127 of vmware_manager.py.

### Pitfall 2: Missing Datacenter reference in deploy_ methods
**What goes wrong:** Only fixing the `ImportVApp` folder argument (the most obvious change) and missing the datastore lookup loop and resource pool ContainerView changes.
**Why it happens:** Each deploy_ method has 3–4 datacenter references. Only fixing one leaves AttributeError at runtime.
**How to avoid:** Use the AUDIT.md change table for deploy_ovf and deploy_ova — 4 changes each. Verify all 4 are applied before moving on.
**Warning signs:** Method starts working but fails when a non-default datastore or resource pool name is specified.

### Pitfall 3: Forgetting to remove handler map entry from mcp_server.py
**What goes wrong:** `list_datastore_clusters` method deleted from `vmware_manager.py` and `tools.py` but `tool_handler_map` entry in `mcp_server.py` (line 374) remains, causing a runtime error when the tool is called.
**Why it happens:** `mcp_server.py` has two locations for each tool: the `tools` dict (definition) AND the `tool_handler_map` (handler lambda). Both must be removed.
**How to avoid:** Grep for `list_datastore_clusters` across all three files after the change and confirm zero results.
**Warning signs:** Server starts without error but calling the tool produces an AttributeError.

### Pitfall 4: Container view not destroyed after ContainerView-based lookup
**What goes wrong:** Server accumulates server-side container view objects, eventually causing memory pressure or view limit errors.
**Why it happens:** pyVmomi container views are server-side objects that must be explicitly destroyed.
**How to avoid:** Pattern is `container = ...; for x in container.view: ...; container.Destroy()`. The new lookup blocks added to create_vm, create_vm_custom, deploy_ovf, and deploy_ova must all call `container.Destroy()` after use.

### Pitfall 5: upload_file_to_datastore dcPath on ESXi
**What goes wrong:** Upload returns HTTP 404. Cause is unclear — could be wrong dcPath value or ESXi not supporting the parameter.
**Why it happens:** ESXi's datastore HTTP API may handle `dcPath` differently than vCenter.
**How to avoid:** Use `"ha-datacenter"` (Option A) as the first attempt. If live ESXi testing returns 404, try omitting the key entirely (Option B). Document which option worked. This is a known open question from Phase 1 — the implementation should note it explicitly in code as a comment.
**Warning signs:** HTTP 404 when uploading to a valid datastore path.

### Pitfall 6: wait_for_updates traversal spec on ESXi object tree
**What goes wrong:** The simplified `folderToChild`-only traversal may not discover VMs and hosts correctly if the ESXi object tree requires additional traversal specs to reach `vim.ComputeResource.host` and `.resourcePool` children.
**Why it happens:** The ESXi object tree is `rootFolder → ComputeResource → host/vm`. `folderToChild` traverses `Folder.childEntity` — it reaches `ComputeResource` but may not descend into its children without an additional `ComputeResource → host` spec.
**How to avoid:** The AUDIT.md recommendation (folderToChild only) is the correct starting point. If `wait_for_updates` returns empty results on live ESXi, add a `cr_to_host` TraversalSpec for `vim.ComputeResource → host`. This is flagged as requiring live ESXi validation.
**Warning signs:** `wait_for_updates` returns an update set with zero objects on ESXi.

---

## Code Examples

Verified patterns from code inspection (HIGH confidence):

### Existing ESXi-Compatible ContainerView Pattern
```python
# Source: vmware_manager.py list_datastores() — already ESXi-compatible
# This pattern is the model for all new datastore/network/rp lookups in Phase 2

container = self.content.viewManager.CreateContainerView(
    self.content.rootFolder, [vim.Datastore], True)
for ds in container.view:
    # ... process ds
container.Destroy()
```

### Complete create_vm ESXi Replacement (lines 449–515)
```python
# Source: AUDIT.md rewrite spec for create_vm (verified line numbers)

# Replace line 450 — datastore lookup:
if datastore:
    container = self.content.viewManager.CreateContainerView(
        self.content.rootFolder, [vim.Datastore], True)
    datastore_obj = next(
        (ds for ds in container.view
         if isinstance(ds, vim.Datastore) and ds.name == datastore), None)
    container.Destroy()
    if not datastore_obj:
        raise Exception(f"Specified datastore {datastore} not found")

# Replace line 455 — network lookup:
if network:
    container = self.content.viewManager.CreateContainerView(
        self.content.rootFolder, [vim.Network], True)
    network_obj = next(
        (net for net in container.view if net.name == network), None)
    container.Destroy()
    if not network_obj:
        raise Exception(f"Specified network {network} not found")

# Replace line 512 — VM folder:
host_system = self.content.rootFolder.childEntity[0].host[0]
vm_folder = host_system.vm  # vim.Folder on ESXi
```

### Complete _build_traversal_spec ESXi Replacement
```python
# Source: AUDIT.md rewrite spec for wait_for_updates (verified line numbers 1336–1372)

def _build_traversal_spec(self):
    """Build traversal spec for property collector (ESXi-compatible)."""
    from pyVmomi import vmodl

    folder_to_child = vmodl.query.PropertyCollector.TraversalSpec(
        name='folderToChild',
        type=vim.Folder,
        path='childEntity',
        skip=False,
        selectSet=[vmodl.query.PropertyCollector.SelectionSpec(name='folderToChild')]
    )

    return [folder_to_child]
```

### list_datastore_clusters Removal Verification Command
```bash
# Run after removal to confirm zero remaining references:
grep -rn "list_datastore_clusters\|StoragePod" \
    esxi_mcp_server/vmware_manager.py \
    esxi_mcp_server/mcp_server.py \
    esxi_mcp_server/tools.py
# Expected output: empty (no matches)
```

### Post-Change Verification for datacenter_obj References
```bash
# Run after all rewrites to confirm no datacenter_obj remains in tool method bodies:
grep -n "datacenter_obj\|vim\.ClusterComputeResource\|vim\.dvs\." \
    esxi_mcp_server/vmware_manager.py
# Expected: only references within _connect_vcenter() (lines 64–127)
# Any reference OUTSIDE lines 64–127 is a missed rewrite
```

---

## Implementation Order

The planner should sequence tasks in this order to minimize error surface:

1. **RMVL-01 first:** Remove `list_datastore_clusters` from all three files. Simple deletion; zero ESXi API knowledge required. Establishes the edit/verify loop.

2. **RWRT-01 + RWRT-02 + RWRT-03 together (or sequentially):** `create_vm`, `clone_vm`, `create_vm_custom` all share the same ESXi folder pattern. Batch these because the fix is identical. These tools will be partially fixed (folder correct, resource_pool still from broken init) — acceptable until Phase 3.

3. **RWRT-04:** `deploy_ovf` and `deploy_ova` together (same 4-change pattern each).

4. **RWRT-05:** `upload_file_to_vm`, `upload_file_to_datastore`, `wait_for_updates`/`_build_traversal_spec`. These are independent of each other; can be done in any sub-order.

5. **Config key rename (if Option A):** Update `config.py` field names and `env_map`. Update all `self.config.vcenter_host` references in `vmware_manager.py` that were changed in steps 3–4.

6. **Verification grep:** Confirm no `datacenter_obj`, `vim.ClusterComputeResource`, `vim.dvs.*`, or `StoragePod` references remain outside `_connect_vcenter()`.

---

## State of the Art

| Current Code | After Phase 2 | Phase 3 Still Needed |
|--------------|---------------|----------------------|
| `create_vm` uses `datacenter_obj.vmFolder` | Uses `host_system.vm` | `self.resource_pool` still sourced from broken `_connect_vcenter()` |
| `clone_vm` fallback uses `datacenter_obj.vmFolder` | Uses `host_system.vm` | `self.datastore_obj` still from broken init |
| `deploy_ovf/ova` uses `datacenter_obj.vmFolder` | Uses `host_system.vm` | Config `vcenter_host` field renamed here (Option A) |
| `list_datastore_clusters` exists | Removed completely | Nothing |
| `_build_traversal_spec` walks Datacenter paths | Walks only Folder/childEntity | Nothing (complete after Phase 2) |
| `upload_file_to_datastore` uses `datacenter_obj.name` | Uses `"ha-datacenter"` literal | Nothing |

---

## Open Questions

1. **`upload_file_to_datastore` dcPath on ESXi — `"ha-datacenter"` vs omit**
   - What we know: ESXi uses a pseudo-datacenter named `ha-datacenter` in its object model and datastore HTTP API
   - What's unclear: Whether ESXi requires the `dcPath` query parameter at all, or whether it can be omitted entirely
   - Recommendation: Implement with `"ha-datacenter"` (Option A from AUDIT.md). Add an inline comment noting this is an ESXi assumption requiring live testing verification. If 404 is returned, remove the `dcPath` key entirely.

2. **`wait_for_updates` traversal spec — folderToChild-only sufficient on ESXi?**
   - What we know: ESXi object tree is `rootFolder → ComputeResource (no Datacenter)`. Removing `dcToVmFolder` and `dcToHostFolder` is correct.
   - What's unclear: Whether `folderToChild` traversal alone reaches VMs and hosts inside `ComputeResource.host[]` on ESXi, or whether a `crToHost` TraversalSpec is also needed.
   - Recommendation: Implement folderToChild-only as specified. Note in code comment that this requires live ESXi validation. If `wait_for_updates` returns empty results, add `ComputeResource → host` traversal spec.

3. **Option A vs Option B for config key rename**
   - What we know: Four methods reference `self.config.vcenter_host`. AUDIT.md recommends Option A (rename simultaneously in Phase 2) to avoid leaving broken references.
   - What's unclear: Whether the planner will treat config rename as in-scope for Phase 2 or leave it entirely to Phase 3.
   - Recommendation: Option A. The change is small (4 references in vmware_manager.py + dataclass field rename in config.py) and prevents the confusion of Phase 3 implementors seeing `vcenter_host` in code that already uses `esxi_host`.

---

## Sources

### Primary (HIGH confidence)
- `/home/cars/src/github/cars/esxi-mcp-server/.planning/phases/01-audit/AUDIT.md` — authoritative rewrite specs with verified line numbers; direct output of Phase 1
- `/home/cars/src/github/cars/esxi-mcp-server/esxi_mcp_server/vmware_manager.py` — direct code inspection confirming AUDIT.md line numbers are accurate
- `/home/cars/src/github/cars/esxi-mcp-server/esxi_mcp_server/mcp_server.py` — confirmed tool definition and handler map structure
- `/home/cars/src/github/cars/esxi-mcp-server/esxi_mcp_server/tools.py` — confirmed handler delegation structure
- `/home/cars/src/github/cars/esxi-mcp-server/esxi_mcp_server/config.py` — confirmed `vcenter_host` field name and env_map structure

### Secondary (MEDIUM confidence)
- Phase 1 RESEARCH.md — ESXi vs vCenter object hierarchy; `content.rootFolder.childEntity[0]` is `vim.ComputeResource` on ESXi (established pyVmomi community knowledge, verified against code structure)
- pyVmomi community knowledge: `host_system.vm` is a `vim.Folder` on ESXi, usable as `CreateVM_Task` and `ImportVApp` folder argument

### Tertiary (LOW confidence)
- ESXi pseudo-datacenter name `"ha-datacenter"` for datastore HTTP API — widely cited in community sources but not verified against live ESXi in this project; flagged as requiring live testing

---

## Metadata

**Confidence breakdown:**
- Tool removal (RMVL-01): HIGH — trivial deletion; AUDIT.md provides exact blocks to remove
- VM creation rewrites (RWRT-01/02/03): HIGH — pattern verified from AUDIT.md; ESXi host.vm folder pattern is established
- deploy_ovf/ova rewrites (RWRT-04): HIGH — 4 changes per method clearly specified in AUDIT.md
- upload_file_to_vm rewrite (RWRT-05 partial): HIGH — one-line change; confirmed line number
- upload_file_to_datastore rewrite (RWRT-05 partial): MEDIUM — dcPath value on ESXi is LOW confidence; rest is HIGH
- wait_for_updates traversal rewrite (RWRT-05 partial): MEDIUM — folderToChild-only traversal correctness on ESXi requires live validation
- Config key rename (Option A): HIGH — straightforward field rename with confirmed impact locations

**Research date:** 2026-03-02
**Valid until:** 2026-04-02 (stable — pyVmomi API changes on these paths are rare)
