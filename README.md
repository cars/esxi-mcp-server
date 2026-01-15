# ESXi MCP Server

A VMware ESXi/vCenter management server based on MCP (Model Control Protocol), providing simple REST API interfaces for virtual machine management.

## Features

- Support for ESXi and vCenter Server connections
- Multiple MCP transport protocols:
  - **Streamable HTTP** - HTTP-based transport at `/message` endpoint (default)
  - **stdio** - Standard input/output transport for subprocess communication
- RESTful API interface with JSON-RPC support
- API key authentication
- Complete virtual machine lifecycle management
- Real-time performance monitoring
- SSL/TLS secure connection support
- Flexible configuration options (YAML/JSON/Environment Variables)

## Core Functions

- Virtual Machine Management
  - Create VM
  - Clone VM
  - Delete VM
  - Power On/Off operations
  - List all VMs
- Performance Monitoring
  - CPU usage
  - Memory usage
  - Storage usage
  - Network traffic statistics

## Requirements

- Python 3.7+
- pyVmomi
- PyYAML
- uvicorn
- mcp-core (Machine Control Protocol core library)

## Quick Start

### Installation

You can install the package in one of two ways:

**Option 1: Install from source (recommended for development)**:
```bash
git clone https://github.com/dylanturn/esxi-mcp-server.git
cd esxi-mcp-server
pip install -e .
```

**Option 2: Install dependencies only**:
```bash
pip install pyvmomi pyyaml uvicorn mcp-core
```

### Configuration

1. Create configuration file `config.yaml`:

```yaml
vcenter_host: "your-vcenter-ip"
vcenter_user: "administrator@vsphere.local"
vcenter_password: "your-password"
datacenter: "your-datacenter"        # Optional
cluster: "your-cluster"              # Optional
datastore: "your-datastore"          # Optional
network: "VM Network"                # Optional
insecure: true                       # Skip SSL certificate verification
api_key: "your-api-key"             # API access key
log_file: "./logs/vmware_mcp.log"   # Log file path
log_level: "INFO"                    # Log level
```

### Running the Server

**HTTP Transport (default)**:
```bash
# If installed with pip:
esxi-mcp-server -c config.yaml --transport http

# Or using Python module:
python -m esxi_mcp_server -c config.yaml --transport http

# Or using the entry point script:
python server.py -c config.yaml --transport http
```

**stdio Transport** (for subprocess/pipe communication):
```bash
# If installed with pip:
esxi-mcp-server -c config.yaml --transport stdio

# Or using Python module:
python -m esxi_mcp_server -c config.yaml --transport stdio

# Or using the entry point script:
python server.py -c config.yaml --transport stdio
```

### MCP Client Configuration

When configuring this server in an MCP client (like Claude Desktop), use the following configuration format in your MCP settings file:

**For stdio transport** (recommended):
```json
{
  "mcpServers": {
    "esxi": {
      "command": "python",
      "args": [
        "-m",
        "esxi_mcp_server",
        "-c",
        "/path/to/config.yaml",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

**Alternatively, using the entry point script**:
```json
{
  "mcpServers": {
    "esxi": {
      "command": "python",
      "args": [
        "/path/to/esxi-mcp-server/server.py",
        "-c",
        "/path/to/config.yaml",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

**Important**: Each command-line argument must be a separate string in the `args` array. Do not combine arguments like `"-c config.yaml"` or `"--transport stdio"` as single strings.

**Using uv**:
```json
{
  "mcpServers": {
    "esxi": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/esxi-mcp-server",
        "server.py",
        "-c",
        "config.yaml",
        "--transport",
        "stdio"
      ]
    }
  }
}
```

## API Interface

### Transport Protocols

The server supports two MCP transport protocols:

1. **Streamable HTTP** (default) - HTTP-based transport
   - Endpoint: `/message`
   - Methods: `GET` (streaming responses), `POST` (requests)
   - Requires API key authentication
   - Accessible over network at `http://host:8080/message`

2. **stdio** - Standard input/output transport
   - Communicates via stdin/stdout
   - Used when running as a subprocess
   - No network required
   - Authentication handled by parent process

### Streamable HTTP Transport

When using HTTP transport, the server listens on port 8080:

- **Endpoint**: `/message`
- **Methods**: `GET` (for streaming responses), `POST` (for requests)
- Modern HTTP-based transport protocol with full MCP specification compliance

### Authentication

All privileged operations require authentication. Include your API key in request headers:

```http
Authorization: Bearer your-api-key
```

Or:

```http
X-API-Key: your-api-key
```

### Main Tool Interfaces

1. Create VM
```json
{
    "name": "vm-name",
    "cpu": 2,
    "memory": 4096,
    "datastore": "datastore-name",
    "network": "network-name"
}
```

2. Clone VM
```json
{
    "template_name": "source-vm",
    "new_name": "new-vm-name"
}
```

3. Delete VM
```json
{
    "name": "vm-name"
}
```

4. Power Operations
```json
{
    "name": "vm-name"
}
```

### Resource Monitoring Interface

Get VM performance data:
```http
GET vmstats://{vm_name}
```

## Configuration

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| vcenter_host | vCenter/ESXi server address | Yes | - |
| vcenter_user | Login username | Yes | - |
| vcenter_password | Login password | Yes | - |
| datacenter | Datacenter name | No | Auto-select first |
| cluster | Cluster name | No | Auto-select first |
| datastore | Storage name | No | Auto-select largest available |
| network | Network name | No | VM Network |
| insecure | Skip SSL verification | No | false |
| api_key | API access key | No | - |
| log_file | Log file path | No | Console output |
| log_level | Log level | No | INFO |

## Project Structure

The project follows the recommended Python package structure:

```
esxi-mcp-server/
├── esxi_mcp_server/          # Main package directory
│   ├── __init__.py           # Package initialization
│   ├── __main__.py           # Entry point for python -m esxi_mcp_server
│   ├── config.py             # Configuration management
│   ├── vmware_manager.py     # VMware vSphere operations
│   ├── tools.py              # MCP tool handlers
│   ├── mcp_server.py         # MCP server setup and registration
│   └── transport.py          # Transport layer (HTTP/stdio)
├── server.py                 # Simple entry point script
├── setup.py                  # Package installation configuration
├── requirements.txt          # Python dependencies
├── config.yaml.sample        # Sample configuration file
├── README.md                 # Documentation
├── Dockerfile                # Docker container configuration
└── docker-compose.yml        # Docker Compose configuration
```

### Module Descriptions

- **config.py**: Handles configuration loading from files (YAML/JSON) and environment variables
- **vmware_manager.py**: Contains the `VMwareManager` class that interfaces with VMware vSphere using pyVmomi
- **tools.py**: Implements the `ToolHandlers` class with all MCP tool handler methods
- **mcp_server.py**: Sets up the MCP server and registers all tools and resources
- **transport.py**: Manages transport layer including HTTP and stdio transports
- **__main__.py**: Main entry point that ties everything together

## Environment Variables

All configuration items support environment variable settings, following these naming rules:
- VCENTER_HOST
- VCENTER_USER
- VCENTER_PASSWORD
- VCENTER_DATACENTER
- VCENTER_CLUSTER
- VCENTER_DATASTORE
- VCENTER_NETWORK
- VCENTER_INSECURE
- MCP_API_KEY
- MCP_LOG_FILE
- MCP_LOG_LEVEL

## Security Recommendations

1. Production Environment:
   - Use valid SSL certificates
   - Enable API key authentication
   - Set appropriate log levels
   - Restrict API access scope

2. Testing Environment:
   - Set insecure: true to skip SSL verification
   - Use more detailed log level (DEBUG)

## License

MIT License

## Contributing

Issues and Pull Requests are welcome!

## Changelog

### v0.0.4
- **BREAKING CHANGE**: Refactored project structure to follow Python best practices
- Split monolithic `server.py` into modular package structure (`esxi_mcp_server/`)
- Added proper package installation support with `setup.py`
- Improved code organization and maintainability
- Added lazy imports to reduce startup time
- New ways to run the server:
  - `esxi-mcp-server` (when installed with pip)
  - `python -m esxi_mcp_server`
  - `python server.py` (backward compatible)

### v0.0.3
- Added stdio transport support for subprocess communication
- Added `--transport` CLI flag to choose between HTTP and stdio modes
- Enhanced flexibility for different deployment scenarios

### v0.0.2
- **BREAKING CHANGE**: Replaced deprecated SSE transport with modern Streamable HTTP transport
- MCP endpoint now at `/message` instead of `/sse` and `/sse/messages`
- Enhanced MCP protocol compliance with HTTP-based transport
- Improved concurrency handling and error management

### v0.0.1
- Initial release
- Basic VM management functionality
- SSE communication support
- API key authentication
- Performance monitoring

## Author

Bright8192

## Acknowledgments

- VMware pyvmomi team
- MCP Protocol development team
