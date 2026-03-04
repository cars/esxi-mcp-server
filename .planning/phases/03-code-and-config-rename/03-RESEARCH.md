# Phase 3: Code and Config Rename - Research

**Researched:** 2026-03-03
**Domain:** Python refactoring — identifier rename, config key migration, datacenter/cluster dead-code removal
**Confidence:** HIGH

## Summary

Phase 3 is a pure rename and dead-code removal pass. No new logic is introduced; no external libraries are added. The codebase already completed the functional ESXi pivot in Phase 2. Phase 3 finishes the job by renaming every `VCENTER_*` / `vcenter_*` / `_connect_vcenter` surface area to its `ESXI_*` / `esxi_*` / `_connect_esxi` equivalent, and by deleting the datacenter-by-name and cluster-by-name lookup paths that no longer serve any purpose.

The scope is well-bounded: two Python files carry the bulk of the work (`config.py` and `vmware_manager.py`), with minor touches needed in `__init__.py` (module docstring). The `_connect_vcenter` method is the largest single change — it becomes `_connect_esxi` and sheds the conditional branches that branched on `self.config.datacenter` and `self.config.cluster`.

CONF-04 (simplify startup connection logic) requires careful thought: the datacenter object (`self.datacenter_obj`) is still used by `vmware_manager.py` at several call sites (lines 103, 110, 120, 1090, 1207). The datacenter object itself stays; only the code that conditionally *looked it up by name* (based on `self.config.datacenter` / `self.config.cluster`) is removed. The unconditional ESXi path — "take the first `vim.Datacenter` from `rootFolder.childEntity`" — is kept as the sole path.

**Primary recommendation:** Execute the rename in file order — `config.py` first, then `vmware_manager.py`, then `__init__.py` — so that each subsequent file edit can reference verified field names from the updated config.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CONF-01 | Rename env vars: `VCENTER_HOST` → `ESXI_HOST`, `VCENTER_USER` → `ESXI_USER`, `VCENTER_PASSWORD` → `ESXI_PASSWORD`, `VCENTER_INSECURE` → `ESXI_INSECURE` | `env_map` dict in `config.py` lines 54-66; four keys need renaming |
| CONF-02 | Remove `VCENTER_DATACENTER` and `VCENTER_CLUSTER` env vars and corresponding `Config` dataclass fields (`datacenter`, `cluster`) | `config.py` lines 13-20 (dataclass), lines 58-59 (env_map), lines 65-89 in `_connect_vcenter` (usage) |
| CONF-03 | Rename `VCENTER_DATASTORE` → `ESXI_DATASTORE`, `VCENTER_NETWORK` → `ESXI_NETWORK` | `env_map` in `config.py` lines 60-61 |
| CONF-04 | Remove datacenter and cluster resolution code from `VMwareManager._connect_vcenter()` (now `_connect_esxi()`) | Lines 64-95 of `vmware_manager.py`; datacenter-by-name and cluster-by-name branches removed; unconditional first-datacenter path remains |
| CODE-01 | Rename `_connect_vcenter()` → `_connect_esxi()` in `vmware_manager.py`; update all call sites | Definition line 38; call in `__init__` line 25; call in `_ensure_connected` line 36 |
| CODE-02 | Rename `Config` dataclass fields: `vcenter_user` → `esxi_user`, `vcenter_password` → `esxi_password` | `config.py` lines 13-14; `required_keys` list line 78; all `self.config.vcenter_user` / `self.config.vcenter_password` references in `vmware_manager.py` |
| CODE-03 | Update comments, docstrings, log messages to reference ESXi instead of vCenter | 8 occurrences in `vmware_manager.py`; 1 in `__init__.py` |
| CODE-04 | `mcp_server.py` and `tools.py` updated to remove vCenter-specific references (if any remain) | No `vcenter`/`vCenter` strings found in these files; only minor docstring cleanup needed |
</phase_requirements>

## Standard Stack

### Core (no additions needed)
| File | Current State | Phase 3 Changes |
|------|--------------|-----------------|
| `config.py` | `vcenter_user`, `vcenter_password` dataclass fields; `VCENTER_*` env map | Rename fields and env keys; remove `datacenter`/`cluster` fields |
| `vmware_manager.py` | `_connect_vcenter()` method; `self.config.vcenter_user/password` refs; datacenter/cluster branch code | Rename method; update field refs; remove branches |
| `__init__.py` | Module docstring mentions vCenter | Update docstring |
| `mcp_server.py` | No `vcenter` strings found | No code changes needed |
| `tools.py` | No `vcenter` strings found | No code changes needed |

**Installation:** No new packages required.

## Architecture Patterns

### Complete Inventory of Changes

This phase is enumeration-driven. Every change is a known location in a small set of files.

#### config.py — Full Change Map

**Dataclass fields to rename:**
```python
# BEFORE (lines 13-14)
vcenter_user: str
vcenter_password: str

# AFTER
esxi_user: str
esxi_password: str
```

**Fields to remove entirely:**
```python
# REMOVE (lines 15-16)
datacenter: Optional[str] = None
cluster: Optional[str] = None
```

**env_map changes (lines 54-66):**
```python
# BEFORE
env_map = {
    "VCENTER_HOST": "esxi_host",       # already renamed in Phase 2
    "VCENTER_USER": "vcenter_user",    # rename env key + value
    "VCENTER_PASSWORD": "vcenter_password",  # rename env key + value
    "VCENTER_DATACENTER": "datacenter",     # REMOVE
    "VCENTER_CLUSTER": "cluster",           # REMOVE
    "VCENTER_DATASTORE": "datastore",       # rename env key only
    "VCENTER_NETWORK": "network",           # rename env key only
    "VCENTER_INSECURE": "insecure",         # rename env key only
    "MCP_API_KEY": "api_key",               # unchanged
    "MCP_LOG_FILE": "log_file",             # unchanged
    "MCP_LOG_LEVEL": "log_level"            # unchanged
}

# AFTER
env_map = {
    "ESXI_HOST": "esxi_host",
    "ESXI_USER": "esxi_user",
    "ESXI_PASSWORD": "esxi_password",
    "ESXI_DATASTORE": "datastore",
    "ESXI_NETWORK": "network",
    "ESXI_INSECURE": "insecure",
    "MCP_API_KEY": "api_key",
    "MCP_LOG_FILE": "log_file",
    "MCP_LOG_LEVEL": "log_level"
}
```

**required_keys update (line 78):**
```python
# BEFORE
required_keys = ["esxi_host", "vcenter_user", "vcenter_password"]

# AFTER
required_keys = ["esxi_host", "esxi_user", "esxi_password"]
```

#### vmware_manager.py — Full Change Map

**Method rename + call site update:**
```python
# BEFORE: definition (line 38), called at lines 25 and 36
def _connect_vcenter(self):
    ...
self._connect_vcenter()   # __init__ line 25
self._connect_vcenter()   # _ensure_connected line 36

# AFTER
def _connect_esxi(self):
    ...
self._connect_esxi()
self._connect_esxi()
```

**Field reference updates (lines 48-49, 55-56, 548, 552):**
```python
# BEFORE
user=self.config.vcenter_user,
pwd=self.config.vcenter_password,
# in clone_vm lines 548, 552:
f"vi://{self.config.vcenter_user}:{self.config.vcenter_password}@..."

# AFTER
user=self.config.esxi_user,
pwd=self.config.esxi_password,
f"vi://{self.config.esxi_user}:{self.config.esxi_password}@..."
```

**Dead code removal in `_connect_esxi()` — datacenter lookup simplification (CONF-04):**

The existing conditional datacenter lookup (lines 65-77) branches on `self.config.datacenter` (which is removed). The `else` branch — "take the first `vim.Datacenter`" — is the correct ESXi path. Keep only that path:

```python
# REMOVE the if/else entirely; replace with the unconditional ESXi path:
self.datacenter_obj = next((dc for dc in self.content.rootFolder.childEntity
                            if isinstance(dc, vim.Datacenter)), None)
if not self.datacenter_obj:
    raise Exception("No datacenter found on ESXi host")
```

**Dead code removal — cluster lookup simplification (CONF-04):**

The existing conditional cluster lookup (lines 81-95) branches on `self.config.cluster`. The `else` branch — "take the first `vim.ComputeResource`" — is the correct ESXi path. Keep only that path:

```python
# REMOVE the if/else; replace with unconditional path:
compute_resource = next((cr for cr in self.datacenter_obj.hostFolder.childEntity
                          if isinstance(cr, vim.ComputeResource)), None)
if not compute_resource:
    raise Exception("No compute resource found on ESXi host")
self.resource_pool = compute_resource.resourcePool
self.compute_resource = compute_resource
logging.info(f"Using resource pool: {self.resource_pool.name}")
```

**Log/docstring updates:**
```
Line 28 docstring: "Check if the vCenter session is still active" → "Check if the ESXi session is still active"
Line 35 log: "vCenter/ESXi session expired or lost, reconnecting..." → "ESXi session expired or lost, reconnecting..."
Line 39 docstring: "Connect to vCenter/ESXi and retrieve..." → "Connect to ESXi and retrieve..."
Line 58 log: "Failed to connect to vCenter/ESXi: {e}" → "Failed to connect to ESXi: {e}"
Line 62 log: "Successfully connected to VMware vCenter/ESXi API" → "Successfully connected to VMware ESXi API"
Line 536 docstring: already correctly notes "CloneVM_Task requires vCenter" — keep as-is (factual note)
Line 722 docstring: "Wait for a vCenter task to complete" → "Wait for a task to complete"
```

#### __init__.py — Single line update
```python
# BEFORE (line 1)
"""ESXi MCP Server - A VMware ESXi/vCenter management server based on MCP."""

# AFTER
"""ESXi MCP Server - A VMware ESXi management server based on MCP."""
```

### What Does NOT Change

- `self.datacenter_obj` instance variable — still used at `vmware_manager.py` lines 103, 110, 120, 1090, 1207. The object stays; only the *selection logic* is simplified.
- `config.datastore` and `config.network` field *names* — only the env var keys change (CONF-01/CONF-03 rename env vars, not dataclass field names for datastore/network).
- `mcp_server.py` — no `vcenter`/`vCenter` strings present; no changes needed.
- `tools.py` — no `vcenter`/`vCenter` strings present; no changes needed.
- `config.yaml.sample`, `docker-entrypoint.sh`, `README.md` — Phase 4 scope.
- `config.yaml.sample` file's YAML keys — Phase 4 scope.

### Anti-Patterns to Avoid

- **Renaming `datastore` and `network` dataclass fields:** CONF-03 only renames the environment variable keys (`VCENTER_DATASTORE` → `ESXI_DATASTORE`). The internal dataclass field names (`datastore`, `network`) remain unchanged since they are already generic and correct.
- **Removing `self.datacenter_obj` usage:** The datacenter object is still a valid ESXi concept ("ha-datacenter"). Only the by-name selection code is removed, not the object itself.
- **Touching `docker-entrypoint.sh`:** That file still uses `VCENTER_HOST` etc. — this is Phase 4's problem (DOCS-03), not Phase 3.
- **Treating line 536 comment as a violation:** The comment "CloneVM_Task requires vCenter" is a factual technical explanation, not a config reference. Success criterion 4 targets config field names, log output, and docstrings — not embedded technical rationale comments.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead |
|---------|-------------|-------------|
| Finding all vcenter occurrences | Manual scanning | `grep -rn "vcenter\|vCenter\|VCENTER" esxi_mcp_server/ --include="*.py"` |
| Verifying no references remain | Manual review | Same grep after edits — zero output = success |

## Common Pitfalls

### Pitfall 1: Renaming env vars without updating BOTH the key and the mapped field name
**What goes wrong:** `"ESXI_USER": "vcenter_user"` maps a new env key to an old field name. The env var reads correctly but the Config dataclass still has `vcenter_user`.
**How to avoid:** When CONF-01/CONF-02 rename the env key, simultaneously rename the dataclass field (CODE-02). The `env_map` value must match the dataclass field name exactly.

### Pitfall 2: Removing datacenter field but leaving datacenter object usage
**What goes wrong:** Removing `config.datacenter` field causes `AttributeError` at startup if any code still tries to read `self.config.datacenter`.
**How to avoid:** After removing the field from `Config`, run a grep for `self.config.datacenter` to confirm zero hits remain. The only references are in the conditional branches being deleted.

### Pitfall 3: Removing cluster field but forgetting the error message reference
**What goes wrong:** `config.py` removes the `cluster` field but `vmware_manager.py` still has `self.config.cluster` in the branch being deleted. The branch must be deleted in the same pass.
**How to avoid:** CONF-02 and CONF-04 are tightly coupled — remove the config field AND the branch code in the same plan.

### Pitfall 4: Incorrect `required_keys` list after field rename
**What goes wrong:** `load_config()` validates required keys by name against `config_data` dict. After renaming `vcenter_user` → `esxi_user` in the dataclass, the env_map value must also be `esxi_user`, or the required_keys check will fail with "Missing required configuration item: esxi_user" even when ESXI_USER is set.
**How to avoid:** Keep `required_keys` in sync with the dataclass field names and `env_map` values.

### Pitfall 5: Forgetting `_ensure_connected` call site for `_connect_vcenter`
**What goes wrong:** Renaming the method definition but missing the call at line 36 inside `_ensure_connected`. The server starts fine but silently fails to reconnect after session expiry.
**How to avoid:** There are exactly three occurrences: definition (line 38), `__init__` call (line 25), `_ensure_connected` call (line 36). Update all three.

## Code Examples

### Verified: Current state of all vcenter references (from live code inspection)

**config.py — complete vcenter surface:**
```
line 13: vcenter_user: str                      # dataclass field
line 14: vcenter_password: str                  # dataclass field
line 55: "VCENTER_HOST": "esxi_host",           # env_map (host already uses esxi_host)
line 56: "VCENTER_USER": "vcenter_user",        # env_map
line 57: "VCENTER_PASSWORD": "vcenter_password", # env_map
line 58: "VCENTER_DATACENTER": "datacenter",    # env_map (field being removed)
line 59: "VCENTER_CLUSTER": "cluster",          # env_map (field being removed)
line 60: "VCENTER_DATASTORE": "datastore",      # env_map (env key rename only)
line 61: "VCENTER_NETWORK": "network",          # env_map (env key rename only)
line 62: "VCENTER_INSECURE": "insecure",        # env_map (env key rename)
line 78: required_keys = ["esxi_host", "vcenter_user", "vcenter_password"]
```

**vmware_manager.py — complete vcenter surface:**
```
line 25: self._connect_vcenter()                # __init__ call site
line 28: docstring "vCenter session"
line 35: log "vCenter/ESXi session expired"
line 36: self._connect_vcenter()                # _ensure_connected call site
line 38: def _connect_vcenter(self):            # method definition
line 39: docstring "Connect to vCenter/ESXi"
line 48: user=self.config.vcenter_user,
line 49: pwd=self.config.vcenter_password,
line 55: user=self.config.vcenter_user,
line 56: pwd=self.config.vcenter_password)
line 58: log "Failed to connect to vCenter/ESXi"
line 62: log "Successfully connected to VMware vCenter/ESXi API"
line 536: docstring "CloneVM_Task requires vCenter" (factual, may keep)
line 548: f"vi://{self.config.vcenter_user}:{self.config.vcenter_password}..."
line 552: f"vi://{self.config.vcenter_user}:{self.config.vcenter_password}..."
line 722: docstring "Wait for a vCenter task"
```

**__init__.py — complete vcenter surface:**
```
line 1: module docstring "VMware ESXi/vCenter management server"
```

### Post-change verification command
```bash
# Must return zero lines when Phase 3 is complete
grep -rn "vcenter\|vCenter\|VCENTER" /path/to/esxi_mcp_server/ --include="*.py"
# Acceptable surviving hits:
#   vmware_manager.py line 536: "CloneVM_Task requires vCenter" (factual comment, acceptable)
```

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| `VCENTER_HOST` env var | `ESXI_HOST` (after Phase 3) | Breaking change, greenfield acceptable per STATE.md |
| `vcenter_user` / `vcenter_password` Config fields | `esxi_user` / `esxi_password` | Field rename propagates to all SmartConnect calls |
| `_connect_vcenter()` with datacenter/cluster branches | `_connect_esxi()` unconditional | Datacenter name config is vCenter concept; ESXi always has exactly one datacenter |

## Open Questions

1. **The `clone_vm` docstring at line 536**
   - What we know: Contains "CloneVM_Task requires vCenter" as factual technical rationale
   - What's unclear: Success criterion 4 says "No `vcenter` string appears in... in-code docstrings". This docstring contains "vCenter".
   - Recommendation: Update to remove "vCenter" — rephrase as "CloneVM_Task is not supported on standalone ESXi hosts". This satisfies the success criterion while preserving the technical information.

2. **`VCENTER_HOST` backward compat vs Phase 3 scope**
   - What we know: Phase 2 (plan 02-05) partially renamed — `VCENTER_HOST` still in env_map but maps to `esxi_host` field. STATE.md notes "vcenter_user and vcenter_password renames deferred to Phase 3."
   - What's unclear: Does Phase 3 also remove `VCENTER_HOST` from env_map? Requirements say CONF-01 renames it to `ESXI_HOST`.
   - Recommendation: Yes — CONF-01 explicitly lists this rename. Replace `"VCENTER_HOST": "esxi_host"` with `"ESXI_HOST": "esxi_host"` in Phase 3.

## Sources

### Primary (HIGH confidence)
- Live code inspection of `esxi_mcp_server/config.py` — complete vcenter surface mapped
- Live code inspection of `esxi_mcp_server/vmware_manager.py` — complete vcenter surface mapped with line numbers
- Live code inspection of `esxi_mcp_server/__init__.py` — one-line docstring hit confirmed
- Live grep output: `grep -rn "vcenter|vCenter|VCENTER" esxi_mcp_server/ --include="*.py"` — exhaustive, 23 hits across 3 files

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` — requirement IDs and descriptions used as-is
- `.planning/STATE.md` decisions section — confirms Phase 2 deferred `vcenter_user`/`vcenter_password` renames to Phase 3

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no external dependencies; pure Python rename within a fully read codebase
- Architecture: HIGH — all change locations identified with exact line numbers from live code inspection
- Pitfalls: HIGH — derived from direct code analysis, not speculation

**Research date:** 2026-03-03
**Valid until:** Stable until any Phase 2 gap-closure plan modifies `config.py` or `vmware_manager.py` (check git log before executing)
