"""Configuration management for ESXi MCP Server."""

import os
import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Configuration data class for storing configuration options."""
    vcenter_host: str
    vcenter_user: str
    vcenter_password: str
    datacenter: Optional[str] = None   # Datacenter name (optional)
    cluster: Optional[str] = None      # Cluster name (optional)
    datastore: Optional[str] = None    # Datastore name (optional)
    network: Optional[str] = None      # Virtual network name (optional)
    insecure: bool = False             # Whether to skip SSL certificate verification (default: False)
    api_key: Optional[str] = None      # API access key for authentication
    log_file: Optional[str] = None     # Log file path (if not specified, output to console)
    log_level: str = "INFO"            # Log level


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
    config_data = {}
    
    # Load from file if path is provided
    if config_path:
        if config_path.endswith((".yml", ".yaml")):
            import yaml
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        elif config_path.endswith(".json"):
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        else:
            raise ValueError("Unsupported configuration file format. Please use JSON or YAML")
    
    # Override configuration from environment variables (higher priority than file)
    env_map = {
        "VCENTER_HOST": "vcenter_host",
        "VCENTER_USER": "vcenter_user",
        "VCENTER_PASSWORD": "vcenter_password",
        "VCENTER_DATACENTER": "datacenter",
        "VCENTER_CLUSTER": "cluster",
        "VCENTER_DATASTORE": "datastore",
        "VCENTER_NETWORK": "network",
        "VCENTER_INSECURE": "insecure",
        "MCP_API_KEY": "api_key",
        "MCP_LOG_FILE": "log_file",
        "MCP_LOG_LEVEL": "log_level"
    }
    
    for env_key, cfg_key in env_map.items():
        if env_key in os.environ:
            val = os.environ[env_key]
            # Boolean type conversion
            if cfg_key == "insecure":
                config_data[cfg_key] = val.lower() in ("1", "true", "yes")
            else:
                config_data[cfg_key] = val
    
    # Validate required keys
    required_keys = ["vcenter_host", "vcenter_user", "vcenter_password"]
    for k in required_keys:
        if k not in config_data or not config_data[k]:
            raise Exception(f"Missing required configuration item: {k}")
    
    return Config(**config_data)
