# Coding Conventions

**Analysis Date:** 2026-03-02

## Naming Patterns

**Files:**
- Lowercase with underscores (snake_case)
- Examples: `vmware_manager.py`, `mcp_server.py`, `transport.py`, `config.py`, `tools.py`
- Entry point: `__main__.py`
- Package marker: `__init__.py`

**Classes:**
- PascalCase
- Examples: `VMwareManager` (in `vmware_manager.py`), `Config` (in `config.py`), `ToolHandlers` (in `tools.py`)

**Functions/Methods:**
- snake_case for public methods
- Examples: `create_vm()`, `list_vms()`, `delete_vm()`, `power_on_vm()`
- snake_case with leading underscore for private/internal methods
- Examples: `_ensure_connected()`, `_connect_vcenter()`, `_check_auth()`, `_find_snapshot_by_name()`

**Variables:**
- snake_case throughout
- Examples: `vm_name`, `datastore_name`, `resource_pool`, `authenticated`, `config_data`
- Acronyms remain uppercase when part of name: `vcenter_host`, `vm_list`, `si` (ServiceInstance), `qs` (quickStats)

**Type Hints:**
- Python 3.7+ type hints used consistently
- Returns specified: `-> str`, `-> list`, `-> dict`, `-> Dict[str, Any]`, `-> Optional[vim.VirtualMachine]`
- Parameter types specified: `vm_name: str`, `cpu: int`, `memory: int`, `datastore: Optional[str]`
- Location: `vmware_manager.py` (1372 lines), `tools.py` (199 lines), `config.py` (83 lines), `mcp_server.py` (451 lines)

## Code Style

**Formatting:**
- No explicit formatter configured (no `.prettierrc`, `pyproject.toml`, or Black config detected)
- Manual style consistency across codebase
- Default PEP 8 style observed

**Linting:**
- No linter configuration found (no `.eslintrc`, `pylintrc`, or similar)
- Code follows implicit Python conventions

**Docstrings:**
- Triple-quoted docstrings for functions and classes
- Single-line format for simple functions: `"""Function description."""`
- Multi-line format for complex functions with parameter/return details
- Examples from `vmware_manager.py`:
  ```python
  def list_vms(self) -> list:
      """List all virtual machine names."""

  def get_vm_performance(self, vm_name: str) -> Dict[str, Any]:
      """Retrieve performance data (CPU, memory, storage, and network) for the specified virtual machine."""

  def load_config(config_path: Optional[str] = None) -> Config:
      """
      Load configuration from file or environment variables.

      Args:
          config_path: Path to configuration file (JSON or YAML)

      Returns:
          Config object with loaded configuration

      Raises:
          ValueError: If configuration file format is not supported
          Exception: If required configuration is missing
      """
  ```

## Import Organization

**Order:**
1. Standard library imports (`ssl`, `os`, `json`, `logging`, `argparse`, `asyncio`)
2. Third-party library imports (`pyVim`, `pyVmomi`, `yaml`, `pyyaml`, `uvicorn`, `anyio`, `mcp`)
3. Relative package imports (`.config`, `.vmware_manager`, `.tools`, `.mcp_server`, `.transport`)

**Examples from `vmware_manager.py`:**
```python
import ssl
import logging
from typing import Optional, Dict, Any

from pyVim import connect
from pyVmomi import vim, vmodl

from .config import Config
```

**Examples from `__main__.py`:**
```python
import os
import argparse
import logging
import anyio
import uvicorn

from mcp.server import stdio

from . import load_config, VMwareManager, ToolHandlers, create_mcp_server, register_handlers
from .transport import create_asgi_app
```

**Path Aliases:**
- Not used; direct relative imports with `.` notation
- Package-level exports via `__init__.py` using lazy loading pattern

## Error Handling

**Patterns:**
- Generic `Exception` raised with descriptive messages: `raise Exception(f"VM {vm_name} not found")`
- Logging errors with `logging.error()` before re-raising:
  ```python
  except Exception as e:
      logging.error(f"Failed to connect to vCenter/ESXi: {e}")
      raise
  ```
- Graceful degradation with logging.warning for non-critical failures:
  ```python
  except Exception as e:
      logging.warning(f"Failed to retrieve network performance data: {e}")
      stats["network_transmit_KBps"] = None
      stats["network_receive_KBps"] = None
  ```
- Bare `except:` used in async tasks (keepalive threads) where specific exception handling not needed
- Validation pattern: check for None or missing attributes, raise with context:
  ```python
  if not vm:
      raise Exception(f"Virtual machine {name} not found")
  ```

## Logging

**Framework:** Standard `logging` module (stdlib)

**Patterns:**
- Initialized in `__main__.py` via `setup_logging()` function
- Log levels: INFO (default), DEBUG, WARNING, ERROR
- Format: `"%(asctime)s [%(levelname)s] %(message)s"` with optional file output
- Logging to file if `config.log_file` set, console otherwise
- Location: `logging.info()`, `logging.warning()`, `logging.error()`
- Examples:
  - `logging.info("Successfully connected to VMware vCenter/ESXi API")`
  - `logging.warning("vCenter/ESXi session expired or lost, reconnecting...")`
  - `logging.error(f"Failed to delete virtual machine: {e}")`

## Comments

**When to Comment:**
- Inline comments explain non-obvious VMware API behavior
- Block comments explain complex logic flows
- Comments in config.py explain env var mappings and boolean conversions
- Comments in transport.py explain async/await locking patterns
- Comments in vmware_manager.py explain performance counter queries and datastore selection logic
- No comment-driven code (no "IMPLEMENT THIS" comments found)

**JSDoc/TSDoc:**
- Not applicable; Python project uses docstrings instead

## Function Design

**Size:** Methods range from 2-200+ lines
- Short accessor/delegation methods: 2-5 lines (e.g., `list_vms()`)
- Standard operation methods: 10-40 lines (e.g., `power_on_vm()`, `clone_vm()`)
- Complex methods with nested loops: 50-200+ lines (e.g., `deploy_ovf()`, `deploy_ova()`, `get_vm_performance()`)
- Largest method: `deploy_ova()` at ~80 lines with async task keepalive logic

**Parameters:**
- Required parameters first (positional)
- Optional parameters with defaults: `datastore: Optional[str] = None`, `memory: bool = False`
- Type hints always present for parameters
- Examples:
  ```python
  def create_vm(self, name: str, cpu: int, memory: int,
                datastore: Optional[str] = None,
                network: Optional[str] = None) -> str

  def create_vm_custom(self, name: str, cpu: int, memory: int,
                       disk_size_gb: int = 10,
                       guest_id: str = "otherGuest",
                       datastore: Optional[str] = None,
                       network: Optional[str] = None,
                       thin_provisioned: bool = True,
                       annotation: Optional[str] = None) -> str
  ```

**Return Values:**
- Type hints always specified: `-> str`, `-> list`, `-> dict`, `-> Dict[str, Any]`
- Return strings for status messages: `return f"VM '{name}' powered on."`
- Return dicts for structured data: `return {"name": vm.name, "power_state": str(vm.runtime.powerState), ...}`
- Return lists for collections: `return vm_list`
- Return None implicitly or explicitly for void operations (rare in this codebase)

## Module Design

**Exports:**
- Classes and functions exported via `__all__` in `__init__.py`
- Lazy loading pattern in `__init__.py` using `__getattr__()` to avoid loading pyVmomi until needed:
  ```python
  def __getattr__(name):
      if name == "VMwareManager":
          from .vmware_manager import VMwareManager
          return VMwareManager
      elif name == "ToolHandlers":
          from .tools import ToolHandlers
          return ToolHandlers
      # ... etc
  ```

**Barrel Files:**
- Central exports in `__init__.py` (`Config`, `load_config`, `VMwareManager`, `ToolHandlers`, `create_mcp_server`, `register_handlers`)
- Enables clean imports: `from esxi_mcp_server import VMwareManager, Config`

**Class Structure:**
- Single class per file pattern (in most cases)
  - `VMwareManager` in `vmware_manager.py` - core VMware operations
  - `ToolHandlers` in `tools.py` - MCP tool handler wrappers with auth
  - `Config` in `config.py` - configuration dataclass
- Thin delegation pattern in `ToolHandlers`: each method calls `_check_auth()` then delegates to manager
- Service instance pattern: `VMwareManager` manages vCenter connection state throughout application lifecycle

## Configuration

**Environment Variables:**
- Mapped in `config.py` via `env_map` dict
- Naming: `VCENTER_*` for vCenter/ESXi settings, `MCP_*` for server settings
- Override file-based config (higher priority)
- Boolean conversion for `VCENTER_INSECURE`: `val.lower() in ("1", "true", "yes")`

**Data Classes:**
- Config uses `@dataclass` decorator from Python 3.7+
- Optional fields with defaults
- No validation logic in dataclass itself (validation in `load_config()` function)

---

*Convention analysis: 2026-03-02*
