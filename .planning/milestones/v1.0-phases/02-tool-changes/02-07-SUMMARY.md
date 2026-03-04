---
phase: 02-tool-changes
plan: "07"
subsystem: vmware_manager
tags: [clone_vm, ovftool, esxi, subprocess, gap-closure]
dependency_graph:
  requires: []
  provides: [clone_vm-ovftool-implementation]
  affects: [esxi_mcp_server/vmware_manager.py, Dockerfile]
tech_stack:
  added: [subprocess, shutil.which]
  patterns: [lazy-import-in-method, ovftool-vi-url-clone]
key_files:
  created: []
  modified:
    - esxi_mcp_server/vmware_manager.py
    - Dockerfile
decisions:
  - "Use lazy imports (shutil, subprocess inside method body) to avoid overhead on the common path"
  - "Pass credentials via vi:// URL — standard ovftool pattern for ESXi direct access"
  - "--noSSLVerify required because ESXi uses self-signed TLS certificates"
  - "600s timeout matches typical large VM export+import durations"
  - "CloneVM_Task reference retained only in docstring as explanatory context (no functional use)"
metrics:
  duration: 2min
  completed: "2026-03-03"
  tasks_completed: 2
  files_modified: 2
requirements:
  - RWRT-02
---

# Phase 02 Plan 07: clone_vm ovftool Rewrite Summary

**One-liner:** Rewrote clone_vm to use ovftool vi:// subprocess transfer instead of CloneVM_Task (vCenter-only API), with shutil.which PATH check and 600s timeout.

## What Was Built

The `clone_vm` method in `vmware_manager.py` previously called `VirtualMachine.CloneVM_Task` via the pyVmomi API — a vCenter-only operation that returns `vmodl.fault.NotSupported` on standalone ESXi. The method has been rewritten to use VMware's `ovftool` CLI, which supports a direct `vi://` → `vi://` export+import that works on standalone ESXi.

Key implementation details:
- `shutil.which("ovftool")` checks for the binary at startup of each call; raises `RuntimeError` with install instructions if not found
- Source and destination URLs use `vi://user:pass@host/vm-name` pattern
- `subprocess.run` with `capture_output=True`, `text=True`, `timeout=600`
- `--noSSLVerify` flag required for ESXi self-signed certificates
- `--name=new_name` sets the clone's display name
- Non-zero exit code raises `Exception` with stderr content for debugging
- `subprocess.TimeoutExpired` caught and re-raised as `Exception` with descriptive message
- Imports (`shutil`, `subprocess`) are lazy (inside method body) — avoids import overhead on every server start

The Dockerfile received a comment block before the Python packages copy step explaining that ovftool is a proprietary VMware binary, where to download it, and how to include it in the image build.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Rewrite clone_vm in vmware_manager.py to use ovftool | df96a2c | esxi_mcp_server/vmware_manager.py |
| 2 | Add ovftool installation comment to Dockerfile | 7f4c2ff | Dockerfile |

## Verification Results

1. `grep -n "ovftool" vmware_manager.py` — 10 lines, covering shutil.which check, RuntimeError message, URL construction, cmd list, logging, error handling
2. `template_vm.Clone\b` — 0 functional matches (docstring mention is explanatory only)
3. `grep -n "clone_vm" mcp_server.py` — tool still registered at line 40 (definition) and line 358 (handler mapping)
4. `grep -n "ovftool" Dockerfile` — 5 comment lines present

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

All files confirmed present. Both task commits verified in git log.
