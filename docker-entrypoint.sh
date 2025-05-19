#!/bin/bash
set -e

# Docker entrypoint script for Huntarr
# This runs the migration script before starting the main application

# Log function for better clarity
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Huntarr Docker: $1"
}

log_message "Container starting up"

# Path to the migration script inside the container
MIGRATION_SCRIPT="/app/migrate_configs.sh"

# Make sure the migration script is executable
if [ -f "$MIGRATION_SCRIPT" ]; then
    chmod +x "$MIGRATION_SCRIPT"
    log_message "Running configuration migration script"
    
    # Run the migration script
    bash "$MIGRATION_SCRIPT"
    
    # Check exit status
    if [ $? -eq 0 ]; then
        log_message "Migration script completed successfully"
    else
        log_message "WARNING: Migration script encountered issues"
    fi
else
    log_message "Migration script not found at $MIGRATION_SCRIPT - skipping migration"
fi

# Get the command passed to the container
if [ $# -eq 0 ]; then
    # If no command is provided, run the default Huntarr application
    log_message "Starting Huntarr with default configuration"
    exec /app/start_huntarr.sh
else
    # If command is provided, execute it
    log_message "Running provided command: $@"
    exec "$@"
fi
