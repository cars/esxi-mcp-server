# Technology Stack

**Analysis Date:** 2026-03-02

## Languages

**Primary:**
- Python 3.7+ - Core application language. Specified as `python_requires=">=3.7"` in `setup.py` but Docker runs Python 3.11-slim.

## Runtime

**Environment:**
- Python 3.11-slim (Docker production image from `Dockerfile`)
- Python 3.12.3 (development environment)

**Package Manager:**
- pip - Dependency installation
- Lockfile: Not detected (requirements.txt used instead)

## Frameworks

**Core:**
- MCP (Model Control Protocol) - Protocol framework for tool/resource registration via `mcp` package
- uvicorn 0.15.0+ - ASGI HTTP server for running the application on port 8080
- PyYAML 6.0+ - Configuration file parsing (JSON/YAML support)

**Testing:**
- pytest 7.0.0+ - Test framework (detected in `requirements.txt`)

**Build/Dev:**
- setuptools - Package building and distribution
- six 1.15.0+ - Python 2/3 compatibility library

## Key Dependencies

**Critical:**
- pyVmomi 7.0+ - VMware vSphere API client library. Core to all VMware operations via `pyVim.connect` and `pyVmomi.vim` modules. Manages VM lifecycle, snapshots, datastore operations.
- mcp - Model Control Protocol server implementation for tool registration and handling
- uvicorn 0.15.0+ - ASGI application server supporting HTTP transport with Streamable HTTP for MCP protocol streaming responses
- PyYAML 6.0+ - Configuration parsing from YAML and JSON files

**Infrastructure:**
- anyio 3.0.0+ - Async I/O abstraction for async operations across the server
- requests 2.25.0+ - HTTP requests library (for potential external API calls)

## Configuration

**Environment:**
- Configuration loaded from YAML or JSON file via `-c` flag or `MCP_CONFIG_FILE` env var
- Environment variables override file-based configuration with higher priority
- No `.env` file used; configuration purely from YAML/JSON and environment variables

**Required Configuration:**
- `VCENTER_HOST` - vCenter/ESXi host IP or hostname
- `VCENTER_USER` - vCenter user credentials
- `VCENTER_PASSWORD` - vCenter password credentials
- `MCP_API_KEY` - API key for client authentication (optional, enables authentication flow)

**Optional Configuration:**
- `VCENTER_DATACENTER` - Specific datacenter name (defaults to first available)
- `VCENTER_CLUSTER` - Specific cluster name (defaults to first ComputeResource)
- `VCENTER_DATASTORE` - Specific datastore name (defaults to datastore with most free space)
- `VCENTER_NETWORK` - Virtual network name (optional, VMs can be created without network)
- `VCENTER_INSECURE` - Boolean to skip SSL certificate verification (default: false)
- `MCP_LOG_FILE` - Log file path (if not specified, logs output to console)
- `MCP_LOG_LEVEL` - Log level: DEBUG/INFO/WARNING/ERROR (default: INFO)

**Build:**
- `setup.py` - Package metadata and entry point configuration
- `requirements.txt` - Direct pip-installable dependencies
- `Dockerfile` - Multi-stage Docker build (builder + production stages)
- `docker-compose.yml` - Container orchestration configuration

## Platform Requirements

**Development:**
- Python 3.7 or higher (3.11+ recommended)
- pip package manager
- SSL/TLS support for vCenter/ESXi connections
- Network access to vCenter/ESXi host (default port 443)

**Production:**
- Docker 19.0+ (for containerized deployment)
- Kubernetes or Docker Compose (optional orchestration)
- 256MB-512MB RAM per container (from docker-compose resource limits)
- Network connectivity to VMware vCenter/ESXi infrastructure
- API clients must support HTTP/1.1 with optional API key authentication via `Authorization: Bearer <token>` or `X-API-Key` headers

**Deployment Target:**
- HTTP server on port 8080 (configurable in uvicorn)
- Supports two transport modes:
  - HTTP (default) - Streamable HTTP transport via `/message` endpoint
  - stdio - stdin/stdout communication (for embedded deployments)

---

*Stack analysis: 2026-03-02*
