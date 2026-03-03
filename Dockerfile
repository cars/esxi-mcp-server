# Use official Python runtime as base image
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user for security
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Set working directory
WORKDIR /app

# Install only runtime system dependencies (including bash for entrypoint script)
RUN apt-get update && apt-get install -y \
    ca-certificates \
    bash \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ovftool (required for clone_vm tool)
# ovftool is a proprietary VMware binary and cannot be bundled automatically.
# Download from: https://developer.broadcom.com/tools/vmware-ovf-tool/latest
# To include in this image, copy the binary into the build context and add:
#   COPY ovftool /usr/local/bin/ovftool
#   RUN chmod +x /usr/local/bin/ovftool
# Without ovftool, clone_vm will return a RuntimeError explaining the requirement.

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/mcpuser/.local
COPY  ./esxi_mcp_server  /home/mcpuser/.local/lib/python3.11/site-packages/esxi_mcp_server

# Copy application code
COPY server.py .
COPY config.yaml.sample .
COPY docker-entrypoint.sh .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Create necessary directories and set permissions
RUN mkdir -p /app/logs /app/config \
    && chown -R mcpuser:mcpuser /app

# Set environment variables
ENV PATH=/home/mcpuser/.local/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Switch to non-root user
USER mcpuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080')" || exit 1

# Set entrypoint and default command
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "server.py", "--config", "/app/config/config.yaml"] 
