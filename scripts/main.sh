#!/bin/bash

# Main script to launch all Huntarr services in parallel
echo "Starting Huntarr multi-threaded backend services..."

# Define script directory in a way that works on both Linux and macOS
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Make sure all scripts are executable
chmod +x "$SCRIPT_DIR/sonarr_task.sh"
chmod +x "$SCRIPT_DIR/radarr_task.sh"
chmod +x "$SCRIPT_DIR/readarr_task.sh"
chmod +x "$SCRIPT_DIR/lidarr_task.sh"

# Create log directory
mkdir -p /config/logs

# Create locks directory
mkdir -p /config/locks

# Function to run a service once
run_service() {
    local service=$1
    local lock_file="/config/locks/${service}.lock"
    
    # Check if lock exists
    if mkdir "$lock_file" 2>/dev/null; then
        # Lock acquired, run the service
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting $service task..."
        "$SCRIPT_DIR/${service}_task.sh" >> "/config/logs/${service}.log" 2>&1
        
        # Release lock
        rmdir "$lock_file"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - $service task completed"
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - $service is already running, skipping"
    fi
}

# Main loop to keep container running
while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting service execution cycle..."
    
    # Run all services in parallel
    run_service "sonarr" &
    run_service "radarr" &
    run_service "readarr" &
    run_service "lidarr" &
    
    # Wait for all background processes to complete
    wait
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') - All services completed their cycle"
    
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
    
    # Sleep before starting the next cycle
    sleep 60
done