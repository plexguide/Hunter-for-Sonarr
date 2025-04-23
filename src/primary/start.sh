#!/bin/sh
# Startup script for Huntarr with always enabled web UI

# Ensure the configuration directories exist and have proper permissions
mkdir -p /config/settings /config/stateful /config/user /tmp/huntarr-logs
chmod -R 755 /config /tmp/huntarr-logs

# Web UI is always enabled
echo "Starting with Web UI enabled on port 9705"

# Start both the web server and the main application
cd /app
export PYTHONPATH=/app
# Use python -m to run modules correctly
python -m src.primary.web_server &
python -m main