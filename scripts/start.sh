#!/bin/bash

# Entry point script for Huntarr Docker container
echo "Initializing Huntarr container..."

# Create necessary directories
mkdir -p /config/settings

# Copy default.json to config if it doesn't exist
if [ ! -f "/config/settings/huntarr.json" ]; then
    echo "First run detected, copying default settings..."
    cp /app/support/default.json /config/settings/huntarr.json
fi

# Create log directory
mkdir -p /config/logs

# Define script directory in a way that works on both Linux and macOS
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Make sure the main script is executable
chmod +x "$SCRIPT_DIR/main.sh"

# Start the main multithreading script
echo "Starting Huntarr with multi-thread services..."
exec "$SCRIPT_DIR/main.sh"