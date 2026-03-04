# Phase 4: Documentation - Research

**Researched:** 2026-03-03
**Domain:** Documentation updates — Markdown, YAML, shell script, config files
**Confidence:** HIGH

## Summary

Phase 4 is a pure documentation update phase. All source code changes (Phase 2 tool removals/rewrites, Phase 3 config/code renames) are complete. The task is to make four user-facing files match the actual state of the codebase: `README.md`, `config.yaml.sample`, `docker-entrypoint.sh`, and `CLAUDE.md`.

Each file currently describes the old vCenter-centric server with `VCENTER_*` config keys, `datacenter` and `cluster` config options, and 31 tools. The code now runs against standalone ESXi only, uses `ESXI_*` environment variables and `esxi_*` YAML field names, and exposes 30 tools (`list_datastore_clusters` was removed in Phase 2). Every outdated reference was directly verified by reading the current source files.

**Primary recommendation:** Treat each file as an independent find-and-replace + editorial task. No new code, no logic changes — just documentation that accurately mirrors what `config.py`, `mcp_server.py`, and the rest of the codebase now do.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DOCS-01 | `README.md` updated: project description, config key names, tool list, connection instructions for standalone ESXi | Audit of README.md found every specific outdated section; replacement values verified from config.py and mcp_server.py |
| DOCS-02 | `config.yaml.sample` updated with new `ESXI_*` variable names and ESXi-specific comments | config.py shows exact field names and env var keys the loader expects; sample must match dataclass field names (esxi_host, esxi_user, esxi_password) not env var names |
| DOCS-03 | `docker-entrypoint.sh` updated to use new `ESXI_*` environment variable names | Full read of docker-entrypoint.sh shows every VCENTER_* reference; config.py env_map is authoritative list of expected env vars |
| DOCS-04 | `CLAUDE.md` updated to reflect new tool count, removed tools, and renamed config keys | CLAUDE.md currently says "31 MCP tools", "VCENTER_*" keys, "connects to vCenter"; all three are now wrong |
</phase_requirements>

## Standard Stack

### Core
| Component | Version | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| Markdown | — | README.md, CLAUDE.md | Files are already Markdown; no tooling change |
| YAML | — | config.yaml.sample | Already YAML; update field names and comments |
| Bash | — | docker-entrypoint.sh | Existing shell script; update variable names inline |

### Supporting
| Tool | Version | Purpose | When to Use |
|------|---------|---------|-------------|
| Python read of config.py | — | Ground truth for field names and env vars | Verify before writing any config example |
| mcp_server.py tool count | — | Ground truth for number of registered tools | Verify before writing any "N tools" claim |

No new libraries, frameworks, or installations are required. This phase is entirely editorial.

## Architecture Patterns

### Pattern: Authoritative Source → Documentation

Every documentation value must be derived from the actual codebase, not from prior documentation (which is the source of the current errors).

**Authoritative sources (verified during research):**

| Claim | Authoritative Source | Verified Value |
|-------|---------------------|----------------|
| Number of tools | `mcp_server.py` `types.Tool(` count | **30 tools** (31 original − 1 removed `list_datastore_clusters`) |
| Required env vars | `config.py` `env_map` keys | `ESXI_HOST`, `ESXI_USER`, `ESXI_PASSWORD` |
| Optional env vars | `config.py` `env_map` keys | `ESXI_DATASTORE`, `ESXI_NETWORK`, `ESXI_INSECURE` |
| Server env vars | `config.py` `env_map` keys | `MCP_API_KEY`, `MCP_LOG_FILE`, `MCP_LOG_LEVEL` |
| YAML field names | `Config` dataclass fields | `esxi_host`, `esxi_user`, `esxi_password`, `datastore`, `network`, `insecure`, `api_key`, `log_file`, `log_level` |
| Removed fields | `Config` dataclass | `datacenter` and `cluster` fields **do not exist** |
| Removed tool | `mcp_server.py` | `list_datastore_clusters` is **not registered** |
| Connection target | `vmware_manager.py` | Standalone ESXi host; **no vCenter** |
| Method name | `vmware_manager.py` | `_connect_esxi()` (not `_connect_vcenter()`) |

### Pattern: Section-by-Section File Analysis

Each target file has been read and the outdated sections catalogued below (see Code Examples). The plan tasks should map one-to-one to logical sections within each file.

### Anti-Patterns to Avoid
- **Updating env var names but leaving YAML field names unchanged:** The config.yaml.sample uses YAML field names (`esxi_host`) not env var names (`ESXI_HOST`). These are different and both must be correct.
- **Leaving `datacenter` and `cluster` as "Optional" with empty values:** These fields have been removed from the `Config` dataclass. Providing them in a YAML file will cause a `TypeError` on startup (unexpected keyword argument). They must be completely absent from the sample.
- **Claiming "31 tools" after listing 30:** The count must match the actual registered tools. `list_datastore_clusters` was removed; 30 tools are now registered.
- **Introducing `VCENTER_*` env vars in docker-entrypoint.sh echo lines:** The diagnostic echo at line 87 still references `${VCENTER_HOST:-'from config file'}` and `${VCENTER_USER:-'from config file'}` — these will silently display wrong/empty values.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Finding all VCENTER_* occurrences | Manual scan | Read each file top-to-bottom with line numbers | Files are small; a systematic read catches every occurrence |
| Knowing correct tool count | Counting from old docs | `grep -c 'types\.Tool(' mcp_server.py` | Docs say 31, code has 30 |
| Knowing correct YAML keys | Guessing | Read `Config` dataclass in `config.py` | YAML keys must match dataclass field names exactly |

## Common Pitfalls

### Pitfall 1: YAML Key Names vs Environment Variable Names
**What goes wrong:** Writer uses `ESXI_HOST` as a YAML key (matching env var) instead of `esxi_host` (matching dataclass field). The YAML loader passes the key directly to `Config(**config_data)`, so the wrong key causes a TypeError.
**Why it happens:** The env_map in config.py maps env var names to field names. They look similar but are different: `ESXI_HOST` (env var) vs `esxi_host` (YAML key / dataclass field).
**How to avoid:** Use Config dataclass field names in config.yaml.sample, not env var names. Verified field names: `esxi_host`, `esxi_user`, `esxi_password`, `datastore`, `network`, `insecure`, `api_key`, `log_file`, `log_level`.
**Warning signs:** Any YAML key in ALL_CAPS is wrong.

### Pitfall 2: Incomplete Variable Replacement in docker-entrypoint.sh
**What goes wrong:** The heredoc section is updated but the diagnostic `echo` lines at the bottom of the file still reference `VCENTER_HOST` and `VCENTER_USER`.
**Why it happens:** The file has two distinct areas that reference host/user: the config generation block (lines 52-65) and the status output block (lines 87-89). Both must be updated.
**How to avoid:** Update ALL occurrences: `validate_env` required_vars array, heredoc template keys, optional variable conditionals, AND the echo status lines.

### Pitfall 3: README Config Table Still Lists Removed Fields
**What goes wrong:** The Configuration table (line 252-260 in README.md) retains `datacenter` and `cluster` rows after other updates.
**Why it happens:** The table is a separate section from the code block example. Easy to update one and miss the other.
**How to avoid:** Update both the YAML code block example AND the parameter reference table in the same task.

### Pitfall 4: CLAUDE.md Tool Count Inconsistency
**What goes wrong:** CLAUDE.md says "31 MCP tools" in the overview paragraph but a tool list section counts 30.
**Why it happens:** The overview was not updated when `list_datastore_clusters` was removed.
**How to avoid:** Update the tool count in the overview paragraph to 30 and note which tool was removed.

## Code Examples

Verified patterns from actual codebase files:

### Correct config.yaml.sample (to replace current file)
```yaml
# Current file has: vcenter_host, vcenter_user, vcenter_password, datacenter, cluster
# Must become (YAML keys = Config dataclass field names):
esxi_host: "192.168.0.1"          # ESXi host IP address or hostname
esxi_user: "root"                   # ESXi username
esxi_password: "s3cr3t"            # ESXi password
datastore: "datastore1"             # Default datastore name (optional)
network: "VM Network"               # Default network name (optional)
insecure: true                      # Skip SSL certificate verification
api_key: "s3cr3t-api-key"          # API key for authentication
log_file: "./logs/esxi_mcp.log"    # Log file path (optional)
log_level: "DEBUG"                  # Log level: DEBUG/INFO/WARNING/ERROR
# NOTE: datacenter and cluster are NOT valid keys — removed in ESXi-only pivot
```

### Correct docker-entrypoint.sh required_vars (line 30-31)
```bash
# Current: local required_vars=("VCENTER_HOST" "VCENTER_USER" "VCENTER_PASSWORD")
# Must become:
local required_vars=("ESXI_HOST" "ESXI_USER" "ESXI_PASSWORD")
```

### Correct docker-entrypoint.sh heredoc (lines 52-65)
```bash
# Current uses VCENTER_HOST, VCENTER_USER, VCENTER_PASSWORD, VCENTER_DATACENTER,
# VCENTER_CLUSTER, VCENTER_DATASTORE, VCENTER_NETWORK, VCENTER_INSECURE
# Must become:
cat > "$config_file" << EOF
esxi_host: "${ESXI_HOST}"
esxi_user: "${ESXI_USER}"
esxi_password: "${ESXI_PASSWORD}"
EOF

[ -n "$ESXI_DATASTORE" ] && echo "datastore: \"${ESXI_DATASTORE}\"" >> "$config_file"
[ -n "$ESXI_NETWORK" ] && echo "network: \"${ESXI_NETWORK}\"" >> "$config_file"
[ -n "$ESXI_INSECURE" ] && echo "insecure: ${ESXI_INSECURE}" >> "$config_file"
[ -n "$MCP_API_KEY" ] && echo "api_key: \"${MCP_API_KEY}\"" >> "$config_file"
[ -n "$MCP_LOG_LEVEL" ] && echo "log_level: \"${MCP_LOG_LEVEL}\"" >> "$config_file"
# Remove VCENTER_DATACENTER and VCENTER_CLUSTER lines entirely (fields removed from Config)
```

### Correct docker-entrypoint.sh echo lines (lines 87-89)
```bash
# Current:
echo "  Host: ${VCENTER_HOST:-'from config file'}"
echo "  User: ${VCENTER_USER:-'from config file'}"
# Must become:
echo "  Host: ${ESXI_HOST:-'from config file'}"
echo "  User: ${ESXI_USER:-'from config file'}"
```

### Correct CLAUDE.md Overview paragraph (line 7)
```
# Current:
ESXi MCP Server is a Python MCP (Model Control Protocol) server for managing VMware ESXi/vCenter infrastructure. It exposes 31 MCP tools for VM lifecycle, snapshots, host management, guest operations, and OVA/OVF deployment.

# Must become:
ESXi MCP Server is a Python MCP (Model Control Protocol) server for managing VMware ESXi hosts. It exposes 30 MCP tools for VM lifecycle, snapshots, host management, guest operations, and OVA/OVF deployment. Supports both HTTP (Streamable HTTP on port 8080) and stdio transports.
```

### Correct CLAUDE.md Configuration section (lines 77-80)
```markdown
# Current:
- Required: `VCENTER_HOST`, `VCENTER_USER`, `VCENTER_PASSWORD`
- Optional: `VCENTER_DATACENTER`, `VCENTER_CLUSTER`, `VCENTER_DATASTORE`, `VCENTER_NETWORK`, `VCENTER_INSECURE`

# Must become:
- Required: `ESXI_HOST`, `ESXI_USER`, `ESXI_PASSWORD`
- Optional: `ESXI_DATASTORE`, `ESXI_NETWORK`, `ESXI_INSECURE`
- Server: `MCP_API_KEY`, `MCP_LOG_FILE`, `MCP_LOG_LEVEL`
```

### Correct CLAUDE.md __main__.py description (line 66)
```markdown
# Current:
- **`__main__.py`** - CLI entry point: parses args, loads config, connects to vCenter, creates MCP server, starts selected transport.

# Must become:
- **`__main__.py`** - CLI entry point: parses args, loads config, connects to ESXi, creates MCP server, starts selected transport.
```

### Current README.md outdated sections (verified at these line numbers)
- Line 3: "ESXi/vCenter management server" → "ESXi management server (standalone ESXi only)"
- Line 7: "Support for ESXi and vCenter Server connections" → remove or change to "Standalone ESXi connection"
- Line 22: "Clone VM" feature → note that clone_vm uses ovftool vi:// subprocess
- Lines 62-74: YAML config example block — replace all vcenter_* keys with esxi_* keys, remove datacenter/cluster
- Lines 252-260: Configuration parameter table — replace vcenter_* rows, remove datacenter/cluster rows
- Lines 299-306: Environment Variables list — replace with ESXI_* names, remove VCENTER_DATACENTER/CLUSTER

## Scope: Files In vs Out

### In Scope (per DOCS-01 through DOCS-04)
| File | Requirement | Key Changes |
|------|-------------|-------------|
| `README.md` | DOCS-01 | Description, config keys, env vars table, remove datacenter/cluster |
| `config.yaml.sample` | DOCS-02 | All YAML keys, remove datacenter/cluster keys |
| `docker-entrypoint.sh` | DOCS-03 | All VCENTER_* → ESXI_*, remove datacenter/cluster conditionals |
| `CLAUDE.md` | DOCS-04 | Tool count (31→30), removed tool name, config key names, "vCenter" refs |

### Out of Scope (NOT required by DOCS-01 through DOCS-04)
| File | Reason |
|------|--------|
| `README_DOCKER.md` | Not listed in any DOCS requirement |
| `README_ZH.md` | Not listed in any DOCS requirement |
| `TOOLS.md` | Not listed in any DOCS requirement (and doesn't reference list_datastore_clusters) |
| `EXAMPLES.md` | Not listed in any DOCS requirement |
| `TASKS_COMPLETED.md` | Historical record, not user-facing |

## Recommended Plan Structure

Phase 4 is small and all four requirements are independent (different files). The planner should create either:

**Option A: One plan per file (4 plans)** — cleanest, each plan focuses on a single file with no dependencies.

**Option B: Two plans** — one for config files (config.yaml.sample + docker-entrypoint.sh, both config-focused) and one for narrative docs (README.md + CLAUDE.md). Slightly fewer commits but each plan has more moving parts.

**Recommendation: Option A (4 plans, one per requirement).** Each plan is simple enough that one plan per file is clearer and safer. The smallest units of work that can be verified independently.

## Open Questions

1. **README_DOCKER.md and README_ZH.md contain the same outdated VCENTER_* references**
   - What we know: These files are not listed in DOCS-01 through DOCS-04
   - What's unclear: Whether they should be updated as part of this phase or a separate task
   - Recommendation: Keep out of scope for Phase 4 per the requirements. If the planner or user wants them updated, add as DOCS-05/DOCS-06. Do NOT include them in the existing four plans without explicit requirement coverage.

2. **README.md "Clone VM" section describes ovftool dependency**
   - What we know: clone_vm was rewritten to use ovftool subprocess in Phase 2 (plans 02-07, 02-08)
   - What's unclear: README currently says "Clone VM" without mentioning ovftool; should this be added?
   - Recommendation: Yes — add a note that clone_vm requires ovftool installed on the server host. The Dockerfile already has a comment about this (ovftool cannot be bundled). This is a correctness improvement within DOCS-01 scope.

## Sources

### Primary (HIGH confidence)
- `/home/cars/src/github/cars/esxi-mcp-server/esxi_mcp_server/config.py` — Config dataclass field names and env_map read directly
- `/home/cars/src/github/cars/esxi-mcp-server/esxi_mcp_server/mcp_server.py` — Tool count verified via `grep -c 'types\.Tool('` = 30
- `/home/cars/src/github/cars/esxi-mcp-server/README.md` — All outdated sections read with line numbers
- `/home/cars/src/github/cars/esxi-mcp-server/config.yaml.sample` — Current content read; all vcenter_* keys confirmed present
- `/home/cars/src/github/cars/esxi-mcp-server/docker-entrypoint.sh` — All VCENTER_* references read with line context
- `/home/cars/src/github/cars/esxi-mcp-server/CLAUDE.md` — Lines 7, 66, 77-80 verified as containing outdated content
- `.planning/REQUIREMENTS.md` — DOCS-01 through DOCS-04 scope confirmed
- `.planning/STATE.md` — Phase 3 completion confirmed; all vcenter refs removed from code

### Secondary (MEDIUM confidence)
- `.planning/ROADMAP.md` — Phase 4 success criteria cross-checked against research findings

## Metadata

**Confidence breakdown:**
- What files to change: HIGH — directly verified by reading each file
- What values to use: HIGH — derived from authoritative source files (config.py, mcp_server.py)
- Pitfalls: HIGH — identified by reading both code and docs carefully
- Out-of-scope files: HIGH — requirements list exactly four files

**Research date:** 2026-03-03
**Valid until:** N/A — static documentation task; findings are stable until code changes
