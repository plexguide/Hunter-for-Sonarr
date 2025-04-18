#!/bin/bash

# Orchestrator script to launch all Huntarr services in parallel
echo "Starting Huntarr multi-threaded backend services with orchestrator..."

# Define script directory in a way that works on both Linux and macOS
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICES_DIR="$SCRIPT_DIR/../services"
LOGS_DIR="$SCRIPT_DIR/logs"

# Make sure directories exist
mkdir -p "$SERVICES_DIR"
mkdir -p "$LOGS_DIR"
mkdir -p /config/logs
mkdir -p /config/locks

# Create service-specific directories and ensure scripts are executable
for service in sonarr radarr readarr lidarr; do
    mkdir -p "$SERVICES_DIR/$service"
    # Make sure the scripts are executable
    if [ -f "$SERVICES_DIR/$service/$service.sh" ]; then
        chmod +x "$SERVICES_DIR/$service/$service.sh"
    else
        echo "Warning: Service script $SERVICES_DIR/$service/$service.sh not found"
    fi
done

chmod +x "$LOGS_DIR/log_manager.sh"

# Function to continuously run a service in a loop
run_service_loop() {
    local service=$1
    local lock_file="/config/locks/${service}.lock"
    local sleep_time=5  # Default sleep time between cycles (can be adjusted per service)
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting ${service} service loop"
    
    # Run the service in a continuous loop
    while true; do
        # Check if lock exists
        if mkdir "$lock_file" 2>/dev/null; then
            # Lock acquired, run the service
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting $service task..."
            "$SERVICES_DIR/${service}/${service}.sh" >> "/config/logs/${service}.log" 2>&1
            
            # Release lock
            rmdir "$lock_file"
            echo "$(date '+%Y-%m-%d %H:%M:%S') - $service task completed, waiting ${sleep_time}s before next cycle"
        else
            echo "$(date '+%Y-%m-%d %H:%M:%S') - $service is already running, skipping this cycle"
        fi
        
        # Sleep before next iteration
        sleep $sleep_time
    done
}

# Start each service in its own background loop
run_service_loop "sonarr" &
run_service_loop "radarr" &
run_service_loop "readarr" &
run_service_loop "lidarr" &

# Main loop for log rotation and container health monitoring
while true; do
    # Run the log rotation script
    "$LOGS_DIR/log_manager.sh" >> "/config/logs/log_manager.log" 2>&1
    
    # Sleep before checking logs again
    sleep 300  # Check logs every 5 minutes
done
