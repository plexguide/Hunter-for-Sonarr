#!/bin/bash

# Initialize settings script for Huntarr
# This script copies missing JSON configuration files from /app/support to /config/settings

echo "$(date '+%Y-%m-%d %H:%M:%S') - Initializing Huntarr settings..."

# Ensure the settings directory exists
mkdir -p /config/settings

# Define the source and destination directories
SOURCE_DIR="/app/support"
DEST_DIR="/config/settings"

# Array of expected configuration files
CONFIG_FILES=("sonarr.json" "radarr.json" "lidarr.json" "readarr.json")

# Loop through each config file and copy if missing
for config_file in "${CONFIG_FILES[@]}"; do
    if [ ! -f "${DEST_DIR}/${config_file}" ]; then
        # Check if source file exists
        if [ -f "${SOURCE_DIR}/${config_file}" ]; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Copying missing ${config_file} to ${DEST_DIR}"
            cp "${SOURCE_DIR}/${config_file}" "${DEST_DIR}/${config_file}"
            
            # Set proper permissions
            chmod 644 "${DEST_DIR}/${config_file}"
        else
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Warning: Source file ${SOURCE_DIR}/${config_file} not found"
        fi
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - ${config_file} already exists in ${DEST_DIR}"
    fi
done

echo "$(date '+%Y-%m-%d %H:%M:%S') - Settings initialization complete"
