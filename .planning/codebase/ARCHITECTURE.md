# Architecture

**Analysis Date:** 2026-03-02

## Pattern Overview

**Overall:** Layered MCP (Model Control Protocol) server with protocol abstraction from VMware operations.

**Key Characteristics:**
- Clean separation between transport/MCP protocol handling and VMware vSphere API calls
- Tool-based handler pattern with authentication middleware
- Automatic session reconnection on vCenter/ESXi connection expiry
- Support for multiple transport modes (HTTP via Streamable HTTP and stdio)

## Layers

**Transport Layer:**
- Purpose: Handle HTTP/stdio communication, API key validation, ASGI/MCP protocol translation
- Location: `esxi_mcp_server/transport.py`
- Contains: Streamable HTTP endpoint handler, ASGI app factory, request routing
- Depends on: `config.Config`, MCP `StreamableHTTPServerTransport`
- Used by: `__main__.py` entry point

**MCP Protocol Layer:**
- Purpose: Register all 31 MCP tools and resources, manage tool definitions with JSON schemas, map tool calls to handlers
- Location: `esxi_mcp_server/mcp_server.py`
- Contains: Tool definitions (31 tools), resource definitions (vmStats), tool handler decorators
- Depends on: `tools.ToolHandlers`, MCP `Server` and `types`
- Used by: `__main__.py` (registers tools/resources), `transport.py` (serves tool calls)

**Tool Handler Layer:**
- Purpose: Authentication checkpoint and thin delegation to VMware manager
- Location: `esxi_mcp_server/tools.py`
- Contains: `ToolHandlers` class with 31 handler methods, `_check_auth()` method
- Depends on: `vmware_manager.VMwareManager`, `config.Config`
- Used by: `mcp_server.py` (tool handler mappings call these methods)
- Pattern: Each handler calls `_check_auth()` then delegates to corresponding `VMwareManager` method

**VMware Operations Layer:**
- Purpose: Core VMware vSphere API operations via pyVmomi
- Location: `esxi_mcp_server/vmware_manager.py` (~1372 lines)
- Contains: `VMwareManager` class with 40+ methods for VM, host, snapshot, guest operations
- Depends on: `pyVim.connect`, `pyVmomi.vim/vmodl`, `config.Config`
- Used by: `tools.ToolHandlers` (all handler methods delegate here)

**Configuration Layer:**
- Purpose: Load and validate server configuration from YAML/JSON files or environment variables
- Location: `esxi_mcp_server/config.py`
- Contains: `Config` dataclass, `load_config()` function
- Depends on: `yaml`, `json`, `os`
- Used by: All layers (passed to `VMwareManager`, `ToolHandlers`, `transport`)

## Data Flow

**Tool Invocation:**

1. Client sends HTTP POST to `/message` endpoint with tool call (e.g., `list_vms`)
2. `transport.py:streamable_http_endpoint()` validates API key from `Authorization`/`X-API-Key` header
3. `StreamableHTTPServerTransport` routes request to `mcp_server.py:call_tool_handler()`
4. `mcp_server.py` looks up tool name in `tool_handler_map` and calls handler
5. `tools.py:ToolHandlers.<handler>()` calls `_check_auth()` then delegates to `VMwareManager`
6. `vmware_manager.py:VMwareManager.<operation>()` calls pyVmomi API
7. Result serialized to JSON and returned as `TextContent` to client

**State Management:**
- vCenter session (`si`) maintained in `VMwareManager` singleton instance
- Session stored in `self.si` (ServiceInstance), `self.content` (root content object)
- Resource pool, datacenter, datastore, network cached at initialization
- Session expiry detected via `_ensure_connected()` → `si.CurrentTime()` check
- On expiry, automatic reconnection triggered via `_connect_vcenter()`
- Authentication flag (`self.authenticated`) set by client via separate auth mechanism

## Key Abstractions

**VMwareManager:**
- Purpose: Encapsulates all pyVmomi operations and vCenter session lifecycle
- Examples: `vmware_manager.py` lines 13-1372
- Pattern: Instance methods map 1:1 to MCP tools; internal helpers (`_connect_vcenter`, `_ensure_connected`, `find_vm`, `find_host`, `wait_for_task`) support the main operations

**ToolHandlers:**
- Purpose: Stateless wrapper that adds authentication check before delegating to VMwareManager
- Examples: `tools.py` lines 10-200
- Pattern: Each public method calls `self._check_auth()` then `self.manager.<method>()`; single point of API key validation

**MCP Server Registration:**
- Purpose: Define all 31 tools with schemas and wire them to handlers
- Examples: `mcp_server.py` lines 24-426
- Pattern: Tools dict maps tool names to `types.Tool` objects; `tool_handler_map` dict maps names to lambda closures that call `ToolHandlers` methods

**Config Resolution:**
- Purpose: Merge file-based and environment variable configuration with validation
- Examples: `config.py` lines 25-83
- Pattern: File-based config loaded first, environment variables override (higher priority), required fields validated

## Entry Points

**HTTP Server Entry:**
- Location: `esxi_mcp_server/__main__.py:main()` with `--transport http` flag
- Triggers: `python -m esxi_mcp_server -c config.yaml --transport http` or `esxi-mcp-server -c config.yaml`
- Responsibilities: Parse args, load config, create `VMwareManager`, create `ToolHandlers`, create MCP server, start uvicorn with ASGI app on port 8080

**Stdio Server Entry:**
- Location: `esxi_mcp_server/__main__.py:main()` with `--transport stdio` flag
- Triggers: `python -m esxi_mcp_server -c config.yaml --transport stdio`
- Responsibilities: Same setup as HTTP, but run MCP server via `stdio.stdio_server()` for stdin/stdout communication

**Direct Script Entry:**
- Location: `server.py` (root level)
- Triggers: `python server.py -c config.yaml`
- Responsibilities: Simple wrapper that imports and calls `__main__.main()`

**Package Entry:**
- Location: `setup.py` entry_points console script
- Triggers: `esxi-mcp-server -c config.yaml` after `pip install -e .`
- Responsibilities: Points to `esxi_mcp_server.__main__:main`

## Error Handling

**Strategy:** Exception propagation with logging; handlers convert exceptions to MCP TextContent errors

**Patterns:**
- `_ensure_connected()` catches connection errors, logs warning, triggers automatic reconnection
- `find_vm()` / `find_host()` return `None` if not found; callers raise `Exception(f"VM/Host {name} not found")`
- `_check_auth()` raises `Exception("Unauthorized: API key required.")` if auth fails
- Transport layer catches exceptions and returns 401/500 HTTP responses
- All exceptions logged via Python logging before propagation

## Cross-Cutting Concerns

**Logging:** Python standard `logging` module configured in `__main__.py:setup_logging()` with level from config (default INFO); optionally writes to file via `config.log_file`

**Validation:**
- Config validation in `config.py:load_config()` - checks required fields (vcenter_host, vcenter_user, vcenter_password)
- Tool input schemas defined in `mcp_server.py` - MCP framework validates against inputSchema before invoking handler
- VMwareManager methods validate object existence (find_vm, find_host return None if not found)

**Authentication:**
- HTTP: API key extracted from `Authorization: Bearer <key>` or `X-API-Key: <key>` header in `transport.py`
- Auth check: `ToolHandlers._check_auth()` verifies `config.api_key` matches `manager.authenticated` flag
- vCenter credentials: From config (VCENTER_USER, VCENTER_PASSWORD), used in `_connect_vcenter()` SmartConnect call

**Session Management:**
- vCenter session via `pyVim.connect.SmartConnect()` in `__main__.py`
- Session reconnection via `_ensure_connected()` check called on every tool invocation
- SSL verification controlled by `config.insecure` flag

---

*Architecture analysis: 2026-03-02*
