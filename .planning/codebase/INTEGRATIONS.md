# External Integrations

**Analysis Date:** 2026-03-02

## APIs & External Services

**VMware vSphere/ESXi:**
- VMware vCenter Server or ESXi - Virtual infrastructure management platform
  - SDK/Client: pyVmomi 7.0+
  - Connection: Via `pyVim.connect.SmartConnect()` in `esxi_mcp_server/vmware_manager.py`
  - Auth: Username/password credentials (Kerberos not supported, basic auth only)
  - Endpoint: Configured via `VCENTER_HOST` env var or config file
  - Features accessed:
    - VM lifecycle (create, delete, clone, power on/off)
    - VM details and performance metrics (CPU, memory, disk, network)
    - Snapshots (create, delete, restore, list)
    - Host management (list ESXi hosts, maintenance mode, reboot)
    - Guest operations (file operations, command execution)
    - OVA/OVF deployment and export
    - Template management
    - Datastore/network listing and management

## Data Storage

**Databases:**
- None - Application is stateless. All state resides in VMware vCenter/ESXi

**File Storage:**
- VMware Datastore (vSphere virtual storage) - Used for VM disk files and OVA/OVF deployment
  - Connection: Via pyVmomi `vim.Datastore` objects
  - Operations: Listed, selected for VM creation, used as deployment target for OVA/OVF files
  - Configured via `VCENTER_DATASTORE` env var or defaults to datastore with maximum free space

**Caching:**
- None detected - No caching layer implemented

## Authentication & Identity

**Auth Provider:**
- Custom token-based authentication - MCP API key validation
  - Implementation: `esxi_mcp_server/tools.py` via `_check_auth()` method
  - Flow:
    1. Client calls authenticate tool or provides API key in request header
    2. Transport layer validates key in `Authorization: Bearer <token>` or `X-API-Key` headers
    3. `ToolHandlers` sets `manager.authenticated = True` after successful authentication
    4. Subsequent tool calls check `manager.authenticated` before executing
  - Environment variable: `MCP_API_KEY`
  - Optional - If not configured, authentication is disabled
  - Location: `esxi_mcp_server/transport.py` lines 22-42 (HTTP header validation)

**vCenter/ESXi Authentication:**
- Direct credentials to vSphere API
  - Username: `VCENTER_USER` env var or config file
  - Password: `VCENTER_PASSWORD` env var or config file
  - No OAuth or SAML support - Basic authentication only
  - SSL handling: Optional certificate verification via `VCENTER_INSECURE` flag

## Monitoring & Observability

**Error Tracking:**
- None detected - No integration with external error tracking services (Sentry, DataDog, etc.)

**Logs:**
- File-based logging or console output
  - Location: Configurable via `MCP_LOG_FILE` env var or `log_file` config option
  - Default: Console output if no file specified
  - Level: Configurable via `MCP_LOG_LEVEL` env var (DEBUG/INFO/WARNING/ERROR)
  - Implementation: Python `logging` module in `esxi_mcp_server/__main__.py` lines 15-25

## CI/CD & Deployment

**Hosting:**
- Docker containerization (Docker Compose or Kubernetes)
  - Image: Python 3.11-slim base
  - Registry: Not specified (build from source in Dockerfile)
  - Port: 8080 (HTTP endpoint)
  - Health check: HTTP GET to `http://localhost:8080` every 30 seconds

**CI Pipeline:**
- Not detected - No GitHub Actions, GitLab CI, or other CI service integration found

## Environment Configuration

**Required env vars:**
- `VCENTER_HOST` - vCenter/ESXi host address (required)
- `VCENTER_USER` - vCenter user credentials (required)
- `VCENTER_PASSWORD` - vCenter password (required)

**Optional env vars:**
- `VCENTER_DATACENTER` - Specific datacenter to use
- `VCENTER_CLUSTER` - Specific cluster to use
- `VCENTER_DATASTORE` - Specific datastore to use
- `VCENTER_NETWORK` - Virtual network name
- `VCENTER_INSECURE` - Skip SSL verification (true/false)
- `MCP_API_KEY` - Enable API key authentication
- `MCP_LOG_FILE` - Log file path
- `MCP_LOG_LEVEL` - Logging level
- `MCP_CONFIG_FILE` - Config file path (YAML or JSON)

**Secrets location:**
- Environment variables (no .env file)
- Configuration YAML/JSON file (mounted in Docker)
- Docker Compose: `.env` file or `docker-compose.yml` environment section
- Never committed to git (see `.gitignore`)

## Webhooks & Callbacks

**Incoming:**
- MCP `/message` endpoint - Streamable HTTP endpoint for MCP client requests at `/message` (GET/POST/OPTIONS)
  - Location: `esxi_mcp_server/transport.py` lines 18-120
  - Authentication: API key validation via `Authorization` or `X-API-Key` headers
  - Format: JSON-based MCP protocol messages
  - CORS: Enabled for all origins (headers: Content-Type, Authorization, X-API-Key, MCP-Session-Id)

**Outgoing:**
- None - Application does not call webhooks or external APIs. Only calls VMware vSphere API.

## Integration Points Summary

**Inbound:**
1. HTTP clients connect to `/message` endpoint
2. API key header validation (optional)
3. MCP protocol message routing to tool handlers

**Processing:**
1. Tool handler calls appropriate `ToolHandlers` method
2. `ToolHandlers` validates authentication via `_check_auth()`
3. Delegates to `VMwareManager` for actual vSphere API calls
4. vSphere API calls via pyVmomi (SmartConnect, vim objects)

**Outbound:**
1. All outbound traffic is to vCenter/ESXi host on port 443 (HTTPS)
2. No external API calls to third-party services
3. Optional log file writes to local filesystem

---

*Integration audit: 2026-03-02*
