"""MCP tool handler functions."""

import logging
from typing import Optional

from .vmware_manager import VMwareManager
from .config import Config


class ToolHandlers:
    """Container for MCP tool handler functions."""
    
    def __init__(self, manager: VMwareManager, config: Config):
        self.manager = manager
        self.config = config
    
    def _check_auth(self):
        """Internal helper: Check API access permissions."""
        if self.config.api_key:
            # If an API key is configured, require that manager.authenticated is True
            if not self.manager.authenticated:
                raise Exception("Unauthorized: API key required.")
    
    def authenticate(self, key: str) -> str:
        """Validate the API key and enable subsequent operations upon success."""
        if self.config.api_key and key == self.config.api_key:
            self.manager.authenticated = True
            logging.info("API key verification successful, client is authorized")
            return "Authentication successful."
        else:
            logging.warning("API key verification failed")
            raise Exception("Authentication failed: invalid API key.")
    
    def ping(self, message: str = "pong") -> str:
        """A simple test tool that echoes back a message."""
        return f"Ping response: {message}"
    
    def create_vm(self, name: str, cpu: int, memory: int, datastore: Optional[str] = None, network: Optional[str] = None) -> str:
        """Create a new virtual machine."""
        self._check_auth()
        return self.manager.create_vm(name, cpu, memory, datastore, network)
    
    def clone_vm(self, template_name: str, new_name: str) -> str:
        """Clone a virtual machine from a template."""
        self._check_auth()
        return self.manager.clone_vm(template_name, new_name)
    
    def delete_vm(self, name: str) -> str:
        """Delete the specified virtual machine."""
        self._check_auth()
        return self.manager.delete_vm(name)
    
    def power_on(self, name: str) -> str:
        """Power on the specified virtual machine."""
        self._check_auth()
        return self.manager.power_on_vm(name)
    
    def power_off(self, name: str) -> str:
        """Power off the specified virtual machine."""
        self._check_auth()
        return self.manager.power_off_vm(name)
    
    def list_vms(self) -> list:
        """Return a list of all virtual machine names."""
        self._check_auth()
        return self.manager.list_vms()
    
    def get_vm_details(self, vm_name: str) -> dict:
        """Get detailed information about a virtual machine."""
        self._check_auth()
        return self.manager.get_vm_details(vm_name)
    
    def list_templates(self) -> list:
        """List all virtual machine templates."""
        self._check_auth()
        return self.manager.list_templates()
    
    def list_datastores(self) -> list:
        """List all datastores."""
        self._check_auth()
        return self.manager.list_datastores()
    
    def list_networks(self) -> list:
        """List all networks."""
        self._check_auth()
        return self.manager.list_networks()
    
    def list_hosts(self) -> list:
        """List all ESXi hosts."""
        self._check_auth()
        return self.manager.list_hosts()
    
    def get_host_details(self, host_name: str) -> dict:
        """Get detailed information about a host."""
        self._check_auth()
        return self.manager.get_host_details(host_name)
    
    def get_host_performance_metrics(self, host_name: str) -> dict:
        """Get performance metrics for a host."""
        self._check_auth()
        return self.manager.get_host_performance_metrics(host_name)
    
    def get_host_hardware_health(self, host_name: str) -> dict:
        """Get hardware health information for a host."""
        self._check_auth()
        return self.manager.get_host_hardware_health(host_name)
    
    def get_host_performance(self, host_name: str) -> dict:
        """Get detailed performance data for a host."""
        self._check_auth()
        return self.manager.get_host_performance(host_name)
    
    def list_performance_counters(self) -> list:
        """List all available performance counters."""
        self._check_auth()
        return self.manager.list_performance_counters()
    
    def get_vm_summary_stats(self, vm_name: str) -> dict:
        """Get summary statistics for a virtual machine."""
        self._check_auth()
        return self.manager.get_vm_summary_stats(vm_name)
    
    def get_vm_performance(self, vm_name: str) -> dict:
        """Get performance data for a virtual machine."""
        self._check_auth()
        return self.manager.get_vm_performance(vm_name)
    
    def create_vm_custom(self, name: str, cpu: int, memory: int, disk_size_gb: int = 10,
                        guest_id: str = "otherGuest", datastore: Optional[str] = None,
                        network: Optional[str] = None, thin_provisioned: bool = True,
                        annotation: Optional[str] = None) -> str:
        """Create a custom virtual machine with advanced options."""
        self._check_auth()
        return self.manager.create_vm_custom(name, cpu, memory, disk_size_gb, guest_id,
                                            datastore, network, thin_provisioned, annotation)
    
    def vm_performance_resource(self, vm_name: str) -> dict:
        """Retrieve CPU, memory, storage, and network usage for the specified virtual machine."""
        self._check_auth()
        return self.manager.get_vm_performance(vm_name)
