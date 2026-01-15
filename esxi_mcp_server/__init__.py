"""ESXi MCP Server - A VMware ESXi/vCenter management server based on MCP."""

__version__ = "0.0.1"

# Lazy imports to avoid loading heavy dependencies at import time
def __getattr__(name):
    if name == "Config":
        from .config import Config
        return Config
    elif name == "load_config":
        from .config import load_config
        return load_config
    elif name == "VMwareManager":
        from .vmware_manager import VMwareManager
        return VMwareManager
    elif name == "ToolHandlers":
        from .tools import ToolHandlers
        return ToolHandlers
    elif name == "create_mcp_server":
        from .mcp_server import create_mcp_server
        return create_mcp_server
    elif name == "register_handlers":
        from .mcp_server import register_handlers
        return register_handlers
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "Config",
    "load_config",
    "VMwareManager",
    "ToolHandlers",
    "create_mcp_server",
    "register_handlers",
]
