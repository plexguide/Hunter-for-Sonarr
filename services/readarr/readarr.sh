#!/bin/bash

# Readarr service script for Huntarr
echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr task started"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create log directory if it doesn't exist
mkdir -p /config/logs/readarr

# Load settings from config
CONFIG_FILE="/config/settings/readarr.json"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Configuration file not found at $CONFIG_FILE"
    exit 1
fi

# Make sure the sub-scripts are executable
chmod +x "$SCRIPT_DIR/missing.sh"
chmod +x "$SCRIPT_DIR/upgrade.sh"
chmod +x "$SCRIPT_DIR/api_helper.sh"

# Execute the missing content search module
echo "$(date '+%Y-%m-%d %H:%M:%S') - Executing Readarr missing content module"
"$SCRIPT_DIR/missing.sh"
MISSING_STATUS=$?

# Execute the quality upgrade module
echo "$(date '+%Y-%m-%d %H:%M:%S') - Executing Readarr quality upgrade module"
"$SCRIPT_DIR/upgrade.sh"
UPGRADE_STATUS=$?

# Check if any module failed
if [ $MISSING_STATUS -ne 0 ] || [ $UPGRADE_STATUS -ne 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - WARNING: One or more Readarr modules returned an error"
fi

# Echo app name and time at the end
echo "Readarr task completed at $(date '+%Y-%m-%d %H:%M:%S')"
