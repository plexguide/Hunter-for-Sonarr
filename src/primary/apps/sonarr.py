#!/usr/bin/env python3

from flask import Blueprint, request, jsonify
import datetime, os, requests
from src.primary import keys_manager
from src.primary.state import get_state_file_path

sonarr_bp = Blueprint('sonarr', __name__)

LOG_FILE = "/tmp/huntarr-logs/huntarr.log"

# Make sure we're using the correct state files
PROCESSED_MISSING_FILE = get_state_file_path("sonarr", "processed_missing") 
PROCESSED_UPGRADES_FILE = get_state_file_path("sonarr", "processed_upgrades")

@sonarr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a Sonarr API instance with comprehensive diagnostics"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')
    api_timeout = data.get('api_timeout', 30)  # Use longer timeout for connection test

    if not api_url or not api_key:
        return jsonify({"success": False, "message": "API URL and API Key are required"}), 400

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Log the test attempt
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} - sonarr - INFO - Testing connection to Sonarr API at {api_url}\n")
    
    # First check if URL is properly formatted
    if not (api_url.startswith('http://') or api_url.startswith('https://')):
        error_msg = "API URL must start with http:// or https://"
        with open(LOG_FILE, 'a') as f:
            f.write(f"{timestamp} - sonarr - ERROR - {error_msg}\n")
        return jsonify({"success": False, "message": error_msg}), 400
        
    # Create the test URL and set headers
    test_url = f"{api_url.rstrip('/')}/api/v3/system/status"
    headers = {'X-Api-Key': api_key}

    try:
        # Use a connection timeout separate from read timeout
        response = requests.get(test_url, headers=headers, timeout=(10, api_timeout))
        
        # Log HTTP status code for diagnostic purposes
        with open(LOG_FILE, 'a') as f:
            f.write(f"{timestamp} - sonarr - DEBUG - Sonarr API status code: {response.status_code}\n")
        
        # Check HTTP status code
        response.raise_for_status()

        # Ensure the response is valid JSON
        try:
            response_data = response.json()
            
            # Save keys if connection is successful
            keys_manager.save_api_keys("sonarr", api_url, api_key)
            
            with open(LOG_FILE, 'a') as f:
                f.write(f"{timestamp} - sonarr - INFO - Successfully connected to Sonarr API version: {response_data.get('version', 'unknown')}\n")

            # Return success with some useful information
            return jsonify({
                "success": True,
                "message": "Successfully connected to Sonarr API",
                "data": {
                    "version": response_data.get('version', 'unknown'),
                    "appName": response_data.get('appName', 'Sonarr'),
                    "osVersion": response_data.get('osVersion', 'unknown')
                }
            })
        except ValueError:
            error_msg = "Invalid JSON response from Sonarr API"
            with open(LOG_FILE, 'a') as f:
                f.write(f"{timestamp} - sonarr - ERROR - {error_msg}. Response content: {response.text[:200]}\n")
            return jsonify({"success": False, "message": error_msg}), 500

    except requests.exceptions.Timeout as e:
        error_msg = f"Connection timed out after {api_timeout} seconds"
        with open(LOG_FILE, 'a') as f:
            f.write(f"{timestamp} - sonarr - ERROR - {error_msg}: {str(e)}\n")
        return jsonify({"success": False, "message": error_msg}), 504
        
    except requests.exceptions.ConnectionError as e:
        error_msg = "Connection error - check hostname and port"
        details = str(e)
        # Check for common DNS resolution errors
        if "Name or service not known" in details or "getaddrinfo failed" in details:
            error_msg = "DNS resolution failed - check hostname"
        # Check for common connection refused errors
        elif "Connection refused" in details:
            error_msg = "Connection refused - check if Sonarr is running and the port is correct"
        
        with open(LOG_FILE, 'a') as f:
            f.write(f"{timestamp} - sonarr - ERROR - {error_msg}: {details}\n")
        return jsonify({"success": False, "message": f"{error_msg}: {details}"}), 502
        
    except requests.exceptions.RequestException as e:
        error_message = f"Connection failed: {str(e)}"
        
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            
            # Add specific messages based on common status codes
            if status_code == 401:
                error_message = "Authentication failed: Invalid API key"
            elif status_code == 403:
                error_message = "Access forbidden: Check API key permissions"
            elif status_code == 404:
                error_message = "API endpoint not found: Check API URL"
            elif status_code >= 500:
                error_message = f"Sonarr server error (HTTP {status_code}): The Sonarr server is experiencing issues"
            
            # Try to extract more error details if available
            try:
                error_details = e.response.json()
                error_message += f" - {error_details.get('message', 'No details')}"
            except ValueError:
                if e.response.text:
                    error_message += f" - Response: {e.response.text[:200]}"
        
        with open(LOG_FILE, 'a') as f:
            f.write(f"{timestamp} - sonarr - ERROR - {error_message}\n")
        return jsonify({"success": False, "message": error_message}), 500
        
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        with open(LOG_FILE, 'a') as f:
            f.write(f"{timestamp} - sonarr - ERROR - {error_msg}\n")
        return jsonify({"success": False, "message": error_msg}), 500

# Function to check if Sonarr is configured
def is_configured():
    """Check if Sonarr API credentials are configured"""
    api_url, api_key = keys_manager.get_api_keys("sonarr")
    return bool(api_url and api_key)
