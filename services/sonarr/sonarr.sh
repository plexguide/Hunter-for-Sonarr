#!/bin/bash

# Sonarr service script for Huntarr
echo "$(date '+%Y-%m-%d %H:%M:%S') - Sonarr task started"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Make sure the sub-scripts are executable
chmod +x "$SCRIPT_DIR/missing.sh"
chmod +x "$SCRIPT_DIR/upgrade.sh"

# Execute the missing content search module
echo "$(date '+%Y-%m-%d %H:%M:%S') - Executing Sonarr missing content module"
"$SCRIPT_DIR/missing.sh"
MISSING_STATUS=$?

# Execute the quality upgrade module
echo "$(date '+%Y-%m-%d %H:%M:%S') - Executing Sonarr quality upgrade module"
"$SCRIPT_DIR/upgrade.sh"
UPGRADE_STATUS=$?

# Check if any module failed
if [ $MISSING_STATUS -ne 0 ] || [ $UPGRADE_STATUS -ne 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - WARNING: One or more Sonarr modules returned an error"
fi

# Echo app name and time at the end
echo "Sonarr task completed at $(date '+%Y-%m-%d %H:%M:%S')"
