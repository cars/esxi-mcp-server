# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — ESXi Pivot

**Shipped:** 2026-03-04
**Phases:** 4 | **Plans:** 15 | **Timeline:** 2 days (2026-03-02 → 2026-03-04)

### What Was Built
- Classified all 31 MCP tools against pyVmomi API (22 compatible, 8 rewrites, 1 removed)
- Rewrote 8 tools to use ESXi-compatible `host_system.vm` folder and `ContainerView` patterns
- Replaced `clone_vm`'s `CloneVM_Task` with `ovftool vi://` subprocess (vCenter-only API had no ESXi equivalent)
- Renamed all config keys (`VCENTER_*` → `ESXI_*`) and internal method/field names throughout codebase
- Updated all user-facing docs (README, `config.yaml.sample`, `docker-entrypoint.sh`, `CLAUDE.md`)

### What Worked
- **Audit-first approach**: Phase 1 audit produced a detailed classification table that Phase 2 executors could consume directly without re-inspecting code. The "provides/requires" dependency graph in SUMMARYs worked well.
- **Gap closure phases**: Multiple verification failures in Phase 2 were caught by the gsd-verifier and closed via 02-05 through 02-08 gap closure plans. The process prevented shipping broken tools.
- **Research with line numbers**: Researcher agents that cited specific line numbers in their findings (e.g., "line 1074: vcenter_host reference") produced much more actionable plans than vague descriptions.
- **Parallel wave execution**: All 4 Phase 4 plans executed in parallel (independent files) and completed correctly with no merge conflicts.

### What Was Inefficient
- **Multiple gap closure rounds in Phase 2**: The host traversal pattern (`childEntity[0].host[0]`) was initially implemented incorrectly and required two additional gap-closure plans (02-06, 02-08) after the verifier caught the issues. Better upfront research on ESXi `ComputeResource` traversal would have avoided this.
- **`clone_vm` not flagged as vCenter-only in Phase 1 audit**: `CloneVM_Task` was missed as vCenter-only in the initial audit. It was discovered during Phase 2 execution, requiring an extra gap-closure plan (02-07). The audit criteria focused on "datacenter object references" but missed API-level vCenter-only methods.
- **ROADMAP.md plan checkboxes not auto-updated**: After Phase 3 and 4 execution, the milestone archival captured stale `[ ]` checkbox states for plans that were actually complete. Had to manually fix the archive.

### Patterns Established
- **ESXi VM folder pattern**: `host_system = content.rootFolder.childEntity[0].host[0]; vm_folder = host_system.vm` — use for all create/clone/deploy operations
- **ESXi ContainerView lifecycle**: `container = CreateContainerView(rootFolder, [vim.Type], True); items = container.view; container.Destroy()` — always call Destroy() to prevent resource leaks
- **ESXi dcPath**: `ha-datacenter` literal for OVF/datastore URL operations — ESXi built-in pseudo-datacenter name, always present
- **`ovftool` for clone_vm**: `vi://user:pass@host/ha-datacenter/vm/Name` URL format with `--acceptAllEulas` flag and 600s timeout

### Key Lessons
1. **Audit API-level vCenter-only methods, not just object references**: `CloneVM_Task`, `MigrateVM_Task`, and `RelocateVM_Task` are vCenter-only at the API level even if they don't reference `vim.Datacenter` objects directly.
2. **Gap closure is normal, not a failure**: Phase 2 required 3 gap closure plans. The verification loop worked as designed — better to catch problems pre-ship than post-ship.
3. **Config renames are high-blast-radius**: Renaming `VCENTER_*` → `ESXI_*` touched 4+ files (config.py, docker-entrypoint.sh, config.yaml.sample, CLAUDE.md, README.md). Centralizing the rename in Phase 3 (after tool rewrites) was the right call — avoids touching in-flux code.

### Cost Observations
- Model mix: 100% sonnet (researcher, planner, checker, executor, verifier all ran on sonnet)
- Sessions: ~4 (plan phase 1-4, execute phase 1-4, complete milestone)
- Notable: Parallel execution of Phase 2's 8 plans would have been faster; they ran sequentially due to dependency chains. Phase 4's 4 independent doc plans ran in parallel successfully.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Pattern |
|-----------|--------|-------|-------------|
| v1.0 | 4 | 15 | Audit-first pivot; gap closure verified by verifier |

### Top Lessons (Verified Across Milestones)

1. Run audit phase before any code changes when doing a major API migration
2. Gap closure plans are a feature of the process, not a sign of poor planning
