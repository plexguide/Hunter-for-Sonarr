#!/bin/bash

# Entry point script for Huntarr Docker container
echo "Initializing Huntarr container..."

# Create necessary directories
mkdir -p /config/settings
mkdir -p /config/locks

# Define script directory in a way that works on both Linux and macOS
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICES_DIR="$SCRIPT_DIR/../services"
LOGS_DIR="$SCRIPT_DIR/logs"

# Make sure directories exist
mkdir -p "$SERVICES_DIR"
mkdir -p "$LOGS_DIR"

# Make sure initialization script is executable
chmod +x "$SCRIPT_DIR/initialize_settings.sh"

# Run the initialization script to copy any missing settings files
"$SCRIPT_DIR/initialize_settings.sh"

# Make sure orchestrator script is executable
chmod +x "$SCRIPT_DIR/orchestrator.sh"

# Create service-specific directories and ensure scripts are executable
for service in sonarr radarr readarr lidarr; do
    mkdir -p "$SERVICES_DIR/$service"
    # Make sure the scripts are executable
    if [ -f "$SERVICES_DIR/$service/$service.sh" ]; then
        chmod +x "$SERVICES_DIR/$service/$service.sh"
    fi
    if [ -f "$SERVICES_DIR/$service/missing.sh" ]; then
        chmod +x "$SERVICES_DIR/$service/missing.sh"
    fi
    if [ -f "$SERVICES_DIR/$service/upgrade.sh" ]; then
        chmod +x "$SERVICES_DIR/$service/upgrade.sh"
    fi
done

# Start API server in the background
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting Huntarr API server..."
python3 /app/scripts/api.py >> /config/logs/api.log 2>&1 &

# Check if nginx is installed
if command -v nginx >/dev/null 2>&1; then
    # Start the nginx web server for UI
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting Huntarr UI web server on port 9705..."
    nginx -g "daemon off;" &
    UI_PID=$!

    # Wait a moment for nginx to start
    sleep 2

    # Check if nginx is running
    if ps -p $UI_PID > /dev/null; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Huntarr UI successfully started. Available at http://localhost:9705"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Huntarr UI failed to start properly. Check nginx logs for details."
    fi
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: nginx is not installed. UI will not be available."
    echo "$(date '+%Y-%m-%d %H:%M:%S') - To fix this, run: apt-get update && apt-get install -y nginx"
fi

# Start the orchestrator
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting Huntarr service orchestrator..."
"$SCRIPT_DIR/orchestrator.sh" >> /config/logs/orchestrator.log 2>&1 &

# Make ui health check script executable and start it
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting UI health check service..."
chmod +x "$SCRIPT_DIR/ui_health_check.sh"
"$SCRIPT_DIR/ui_health_check.sh" &

# Keep container running
tail -f /dev/null