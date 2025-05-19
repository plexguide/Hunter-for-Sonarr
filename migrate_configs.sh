#!/bin/bash

# Migration script for Huntarr JSON configuration files in Docker environment
# Moves config files from /config/ to /config/settings/ during container startup

# Define the source and destination directories
# These paths are relative to the Docker container filesystem
SOURCE_DIR="/config"
DEST_DIR="/config/settings"

# List of JSON files to migrate
JSON_FILES=("eros.json" "lidarr.json" "readarr.json" "swaparr.json" "general.json" "radarr.json" "sonarr.json" "whisparr.json")

# Flag to track if any files were found and migrated
FILES_MIGRATED=false

# Check if we're in the Docker environment
if [ ! -d "$SOURCE_DIR" ]; then
    echo "WARNING: Source directory $SOURCE_DIR not found. Is this running inside the Docker container?"
    exit 0
fi

# Ensure the destination directory exists with proper permissions
mkdir -p "$DEST_DIR"
chmod 755 "$DEST_DIR"

# Log function for better clarity
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Huntarr Migration: $1"
}

log_message "Starting Docker configuration migration check"

# Check if any of the JSON files exist in the old location
for json_file in "${JSON_FILES[@]}"; do
    source_file="$SOURCE_DIR/$json_file"
    dest_file="$DEST_DIR/$json_file"
    
    # If the file exists in the old location
    if [ -f "$source_file" ]; then
        log_message "Found $json_file in old location: $source_file"
        FILES_MIGRATED=true
        
        # Copy the file to the new location, overwriting if it exists
        cp -f "$source_file" "$dest_file"
        
        # Check if the copy was successful
        if [ $? -eq 0 ]; then
            log_message "Successfully migrated $json_file to $DEST_DIR"
            
            # Set proper permissions on the new file
            chmod 644 "$dest_file"
            
            # Remove the original file
            rm "$source_file"
            
            if [ $? -eq 0 ]; then
                log_message "Removed original $json_file from old location"
            else
                log_message "WARNING: Failed to remove original $json_file from old location"
            fi
        else
            log_message "ERROR: Failed to migrate $json_file to $DEST_DIR"
        fi
    fi
done

# If no files were migrated, log it and exit
if [ "$FILES_MIGRATED" = false ]; then
    log_message "No legacy configuration files found in Docker volume. Nothing to migrate."
    exit 0
fi

log_message "Docker configuration migration completed"
exit 0
