"""MCP server initialization and handler registration."""

import json
from mcp.server.lowlevel import Server
from mcp import types

from .tools import ToolHandlers


def create_mcp_server() -> Server:
    """Create and initialize the MCP server."""
    return Server(name="VMware-MCP-Server", version="0.0.1")


def register_handlers(mcp_server: Server, tool_handlers: ToolHandlers):
    """
    Register all MCP tool and resource handlers.
    
    Args:
        mcp_server: The MCP Server instance
        tool_handlers: The ToolHandlers instance containing handler methods
    """
    # Define tools with proper MCP Tool schema (name, description, inputSchema only)
    tools = {
        "ping": types.Tool(
            name="ping",
            description="A simple test tool that echoes back a message. Use this to verify MCP connectivity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message to echo back", "default": "pong"}
                }
            }
        ),
        "authenticate": types.Tool(
            name="authenticate",
            description="Authenticate using API key to enable privileged operations",
            inputSchema={"type": "object", "properties": {"key": {"type": "string"}}, "required": ["key"]}
        ),
        "createVM": types.Tool(
            name="createVM",
            description="Create a new virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "cpu": {"type": "integer"},
                    "memory": {"type": "integer"},
                    "datastore": {"type": "string"},
                    "network": {"type": "string"}
                },
                "required": ["name", "cpu", "memory"]
            }
        ),
        "cloneVM": types.Tool(
            name="cloneVM",
            description="Clone a virtual machine from a template or existing VM",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_name": {"type": "string"},
                    "new_name": {"type": "string"}
                },
                "required": ["template_name", "new_name"]
            }
        ),
        "deleteVM": types.Tool(
            name="deleteVM",
            description="Delete a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"]
            }
        ),
        "powerOn": types.Tool(
            name="powerOn",
            description="Power on a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"]
            }
        ),
        "powerOff": types.Tool(
            name="powerOff",
            description="Power off a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"]
            }
        ),
        "listVMs": types.Tool(
            name="listVMs",
            description="List all virtual machines",
            inputSchema={"type": "object", "properties": {}}
        ),
        "list_vms": types.Tool(
            name="list_vms",
            description="List all virtual machines",
            inputSchema={"type": "object", "properties": {}}
        ),
        "get_vm_details": types.Tool(
            name="get_vm_details",
            description="Get detailed information about a specific virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the virtual machine"}
                },
                "required": ["vm_name"]
            }
        ),
        "list_templates": types.Tool(
            name="list_templates",
            description="List all virtual machine templates",
            inputSchema={"type": "object", "properties": {}}
        ),
        "list_datastores": types.Tool(
            name="list_datastores",
            description="List all datastores with their details",
            inputSchema={"type": "object", "properties": {}}
        ),
        "list_networks": types.Tool(
            name="list_networks",
            description="List all networks",
            inputSchema={"type": "object", "properties": {}}
        ),
        "list_hosts": types.Tool(
            name="list_hosts",
            description="List all ESXi hosts",
            inputSchema={"type": "object", "properties": {}}
        ),
        "get_host_details": types.Tool(
            name="get_host_details",
            description="Get detailed information about a specific host",
            inputSchema={
                "type": "object",
                "properties": {
                    "host_name": {"type": "string", "description": "Name of the host"}
                },
                "required": ["host_name"]
            }
        ),
        "get_host_performance_metrics": types.Tool(
            name="get_host_performance_metrics",
            description="Get performance metrics for a specific host",
            inputSchema={
                "type": "object",
                "properties": {
                    "host_name": {"type": "string", "description": "Name of the host"}
                },
                "required": ["host_name"]
            }
        ),
        "get_host_hardware_health": types.Tool(
            name="get_host_hardware_health",
            description="Get hardware health information for a specific host",
            inputSchema={
                "type": "object",
                "properties": {
                    "host_name": {"type": "string", "description": "Name of the host"}
                },
                "required": ["host_name"]
            }
        ),
        "get_host_performance": types.Tool(
            name="get_host_performance",
            description="Get detailed performance data for a specific host",
            inputSchema={
                "type": "object",
                "properties": {
                    "host_name": {"type": "string", "description": "Name of the host"}
                },
                "required": ["host_name"]
            }
        ),
        "list_performance_counters": types.Tool(
            name="list_performance_counters",
            description="List all available performance counters",
            inputSchema={"type": "object", "properties": {}}
        ),
        "get_vm_summary_stats": types.Tool(
            name="get_vm_summary_stats",
            description="Get summary statistics for a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the virtual machine"}
                },
                "required": ["vm_name"]
            }
        ),
        "get_vm_performance": types.Tool(
            name="get_vm_performance",
            description="Get performance data for a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "vm_name": {"type": "string", "description": "Name of the virtual machine"}
                },
                "required": ["vm_name"]
            }
        ),
        "create_vm_custom": types.Tool(
            name="create_vm_custom",
            description="Create a custom virtual machine with advanced configuration options",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "VM name"},
                    "cpu": {"type": "integer", "description": "Number of CPUs"},
                    "memory": {"type": "integer", "description": "Memory in MB"},
                    "disk_size_gb": {"type": "integer", "description": "Disk size in GB", "default": 10},
                    "guest_id": {"type": "string", "description": "Guest OS identifier", "default": "otherGuest"},
                    "datastore": {"type": "string", "description": "Datastore name (optional)"},
                    "network": {"type": "string", "description": "Network name (optional)"},
                    "thin_provisioned": {"type": "boolean", "description": "Use thin provisioning", "default": True},
                    "annotation": {"type": "string", "description": "VM annotation/description"}
                },
                "required": ["name", "cpu", "memory"]
            }
        ),
        "power_on_vm": types.Tool(
            name="power_on_vm",
            description="Power on a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the virtual machine"}
                },
                "required": ["name"]
            }
        ),
        "power_off_vm": types.Tool(
            name="power_off_vm",
            description="Power off a virtual machine",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the virtual machine"}
                },
                "required": ["name"]
            }
        )
    }
    
    # Map tool names to their handler functions
    tool_handler_map = {
        "ping": lambda args: tool_handlers.ping(**args),
        "authenticate": lambda args: tool_handlers.authenticate(**args),
        "createVM": lambda args: tool_handlers.create_vm(**args),
        "cloneVM": lambda args: tool_handlers.clone_vm(**args),
        "deleteVM": lambda args: tool_handlers.delete_vm(**args),
        "powerOn": lambda args: tool_handlers.power_on(**args),
        "powerOff": lambda args: tool_handlers.power_off(**args),
        "listVMs": lambda args: tool_handlers.list_vms(),
        "list_vms": lambda args: tool_handlers.list_vms(),
        "get_vm_details": lambda args: tool_handlers.get_vm_details(**args),
        "list_templates": lambda args: tool_handlers.list_templates(),
        "list_datastores": lambda args: tool_handlers.list_datastores(),
        "list_networks": lambda args: tool_handlers.list_networks(),
        "list_hosts": lambda args: tool_handlers.list_hosts(),
        "get_host_details": lambda args: tool_handlers.get_host_details(**args),
        "get_host_performance_metrics": lambda args: tool_handlers.get_host_performance_metrics(**args),
        "get_host_hardware_health": lambda args: tool_handlers.get_host_hardware_health(**args),
        "get_host_performance": lambda args: tool_handlers.get_host_performance(**args),
        "list_performance_counters": lambda args: tool_handlers.list_performance_counters(),
        "get_vm_summary_stats": lambda args: tool_handlers.get_vm_summary_stats(**args),
        "get_vm_performance": lambda args: tool_handlers.get_vm_performance(**args),
        "create_vm_custom": lambda args: tool_handlers.create_vm_custom(**args),
        "power_on_vm": lambda args: tool_handlers.power_on(**args),
        "power_off_vm": lambda args: tool_handlers.power_off(**args),
    }
    
    resources = {
        "vmStats": types.Resource(
            name="vmStats",
            uri="vmstats://{vm_name}",
            description="Get CPU, memory, storage, network usage of a VM",
            mimeType="application/json"
        )
    }
    
    # Register tool handlers using decorators
    @mcp_server.list_tools()
    async def list_tools_handler():
        """List all available tools."""
        return list(tools.values())
    
    @mcp_server.call_tool()
    async def call_tool_handler(name: str, arguments: dict):
        """Handle tool calls."""
        if name not in tool_handler_map:
            raise ValueError(f"Unknown tool: {name}")
        
        # Call the handler function
        handler = tool_handler_map[name]
        result = handler(arguments)
        
        # Return result as text content
        if isinstance(result, (dict, list)):
            text = json.dumps(result, indent=2)
        else:
            text = str(result)
        
        return [types.TextContent(type="text", text=text)]
    
    # Register resource handlers
    @mcp_server.list_resources()
    async def list_resources_handler():
        """List all available resources."""
        return list(resources.values())
    
    @mcp_server.read_resource()
    async def read_resource_handler(uri: str):
        """Handle resource reads."""
        # Parse URI to extract resource name and parameters
        for resource_name, resource in resources.items():
            if uri.startswith(resource.uri.split("{")[0]):
                # Extract parameters from URI
                # For vmstats://{vm_name}, extract vm_name
                if resource_name == "vmStats":
                    vm_name = uri.replace("vmstats://", "")
                    result = tool_handlers.vm_performance_resource(vm_name)
                    # Return resource content
                    return [types.TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]
        
        raise ValueError(f"Unknown resource: {uri}")
