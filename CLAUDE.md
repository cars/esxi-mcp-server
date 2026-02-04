# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ESXi MCP Server is a Python MCP (Model Control Protocol) server for managing VMware ESXi/vCenter infrastructure. It exposes 31 MCP tools for VM lifecycle, snapshots, host management, guest operations, and OVA/OVF deployment. Supports both HTTP (Streamable HTTP on port 8080) and stdio transports.

## Commands

### Install dependencies
```bash
pip install -r requirements.txt
# or for development
pip install -e .
```

### Run the server
```bash
# HTTP transport (default, port 8080)
python -m esxi_mcp_server -c config.yaml --transport http

# stdio transport
python -m esxi_mcp_server -c config.yaml --transport stdio

# Alternative entry points
python server.py -c config.yaml
esxi-mcp-server -c config.yaml  # after pip install -e .
```

### Docker
```bash
make build          # Build Docker image
make run            # Run in background
make dev            # Build + run with logs
make stop           # Stop containers
make health         # Check container health
make clean          # Remove containers and volumes
```

### Tests
```bash
pytest
```

## Architecture

The server follows a layered architecture with clear separation between protocol handling and VMware operations:

```
Client Request
  -> transport.py (HTTP auth + routing, or stdio)
    -> mcp_server.py (MCP protocol, tool/resource registration)
      -> tools.py (auth check + delegation)
        -> vmware_manager.py (pyVmomi vSphere API calls)
```

### Key modules

- **`vmware_manager.py`** (~1360 lines) - Core VMware operations via pyVmomi. All vSphere API interactions go through the `VMwareManager` class. This is the largest and most important file.
- **`mcp_server.py`** - Creates the MCP `Server` instance and registers all 31 tool definitions with JSON schemas plus resource handlers. Tool definitions and their handler mappings are both defined here.
- **`tools.py`** - `ToolHandlers` class that wraps each `VMwareManager` method with API key authentication (`_check_auth()`). Each handler is a thin delegation layer.
- **`transport.py`** - HTTP transport via Streamable HTTP (`/message` endpoint) with API key validation from `Authorization` or `X-API-Key` headers. Also creates the ASGI app.
- **`config.py`** - `Config` dataclass loaded from YAML/JSON or environment variables. Environment variables override file values.
- **`__init__.py`** - Lazy imports to avoid loading pyVmomi at package import time.
- **`__main__.py`** - CLI entry point: parses args, loads config, connects to vCenter, creates MCP server, starts selected transport.

### Adding a new MCP tool

To add a new tool, you need to modify three files:
1. **`vmware_manager.py`** - Add the actual VMware operation method to `VMwareManager`
2. **`mcp_server.py`** - Add the tool definition (name, description, input schema) in `register_handlers()` and add its handler mapping in the `handlers` dict
3. **`tools.py`** - Add a handler method in `ToolHandlers` that calls `_check_auth()` then delegates to the manager

### Configuration

Config is loaded from YAML/JSON file (`-c` flag) or environment variables:
- Required: `VCENTER_HOST`, `VCENTER_USER`, `VCENTER_PASSWORD`
- Optional: `VCENTER_DATACENTER`, `VCENTER_CLUSTER`, `VCENTER_DATASTORE`, `VCENTER_NETWORK`, `VCENTER_INSECURE`
- Server: `MCP_API_KEY`, `MCP_LOG_FILE`, `MCP_LOG_LEVEL`

See `config.yaml.sample` for file-based configuration template.

### Docker

Multi-stage Dockerfile with Python 3.11-slim. Runs as non-root user `mcpuser`. The `docker-entrypoint.sh` script will generate `config.yaml` from environment variables if no config file is mounted.
