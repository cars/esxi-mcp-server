# Testing Patterns

**Analysis Date:** 2026-03-02

## Test Framework

**Runner:**
- pytest >= 7.0.0 (listed in `requirements.txt`)
- Configuration: Not explicitly configured (no `pytest.ini`, `pyproject.toml`, `setup.cfg`, or `tox.ini` found)

**Assertion Library:**
- Not detected (default pytest assertions assumed)

**Run Commands:**
```bash
pytest                  # Run all tests (default pytest discovery)
pytest -v              # Verbose output
pytest --cov          # Coverage report (requires pytest-cov)
pytest -k test_name    # Run specific test by name/pattern
```

**Note:** Test execution commands inferred from pytest defaults. Actual command configuration not present in codebase.

## Test File Organization

**Location:**
- No test directory structure exists in codebase
- No test files detected at any level (`test_*.py`, `*_test.py`)
- No integration test directory
- No unit test directory
- No E2E test directory

**Naming:**
- Not established; no test files present

**Structure:**
- Not established; testing infrastructure not yet implemented

## Test Coverage Status

**Current State:**
- **No tests written** - Zero test files found in entire repository
- pytest dependency is declared but not utilized
- Testing strategy has not been established

**Why This Matters:**
- `VMwareManager` class (1372 lines) - untested
- `ToolHandlers` class (199 lines) - untested
- `mcp_server.py` registration logic (451 lines) - untested
- `transport.py` HTTP endpoint and auth logic (120 lines) - untested
- `config.py` loading and validation (83 lines) - untested

## Testing Opportunities

### Unit Tests Candidates

**`vmware_manager.py` methods to test:**
- `list_vms()` - Should return VM list
- `find_vm(name)` - Should find or return None
- `get_vm_details(vm_name)` - Should return dict with VM info
- `get_vm_performance(vm_name)` - Should handle missing performance data gracefully
- `power_on_vm(name)` - Should check power state transitions
- `power_off_vm(name)` - Should check power state transitions
- `create_vm(name, cpu, memory, ...)` - Should validate parameters
- `delete_vm(name)` - Should require existing VM
- `create_snapshot(vm_name, snapshot_name, ...)` - Should validate inputs
- `_ensure_connected()` - Should reconnect on session loss

**`config.py` functions to test:**
- `load_config(config_path)` - Should load JSON/YAML files
- `load_config(None)` - Should load from environment variables
- Environment variable override - Should override file values
- Missing required fields - Should raise Exception with message
- Boolean conversion for `VCENTER_INSECURE` - Should handle "true", "1", "yes" (case-insensitive)

**`tools.py` ToolHandlers methods to test:**
- `_check_auth()` - Should verify API key if configured
- `_check_auth()` - Should call `_ensure_connected()` on manager
- Each handler - Should delegate correctly to manager

**`transport.py` HTTP endpoint to test:**
- `streamable_http_endpoint()` - Should reject 401 on invalid API key
- `streamable_http_endpoint()` - Should accept valid API key in Authorization header (Bearer format)
- `streamable_http_endpoint()` - Should accept API key in X-API-Key header
- `streamable_http_endpoint()` - Should skip auth if no API key configured

**`mcp_server.py` registration to test:**
- `create_mcp_server()` - Should return Server instance
- `register_handlers()` - Should register all 31 tools with correct schemas
- Tool schema validation - Should have required and optional properties

### Integration Tests Candidates

- Connect to real vCenter and list VMs
- Create/delete test VM
- VM power on/off state transitions
- Snapshot create/revert/delete workflow
- File upload to VM and datastore
- OVA/OVF deployment
- Session reconnection on expiry

### Mock Strategy

**External Dependencies to Mock:**
- pyVmomi `vim.VirtualMachine` objects
- pyVmomi `vim.Task` objects for async operations
- vCenter connection via `pyVim.connect.SmartConnect()`
- File I/O for config loading
- HTTP requests (if testing transport with mock MCP server)

**Mock Implementation:**
- Use `unittest.mock` (standard library) or `pytest-mock` plugin
- Mock VMware API calls before testing business logic
- Fixture for mock Config object with test values

**What NOT to Mock:**
- Pure Python logic (string formatting, dict building, list operations)
- Type validation and error messages
- Config loading logic itself (should be tested with real files)

### Testing Constraints

**pyVmomi Complexity:**
- pyVmomi objects are complex VMware API wrappers
- Direct instantiation of vim.* objects difficult without vCenter
- Consider using `unittest.mock.MagicMock()` for object properties
- Alternatively, use `pytest` fixtures to create mock VM objects

**Async/Await in transport.py:**
- Transport layer uses asyncio heavily
- Need `pytest-asyncio` plugin for async test support
- Test pattern: `async def test_...()` with `@pytest.mark.asyncio`

**vCenter Connection State:**
- `VMwareManager` maintains persistent connection (in `self.si`)
- Session timeout tests need to verify `_ensure_connected()` reconnection
- Consider mocking `si.CurrentTime()` for session validation

## Example Test Patterns (To Be Implemented)

### Config Loading Test
```python
import pytest
from esxi_mcp_server import load_config, Config

def test_load_config_from_json(tmp_path):
    """Test loading config from JSON file."""
    config_file = tmp_path / "config.json"
    config_file.write_text('{"vcenter_host": "test-host", "vcenter_user": "admin", "vcenter_password": "pass"}')

    config = load_config(str(config_file))

    assert config.vcenter_host == "test-host"
    assert config.vcenter_user == "admin"
    assert config.vcenter_password == "pass"

def test_load_config_missing_required_field():
    """Test that missing required fields raise Exception."""
    with pytest.raises(Exception, match="Missing required configuration"):
        load_config_from_dict({})
```

### VMware Manager Mock Test
```python
from unittest.mock import MagicMock, patch
from esxi_mcp_server import VMwareManager, Config

def test_list_vms_returns_empty_list():
    """Test list_vms with mock empty container."""
    config = Config(
        vcenter_host="test",
        vcenter_user="user",
        vcenter_password="pass"
    )

    with patch('esxi_mcp_server.vmware_manager.connect.SmartConnect'):
        manager = VMwareManager(config)
        manager.content.viewManager.CreateContainerView.return_value.view = []

        result = manager.list_vms()

        assert result == []
```

### Auth Check Test
```python
import pytest
from esxi_mcp_server import ToolHandlers
from unittest.mock import MagicMock

def test_check_auth_raises_on_missing_api_key():
    """Test that _check_auth raises when API key required but not provided."""
    manager = MagicMock()
    config = MagicMock(api_key="required-key")
    config.api_key = "required-key"

    handlers = ToolHandlers(manager, config)
    manager.authenticated = False

    with pytest.raises(Exception, match="Unauthorized"):
        handlers._check_auth()
```

### Async Transport Test
```python
import pytest
from esxi_mcp_server.transport import streamable_http_endpoint

@pytest.mark.asyncio
async def test_streamable_http_endpoint_401_on_invalid_key():
    """Test that invalid API key returns 401."""
    scope = {
        "type": "http",
        "headers": [(b"x-api-key", b"wrong-key")]
    }

    config = MagicMock()
    config.api_key = "correct-key"

    send_calls = []
    async def send(msg):
        send_calls.append(msg)

    async def receive():
        pass

    # Should have sent 401 response
    assert len(send_calls) > 0
    assert send_calls[0]["status"] == 401
```

## Notes on Implementation Priority

1. **Start with `config.py`** - Easiest to test, no external dependencies
2. **Add `tools.py` unit tests** - Mock the manager, test delegation and auth
3. **Mock and test `vmware_manager.py` methods** - High impact, largest file
4. **Test `transport.py` auth logic** - Critical for security
5. **Test `mcp_server.py` registration** - Validate tool schemas
6. **Integration tests** - Require vCenter environment, run last

## Test Dependencies to Add

For comprehensive testing, add these to `requirements-dev.txt` or `requirements.txt`:

```
pytest>=7.0.0          # Already present
pytest-cov>=3.0.0      # For coverage reporting
pytest-asyncio>=0.18.0 # For async test support
pytest-mock>=3.6.0     # For better mocking utilities
responses>=0.20.0      # For mocking HTTP requests (if needed)
```

---

*Testing analysis: 2026-03-02*
