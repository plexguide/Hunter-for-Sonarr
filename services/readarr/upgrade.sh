#!/bin/bash

# Readarr Quality Upgrade Handler
echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: Starting quality upgrade search"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Include the API helper functions
source "$SCRIPT_DIR/api_helper.sh"

# Create state directory if it doesn't exist
STATE_DIR="/config/stateful/readarr"
mkdir -p "$STATE_DIR"
PROCESSED_FILE="$STATE_DIR/processed_upgrade_books.txt"

# Load settings from config
CONFIG_FILE="/config/settings/readarr.json"
if [ -f "$CONFIG_FILE" ]; then
    # Load API config
    if ! load_config; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: ERROR - Failed to load API configuration"
        exit 1
    fi
    
    # Read configuration values that affect quality upgrades
    HUNT_UPGRADE=$(grep -o '"hunt_upgrade_books"[^,}]*' "$CONFIG_FILE" | grep -o '[0-9]\+')
    MONITORED_ONLY=$(grep -o '"monitored_only"[^,}]*' "$CONFIG_FILE" | grep -o 'true\|false')
    REFRESH_AUTHOR=$(grep -o '"refresh_author"[^,}]*' "$CONFIG_FILE" | grep -o 'true\|false')
    RANDOM_SELECTION=$(grep -o '"random_selection"[^,}]*' "$CONFIG_FILE" | grep -o 'true\|false')
    STATE_RESET_HOURS=$(grep -o '"state_reset_interval_hours"[^,}]*' "$CONFIG_FILE" | grep -o '[0-9]\+')
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: Will process up to $HUNT_UPGRADE books for quality upgrade"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: Monitored only: $MONITORED_ONLY"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: Refresh author: $REFRESH_AUTHOR"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: Random selection: $RANDOM_SELECTION"
    
    # Check if we need to reset the state based on the reset interval
    if [ -f "$PROCESSED_FILE" ]; then
        FILE_AGE=$(( $(date +%s) - $(stat -c %Y "$PROCESSED_FILE" 2>/dev/null || stat -f %m "$PROCESSED_FILE") ))
        if [ $FILE_AGE -gt $(( STATE_RESET_HOURS * 3600 )) ]; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: State file is older than $STATE_RESET_HOURS hours, resetting"
            rm "$PROCESSED_FILE"
            touch "$PROCESSED_FILE"
        fi
    else
        touch "$PROCESSED_FILE"
    fi
    
    # Get books that need upgrading
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: Fetching books needing quality upgrade"
    UPGRADE_BOOKS=$(get_upgrade_books)
    
    if [ -z "$UPGRADE_BOOKS" ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: No books needing upgrade found or error fetching list"
        exit 0
    fi
    
    # Extract book IDs and filter out already processed ones
    BOOK_IDS=()
    
    # Extract all records and their IDs for filtering
    while read -r book_id; do
        if ! grep -q "^$book_id$" "$PROCESSED_FILE"; then
            BOOK_IDS+=("$book_id")
        fi
    done < <(echo "$UPGRADE_BOOKS" | grep -o '"id":[0-9]*' | grep -o '[0-9]*')
    
    TOTAL_BOOKS=${#BOOK_IDS[@]}
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: Found $TOTAL_BOOKS unprocessed books needing quality upgrade"
    
    # Process books
    PROCESSED_COUNT=0
    
    # If no books to process, exit
    if [ $TOTAL_BOOKS -eq 0 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: No unprocessed books needing upgrade to search for"
        exit 0
    fi
    
    # Select books to process
    SELECTED_BOOKS=()
    
    if [ "$RANDOM_SELECTION" = "true" ]; then
        # Randomize selection
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: Using random selection for upgrades"
        
        # Shuffle the array of book IDs
        SHUFFLED_BOOKS=($(printf "%s\n" "${BOOK_IDS[@]}" | shuf))
        
        # Take only up to HUNT_UPGRADE books
        MAX_TO_PROCESS=$((HUNT_UPGRADE < TOTAL_BOOKS ? HUNT_UPGRADE : TOTAL_BOOKS))
        for ((i=0; i<$MAX_TO_PROCESS; i++)); do
            SELECTED_BOOKS+=("${SHUFFLED_BOOKS[$i]}")
        done
    else
        # Sequential selection
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: Using sequential selection for upgrades"
        
        # Take only up to HUNT_UPGRADE books
        MAX_TO_PROCESS=$((HUNT_UPGRADE < TOTAL_BOOKS ? HUNT_UPGRADE : TOTAL_BOOKS))
        for ((i=0; i<$MAX_TO_PROCESS; i++)); do
            SELECTED_BOOKS+=("${BOOK_IDS[$i]}")
        done
    fi
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: Will process ${#SELECTED_BOOKS[@]} books for upgrade"
    
    # Process each selected book
    for book_id in "${SELECTED_BOOKS[@]}"; do
        # Get book details
        BOOK_DETAILS=$(make_api_request "/api/v1/book/$book_id")
        
        # Extract book title and author
        BOOK_TITLE=$(echo "$BOOK_DETAILS" | grep -o '"title":"[^"]*"' | cut -d'"' -f4)
        AUTHOR_ID=$(echo "$BOOK_DETAILS" | grep -o '"authorId":[0-9]*' | grep -o '[0-9]*')
        
        # Get author details
        AUTHOR_DETAILS=$(get_author_by_id "$AUTHOR_ID")
        AUTHOR_NAME=$(echo "$AUTHOR_DETAILS" | grep -o '"authorName":"[^"]*"' | cut -d'"' -f4)
        
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: Processing book for quality upgrade: $BOOK_TITLE by $AUTHOR_NAME"
        
        # Refresh author if enabled
        if [ "$REFRESH_AUTHOR" = "true" ]; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: Refreshing author: $AUTHOR_NAME"
            REFRESH_RESPONSE=$(refresh_author "$AUTHOR_ID")
            
            # Small delay after refresh
            sleep 2
        fi
        
        # Search for the book
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: Searching for book upgrade: $BOOK_TITLE by $AUTHOR_NAME"
        SEARCH_RESPONSE=$(search_book "$book_id")
        
        # Mark book as processed
        echo "$book_id" >> "$PROCESSED_FILE"
        
        PROCESSED_COUNT=$((PROCESSED_COUNT + 1))
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: Processed $PROCESSED_COUNT/$MAX_TO_PROCESS books for upgrade"
        
        # Small delay between searches to be nice to the indexers
        if [ $PROCESSED_COUNT -lt $MAX_TO_PROCESS ]; then
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: Waiting 5 seconds before next book..."
            sleep 5
        fi
    done
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: Completed quality upgrade search, processed $PROCESSED_COUNT books"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Readarr: ERROR - Configuration file not found at $CONFIG_FILE"
    exit 1
fi
