#!/bin/bash

# Radarr service script for Huntarr
echo "$(date '+%Y-%m-%d %H:%M:%S') - Radarr task started"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Make sure the sub-scripts are executable
chmod +x "$SCRIPT_DIR/missing.sh"
chmod +x "$SCRIPT_DIR/upgrade.sh"

# Execute the missing content search module
echo "$(date '+%Y-%m-%d %H:%M:%S') - Executing Radarr missing content module"
"$SCRIPT_DIR/missing.sh"
MISSING_STATUS=$?

# Execute the quality upgrade module
echo "$(date '+%Y-%m-%d %H:%M:%S') - Executing Radarr quality upgrade module"
"$SCRIPT_DIR/upgrade.sh"
UPGRADE_STATUS=$?

# Check if any module failed
if [ $MISSING_STATUS -ne 0 ] || [ $UPGRADE_STATUS -ne 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - WARNING: One or more Radarr modules returned an error"
fi

# Echo app name and time at the end
echo "Radarr task completed at $(date '+%Y-%m-%d %H:%M:%S')"
