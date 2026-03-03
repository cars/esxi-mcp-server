# Codebase Structure

**Analysis Date:** 2026-03-02

## Directory Layout

```
esxi-mcp-server/
├── esxi_mcp_server/              # Main Python package
│   ├── __init__.py               # Lazy imports for public API
│   ├── __main__.py               # CLI entry point (argv parsing, init, server startup)
│   ├── mcp_server.py             # MCP tool registration and handler wiring
│   ├── tools.py                  # ToolHandlers class (auth + delegation)
│   ├── vmware_manager.py         # VMwareManager class (pyVmomi operations)
│   ├── transport.py              # HTTP transport (Streamable HTTP ASGI)
│   └── config.py                 # Config dataclass and load_config()
├── server.py                     # Simple wrapper entry point
├── setup.py                      # Package setup configuration
├── requirements.txt              # Python dependencies
├── config.yaml.sample            # Example configuration file
├── config.yaml                   # Runtime configuration (not committed)
├── Dockerfile                    # Multi-stage Docker build (Python 3.11-slim)
├── docker-compose.yml            # Docker Compose for local testing
├── docker-entrypoint.sh          # Entrypoint script for Docker
├── Makefile                      # Docker build/run targets
├── logs/                         # Log files directory (generated at runtime)
└── [docs/]                       # README.md, EXAMPLES.md, TOOLS.md, etc.
```

## Directory Purposes

**esxi_mcp_server/:**
- Purpose: Main Python package containing all server logic
- Contains: 7 Python modules totaling ~2200 lines
- Key files: `vmware_manager.py` (1372 lines, core operations), `mcp_server.py` (450 lines, protocol), others <200 lines each

## Key File Locations

**Entry Points:**
- `server.py`: Simple wrapper importing `__main__.main()`
- `esxi_mcp_server/__main__.py`: CLI parsing, config loading, server initialization (argparse, logging setup, VMwareManager creation, uvicorn/stdio startup)

**Configuration:**
- `esxi_mcp_server/config.py`: `Config` dataclass (11 fields), `load_config()` function that merges YAML/JSON with environment variable overrides
- `config.yaml.sample`: Example config with vCenter credentials
- `config.yaml`: Runtime config (git-ignored, contains real credentials)

**Core Logic:**
- `esxi_mcp_server/vmware_manager.py`: `VMwareManager` class with 40+ methods for VM/host/snapshot/guest operations via pyVmomi
- `esxi_mcp_server/tools.py`: `ToolHandlers` class with 31 handler methods (auth wrapper layer)
- `esxi_mcp_server/mcp_server.py`: `create_mcp_server()` factory, `register_handlers()` function that defines 31 tool schemas + maps to handlers

**Protocol & Transport:**
- `esxi_mcp_server/transport.py`: HTTP transport implementation (Streamable HTTP, ASGI app, request routing, API key validation)

**Testing:**
- No test files in codebase (pytest not configured)

## Naming Conventions

**Files:**
- Python modules: snake_case.py (e.g., `vmware_manager.py`, `__main__.py`)
- Config files: lowercase with extensions (e.g., `config.yaml.sample`)
- Docker files: Uppercase (Dockerfile, Makefile)

**Directories:**
- Lowercase snake_case (e.g., `esxi_mcp_server/`, `logs/`)
- Package directory matches project name without hyphens

**Python Classes:**
- PascalCase: `VMwareManager`, `ToolHandlers`, `Config`

**Python Methods/Functions:**
- snake_case: `list_vms()`, `get_vm_details()`, `_ensure_connected()` (private prefix underscore)
- Handler methods: `<action>_<resource>()` (e.g., `create_vm()`, `power_on_vm()`, `list_datastores()`)
- Internal methods: `_ensure_connected()`, `_connect_vcenter()`, `_check_auth()`, `_find_snapshot_by_name()`

**Python Variables:**
- snake_case: `vm_name`, `datastore_name`, `config_path`

**Configuration Keys:**
- Environment variables: UPPER_SNAKE_CASE (e.g., `VCENTER_HOST`, `MCP_API_KEY`)
- Config dataclass fields: snake_case (e.g., `vcenter_host`, `api_key`)

## Where to Add New Code

**New VMware Operation:**
1. Add method to `VMwareManager` class in `esxi_mcp_server/vmware_manager.py`
   - Use existing helper methods like `find_vm()`, `find_host()`, `wait_for_task()`
   - Return dict or string (will be JSON-serialized by MCP layer)

2. Add handler to `ToolHandlers` class in `esxi_mcp_server/tools.py`
   - Call `_check_auth()` at start
   - Delegate to `VMwareManager` method
   - Keep it as a thin wrapper

3. Register tool in `esxi_mcp_server/mcp_server.py`
   - Add `types.Tool` object to `tools` dict (name, description, inputSchema with properties/required)
   - Add entry to `tool_handler_map` dict mapping tool name to lambda calling `ToolHandlers` method

**New Transport/Protocol Feature:**
- Primary: `esxi_mcp_server/transport.py` for HTTP changes
- Reference: `__main__.py` for adding new startup flags or configuration

**New Configuration Option:**
1. Add field to `Config` dataclass in `esxi_mcp_server/config.py`
2. Add env var mapping to `env_map` dict in `load_config()`
3. Add to config.yaml.sample
4. Update CLAUDE.md documentation

**New Dependencies:**
- Add to `requirements.txt` (pinned version recommended)
- Update `setup.py` if adding new entry points
- Update Dockerfile if requiring system packages

## Special Directories

**logs/:**
- Purpose: Runtime log files (created if `MCP_LOG_FILE` configured)
- Generated: Yes
- Committed: No (in .gitignore)

**esxi_mcp_server/__pycache__/:**
- Purpose: Python bytecode cache (auto-generated)
- Generated: Yes
- Committed: No (in .gitignore)

## Module Import Graph

```
__main__.py
  ├── imports: config.load_config, VMwareManager, ToolHandlers, create_mcp_server, register_handlers
  ├── imports: transport.create_asgi_app
  └── creates: VMwareManager → Config
               ToolHandlers → VMwareManager, Config
               MCP Server instance
               ASGI app

mcp_server.py
  └── imports: tools.ToolHandlers
               mcp.server.lowlevel.Server
               mcp.types

tools.py
  ├── imports: vmware_manager.VMwareManager
  │            config.Config
  └── composition: holds instances of both

vmware_manager.py
  ├── imports: config.Config
  └── uses: pyVim.connect.SmartConnect
            pyVmomi.vim/vmodl (vSphere API)

transport.py
  ├── imports: config.Config
  └── uses: mcp.server.streamable_http.StreamableHTTPServerTransport
            uvicorn (indirect via __main__.py)

config.py
  └── uses: yaml, json, os (standard library)

__init__.py
  └── lazy imports: All public API (defers loading pyVmomi until needed)
```

## Configuration Load Order

1. Parse command-line args in `__main__.py` (get `-c config_path` and `-t transport`)
2. Call `load_config(config_path)` which:
   - Loads YAML/JSON file if path provided
   - Overlays environment variables (higher priority)
   - Validates required fields present
   - Returns `Config` instance
3. Pass `Config` to `VMwareManager`, `ToolHandlers`, `transport.create_asgi_app()`

## How Requests Flow Through the System

**HTTP Request:**
```
Client → HTTP POST /message
         ↓
transport.py: streamable_http_endpoint()
  ├─ Extract API key from header
  ├─ Validate against config.api_key
  └─ → StreamableHTTPServerTransport.handle_request()
        ↓
        mcp_server.py: call_tool_handler()
          ├─ Look up handler in tool_handler_map
          └─ → tools.py: ToolHandlers.<handler>()
                ├─ Call _check_auth()
                └─ → vmware_manager.py: VMwareManager.<operation>()
                      ├─ Call _ensure_connected() (check session)
                      ├─ Call pyVmomi APIs
                      └─ Return result dict/string
                ↓
                Serialize result to JSON
                ↓
                Return TextContent to transport
                ↓
Client ← Response
```

**Stdio Request (alternative transport):**
```
Same, except:
  - No HTTP header parsing
  - stdio.stdio_server() manages read/write streams
  - No API key validation (stdio is localhost-only in typical usage)
```

---

*Structure analysis: 2026-03-02*
