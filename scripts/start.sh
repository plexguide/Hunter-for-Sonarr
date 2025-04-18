#!/bin/bash

# Entry point script for Huntarr Docker container
echo "Initializing Huntarr container..."

# Create necessary directories
mkdir -p /config/settings
mkdir -p /config/locks

# Copy default.json to config if it doesn't exist
if [ ! -f "/config/settings/huntarr.json" ]; then
    echo "First run detected, copying default settings..."
    cp /app/support/default.json /config/settings/huntarr.json
fi

# Create log directory
mkdir -p /config/logs

# Define script directory in a way that works on both Linux and macOS
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICES_DIR="$SCRIPT_DIR/../services"

# Make sure services directory exists
mkdir -p "$SERVICES_DIR"

# Make sure orchestrator script is executable
chmod +x "$SCRIPT_DIR/orchestrator.sh"

# Make sure all service scripts are executable
chmod +x "$SERVICES_DIR/sonarr.sh"
chmod +x "$SERVICES_DIR/radarr.sh"
chmod +x "$SERVICES_DIR/readarr.sh"
chmod +x "$SERVICES_DIR/lidarr.sh"

# Start the orchestrator script
echo "Starting Huntarr with multi-thread orchestration..."
exec "$SCRIPT_DIR/orchestrator.sh"