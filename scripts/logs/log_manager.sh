#!/bin/bash

# Log management script for Huntarr
# Handles log rotation and other log-related functionality

# Create log directory if it doesn't exist
mkdir -p /config/logs

# Function to perform log rotation
rotate_logs() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting log rotation check..."
    
    # Simple log rotation (keep logs from growing too large)
    for log_file in /config/logs/*.log; do
        if [ -f "$log_file" ]; then
            # Get file size in a way that works on both Linux and macOS
            file_size=$(wc -c < "$log_file")
            # Rotate if file is larger than 10MB
            if [ $file_size -gt 10485760 ]; then
                echo "$(date '+%Y-%m-%d %H:%M:%S') - Rotating log file: $log_file"
                mv "$log_file" "${log_file}.old"
                touch "$log_file"
            fi
        fi
    done
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Log rotation check completed"
}

# Execute the main function if this script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    rotate_logs
fi
