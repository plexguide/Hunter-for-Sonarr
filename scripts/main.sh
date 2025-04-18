#!/bin/bash

# Main script to launch all Huntarr services in parallel
echo "Starting Huntarr multi-threaded backend services..."

# Define script directory in a way that works on both Linux and macOS
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Make sure all scripts are executable
chmod +x "$SCRIPT_DIR/sonarr.sh"
chmod +x "$SCRIPT_DIR/radarr.sh"
chmod +x "$SCRIPT_DIR/readarr.sh"
chmod +x "$SCRIPT_DIR/lidarr.sh"

# Create log directory
mkdir -p /config/logs

# Function to check if a process is running
check_process() {
    local pid=$1
    local name=$2
    if ps -p $pid > /dev/null; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - $name is running (PID: $pid)"
        return 0
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - WARNING: $name is not running! Restarting..."
        return 1
    fi
}

# Function to restart a service
restart_service() {
    local script=$1
    local name=$2
    local log_file=$3
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Restarting $name service..."
    "$SCRIPT_DIR/$script" > "$log_file" 2>&1 &
    local new_pid=$!
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $name restarted with PID: $new_pid"
    echo $new_pid
}

# Start all services in background
"$SCRIPT_DIR/sonarr.sh" > /config/logs/sonarr.log 2>&1 &
SONARR_PID=$!

"$SCRIPT_DIR/radarr.sh" > /config/logs/radarr.log 2>&1 &
RADARR_PID=$!

"$SCRIPT_DIR/readarr.sh" > /config/logs/readarr.log 2>&1 &
READARR_PID=$!

"$SCRIPT_DIR/lidarr.sh" > /config/logs/lidarr.log 2>&1 &
LIDARR_PID=$!

echo "All services started in parallel:"
echo "Sonarr PID: $SONARR_PID"
echo "Radarr PID: $RADARR_PID"
echo "Readarr PID: $READARR_PID"
echo "Lidarr PID: $LIDARR_PID"

# Keep container running and monitor services
while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Main process monitoring all services..."
    
    # Check if services are still running and restart if needed
    if ! check_process $SONARR_PID "Sonarr"; then
        SONARR_PID=$(restart_service "sonarr.sh" "Sonarr" "/config/logs/sonarr.log")
    fi
    
    if ! check_process $RADARR_PID "Radarr"; then
        RADARR_PID=$(restart_service "radarr.sh" "Radarr" "/config/logs/radarr.log")
    fi
    
    if ! check_process $READARR_PID "Readarr"; then
        READARR_PID=$(restart_service "readarr.sh" "Readarr" "/config/logs/readarr.log")
    fi
    
    if ! check_process $LIDARR_PID "Lidarr"; then
        LIDARR_PID=$(restart_service "lidarr.sh" "Lidarr" "/config/logs/lidarr.log")
    fi
    
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
    
    sleep 60
done