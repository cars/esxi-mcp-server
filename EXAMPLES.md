# MCP Tools Usage Examples

This document provides examples of how to use the implemented MCP tools.

## Prerequisites

1. Configure your vCenter/ESXi connection in `config.yaml`:
```yaml
vcenter_host: "your-vcenter-ip"
vcenter_user: "administrator@vsphere.local"
vcenter_password: "your-password"
api_key: "your-api-key"
insecure: true  # For testing with self-signed certificates
```

2. Start the server:
```bash
python server.py -c config.yaml --transport http
```

## Example Usage

### VM Management

#### List all VMs
```json
{
  "tool": "list_vms",
  "arguments": {}
}
```

#### Get VM details
```json
{
  "tool": "get_vm_details",
  "arguments": {
    "vm_name": "my-vm"
  }
}
```

#### Get VM performance
```json
{
  "tool": "get_vm_performance",
  "arguments": {
    "vm_name": "my-vm"
  }
}
```

#### Get VM summary statistics
```json
{
  "tool": "get_vm_summary_stats",
  "arguments": {
    "vm_name": "my-vm"
  }
}
```

#### Power on a VM
```json
{
  "tool": "power_on_vm",
  "arguments": {
    "name": "my-vm"
  }
}
```

#### Power off a VM
```json
{
  "tool": "power_off_vm",
  "arguments": {
    "name": "my-vm"
  }
}
```

#### Create a custom VM
```json
{
  "tool": "create_vm_custom",
  "arguments": {
    "name": "new-vm",
    "cpu": 4,
    "memory": 8192,
    "disk_size_gb": 50,
    "guest_id": "ubuntu64Guest",
    "datastore": "datastore1",
    "network": "VM Network",
    "thin_provisioned": true,
    "annotation": "Created via MCP"
  }
}
```

### Infrastructure Management

#### List templates
```json
{
  "tool": "list_templates",
  "arguments": {}
}
```

#### List datastores
```json
{
  "tool": "list_datastores",
  "arguments": {}
}
```

#### List networks
```json
{
  "tool": "list_networks",
  "arguments": {}
}
```

### Host Management

#### List hosts
```json
{
  "tool": "list_hosts",
  "arguments": {}
}
```

#### Get host details
```json
{
  "tool": "get_host_details",
  "arguments": {
    "host_name": "esxi-host-1.example.com"
  }
}
```

#### Get host performance metrics
```json
{
  "tool": "get_host_performance_metrics",
  "arguments": {
    "host_name": "esxi-host-1.example.com"
  }
}
```

#### Get host hardware health
```json
{
  "tool": "get_host_hardware_health",
  "arguments": {
    "host_name": "esxi-host-1.example.com"
  }
}
```

#### Get host performance
```json
{
  "tool": "get_host_performance",
  "arguments": {
    "host_name": "esxi-host-1.example.com"
  }
}
```

### Performance Monitoring

#### List performance counters
```json
{
  "tool": "list_performance_counters",
  "arguments": {}
}
```

## Response Examples

### list_vms response
```json
[
  "vm-1",
  "vm-2",
  "vm-3",
  "template-ubuntu"
]
```

### get_vm_details response
```json
{
  "name": "vm-1",
  "power_state": "poweredOn",
  "guest_os": "Ubuntu Linux (64-bit)",
  "cpu_count": 4,
  "memory_mb": 8192,
  "uuid": "502d1d77-...",
  "instance_uuid": "502d2a88-...",
  "ip_address": "192.168.1.100",
  "tools_status": "toolsOk",
  "tools_version": "11269",
  "hostname": "vm-1.example.com",
  "template": false,
  "annotation": "Production web server",
  "disks": [
    {
      "label": "Hard disk 1",
      "capacity_gb": 50.0,
      "disk_mode": "persistent"
    }
  ],
  "networks": [
    {
      "label": "Network adapter 1",
      "mac_address": "00:50:56:...",
      "connected": true,
      "network": "VM Network"
    }
  ]
}
```

### get_host_details response
```json
{
  "name": "esxi-host-1.example.com",
  "connection_state": "connected",
  "power_state": "poweredOn",
  "in_maintenance_mode": false,
  "vendor": "Dell Inc.",
  "model": "PowerEdge R640",
  "uuid": "4234e77d-...",
  "cpu_model": "Intel(R) Xeon(R) Gold 6240 CPU @ 2.60GHz",
  "cpu_cores": 36,
  "cpu_threads": 72,
  "cpu_mhz": 2600,
  "memory_gb": 256.0,
  "hypervisor_version": "7.0.3",
  "hypervisor_build": "19193900"
}
```

### list_datastores response
```json
[
  {
    "name": "datastore1",
    "type": "VMFS",
    "capacity_gb": 2048.0,
    "free_space_gb": 1024.5,
    "accessible": true,
    "maintenance_mode": "normal"
  },
  {
    "name": "datastore2",
    "type": "NFS",
    "capacity_gb": 4096.0,
    "free_space_gb": 3072.8,
    "accessible": true,
    "maintenance_mode": "normal"
  }
]
```

## Integration with MCP Clients

When using with MCP clients like Claude Desktop, the tools are automatically discovered and can be invoked conversationally:

- "List all VMs in my vCenter"
- "Show me details about vm-1"
- "What's the performance of esxi-host-1?"
- "Create a new VM called web-server with 4 CPUs and 8GB RAM"
- "Power on the database-vm"

The MCP client will automatically call the appropriate tools and parse the responses.
