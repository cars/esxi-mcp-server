#!/bin/bash

# Docker entrypoint script for ESXi MCP Server
set -e

# Function to wait for configuration file
wait_for_config() {
    local config_file="/app/config/config.yaml"
    local max_wait=30
    local count=0
    
    echo "Waiting for configuration file..."
    while [ ! -f "$config_file" ] && [ $count -lt $max_wait ]; do
        echo "Configuration file not found, waiting... ($count/$max_wait)"
        sleep 2
        count=$((count + 1))
    done
    
    if [ ! -f "$config_file" ]; then
        echo "Warning: Configuration file not found. Using environment variables."
        return 1
    fi
    
    echo "Configuration file found: $config_file"
    return 0
}

# Function to validate required environment variables
validate_env() {
    local required_vars=("ESXI_HOST" "ESXI_USER" "ESXI_PASSWORD")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        echo "Error: Missing required environment variables: ${missing_vars[*]}"
        echo "Please set these variables or provide a configuration file."
        exit 1
    fi
}

# Function to create configuration from environment variables
create_config_from_env() {
    local config_file="/app/config/config.yaml"
    
    echo "Creating configuration from environment variables..."
    
    cat > "$config_file" << EOF
esxi_host: "${ESXI_HOST}"
esxi_user: "${ESXI_USER}"
esxi_password: "${ESXI_PASSWORD}"
EOF

    # Add optional configuration
    [ -n "$ESXI_DATASTORE" ] && echo "datastore: \"${ESXI_DATASTORE}\"" >> "$config_file"
    [ -n "$ESXI_NETWORK" ] && echo "network: \"${ESXI_NETWORK}\"" >> "$config_file"
    [ -n "$ESXI_INSECURE" ] && echo "insecure: ${ESXI_INSECURE}" >> "$config_file"
    [ -n "$MCP_API_KEY" ] && echo "api_key: \"${MCP_API_KEY}\"" >> "$config_file"
    [ -n "$MCP_LOG_LEVEL" ] && echo "log_level: \"${MCP_LOG_LEVEL}\"" >> "$config_file"
    
    # Always set log file path
    echo "log_file: \"/app/logs/vmware_mcp.log\"" >> "$config_file"
    
    echo "Configuration file created successfully."
}

# Main execution
echo "Starting ESXi MCP Server..."

# Create logs directory if it doesn't exist
mkdir -p /app/logs

# Check if configuration file exists, if not try to create from environment
if ! wait_for_config; then
    validate_env
    create_config_from_env
fi

# Print configuration info (without sensitive data)
echo "Server starting with configuration:"
echo "  Host: ${ESXI_HOST:-'from config file'}"
echo "  User: ${ESXI_USER:-'from config file'}"
echo "  Log Level: ${MCP_LOG_LEVEL:-INFO}"
echo "  Port: 8080"

# Execute the main command
exec "$@" 