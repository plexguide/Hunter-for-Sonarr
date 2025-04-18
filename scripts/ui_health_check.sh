#!/bin/bash

LOG_FILE="/config/logs/ui_health_check.log"
UI_URL="http://localhost:9705"

# Function to check UI health
check_ui_health() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Performing UI health check..." >> $LOG_FILE

    # Use curl to check if the UI is responding
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $UI_URL)
    
    if [ "$RESPONSE" = "200" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - UI health check SUCCESS: UI is responding properly (HTTP 200)" >> $LOG_FILE
        return 0
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - UI health check FAILED: UI returned HTTP $RESPONSE" >> $LOG_FILE
        return 1
    fi
}

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Log startup
echo "$(date '+%Y-%m-%d %H:%M:%S') - UI health check service started" >> $LOG_FILE

# Main loop
while true; do
    check_ui_health
    
    # Sleep for 5 minutes before next check
    sleep 300
done
