#!/bin/bash

# API Helper functions for Readarr
# This script provides common functions for interacting with the Readarr API

# Load configuration
load_config() {
    local config_file="/config/settings/readarr.json"
    
    if [ ! -f "$config_file" ]; then
        echo "ERROR: Readarr configuration file not found at $config_file"
        return 1
    fi
    
    # Export variables for API usage
    export API_KEY=$(grep -o '"api_key"[^,}]*' "$config_file" | cut -d '"' -f 4)
    export APP_URL=$(grep -o '"app_url"[^,}]*' "$config_file" | cut -d '"' -f 4)
    export API_TIMEOUT=$(grep -o '"api_timeout"[^,}]*' "$config_file" | grep -o '[0-9]\+')
    export DEBUG_MODE=$(grep -o '"debug_mode"[^,}]*' "$config_file" | grep -o 'true\|false')
    
    # Remove trailing slash from APP_URL if present
    APP_URL=${APP_URL%/}
    
    if [[ "$API_KEY" == "your-radarr-api-key" || -z "$API_KEY" ]]; then
        echo "ERROR: API key is not configured properly in $config_file"
        return 1
    fi
    
    if [[ "$APP_URL" == "http://your-readarr-url:8787" || -z "$APP_URL" ]]; then
        echo "ERROR: App URL is not configured properly in $config_file"
        return 1
    fi
    
    if [ -z "$API_TIMEOUT" ]; then
        export API_TIMEOUT=60
    fi
    
    return 0
}

# Make API request
# Usage: make_api_request "endpoint" ["GET"|"POST"|"PUT"|"DELETE"] [data]
make_api_request() {
    local endpoint="$1"
    local method="${2:-GET}"
    local data="$3"
    local curl_cmd
    local response
    
    # Ensure URL is properly formatted
    local full_url="${APP_URL}${endpoint}"
    
    # Build curl command
    curl_cmd="curl -s -X $method"
    curl_cmd="$curl_cmd -H \"X-Api-Key: $API_KEY\""
    curl_cmd="$curl_cmd -H \"Content-Type: application/json\""
    
    # Add timeout option
    curl_cmd="$curl_cmd --connect-timeout $API_TIMEOUT"
    
    # Add data for POST/PUT requests
    if [ "$method" == "POST" ] || [ "$method" == "PUT" ]; then
        curl_cmd="$curl_cmd -d '$data'"
    fi
    
    # Add URL
    curl_cmd="$curl_cmd \"$full_url\""
    
    # Debug mode
    if [ "$DEBUG_MODE" == "true" ]; then
        echo "DEBUG: API Request: $curl_cmd"
    fi
    
    # Execute request
    response=$(eval $curl_cmd)
    
    # Debug mode
    if [ "$DEBUG_MODE" == "true" ]; then
        echo "DEBUG: API Response: $response"
    fi
    
    echo "$response"
}

# Get author list
get_authors() {
    make_api_request "/api/v1/author"
}

# Get book list
get_books() {
    make_api_request "/api/v1/book"
}

# Get single author by ID
get_author_by_id() {
    local author_id="$1"
    make_api_request "/api/v1/author/$author_id"
}

# Get monitored books with missing files
get_missing_books() {
    local monitored_only=$(grep -o '"monitored_only"[^,}]*' "/config/settings/readarr.json" | grep -o 'true\|false')
    
    if [ "$monitored_only" == "true" ]; then
        make_api_request "/api/v1/wanted/missing?monitored=true"
    else
        make_api_request "/api/v1/wanted/missing"
    fi
}

# Get books that need upgrading
get_upgrade_books() {
    local monitored_only=$(grep -o '"monitored_only"[^,}]*' "/config/settings/readarr.json" | grep -o 'true\|false')
    
    if [ "$monitored_only" == "true" ]; then
        make_api_request "/api/v1/wanted/cutoff?monitored=true"
    else
        make_api_request "/api/v1/wanted/cutoff"
    fi
}

# Refresh author by ID
refresh_author() {
    local author_id="$1"
    make_api_request "/api/v1/command" "POST" "{\"name\":\"RefreshAuthor\",\"authorId\":$author_id}"
}

# Search for book by ID
search_book() {
    local book_id="$1"
    make_api_request "/api/v1/command" "POST" "{\"name\":\"BookSearch\",\"bookIds\":[$book_id]}"
}

# Check if we need to load config (can be sourced by other scripts)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    load_config
fi
