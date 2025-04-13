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

def get_main_process_pid():
    # ...existing logic...
    try:
        for proc in os.listdir('/proc'):
            if not proc.isdigit():
                continue
            try:
                with open(f'/proc/{proc}/cmdline', 'r') as f:
                    cmdline = f.read().replace('\0', ' ')
                    if 'python' in cmdline and 'primary/main.py' in cmdline:
                        return int(proc)
            except (IOError, ProcessLookupError):
                continue
        return None
    except:
        return None

@sonarr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a Sonarr API instance"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')
    if not api_url or not api_key:
        return jsonify({"success": False, "message": "Missing API URL or API key"}), 400

    # For Sonarr, use api/v3
    api_base = "api/v3"
    url = f"{api_url}/{api_base}/system/status"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Log the connection attempt
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, 'a') as f:
        f.write(f"{timestamp} - sonarr - INFO - Testing connection to: {api_url}\n")
    
    try:
        # This is similar to: curl -H "X-Api-Key: api-key" http://ip-address/api/v3/system/status
        response = requests.get(url, headers=headers, timeout=10)
        
        # Check status code explicitly
        if response.status_code == 401:
            with open(LOG_FILE, 'a') as f:
                f.write(f"{timestamp} - sonarr - ERROR - Connection test failed: 401 Unauthorized - Invalid API key\n")
            return jsonify({"success": False, "message": "Unauthorized - Invalid API key"}), 401
        
        response.raise_for_status()
        
        # Test if response is valid JSON
        try:
            response_data = response.json()
            
            # Save the API keys only if connection test is successful
            keys_manager.save_api_keys("sonarr", api_url, api_key)
            
            with open(LOG_FILE, 'a') as f:
                f.write(f"{timestamp} - sonarr - INFO - Connection test successful: {api_url}\n")
                
            return jsonify({
                "success": True, 
                "message": "Successfully connected to Sonarr API",
                "data": response_data
            })
            
        except ValueError:
            with open(LOG_FILE, 'a') as f:
                f.write(f"{timestamp} - sonarr - ERROR - Invalid JSON response from Sonarr API\n")
            return jsonify({"success": False, "message": "Invalid JSON response from Sonarr API"}), 500
            
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        with open(LOG_FILE, 'a') as f:
            f.write(f"{timestamp} - sonarr - ERROR - Connection test failed: {api_url} - {error_message}\n")
            
        # Provide more specific error messages for common issues
        if "NewConnectionError" in error_message or "ConnectionError" in error_message:
            return jsonify({"success": False, "message": f"Cannot connect to Sonarr at {api_url} - Check if the service is running and URL is correct"}), 500
        elif "Timeout" in error_message:
            return jsonify({"success": False, "message": "Connection timed out - Sonarr is taking too long to respond"}), 500
        else:
            return jsonify({"success": False, "message": error_message}), 500

# Function to check if Sonarr is configured
def is_configured():
    """Check if Sonarr API credentials are configured"""
    api_url, api_key = keys_manager.get_api_keys("sonarr")
    return bool(api_url and api_key)

# Main entry point for Sonarr functionality
def start():
    """Main entry point for Sonarr-related functionality"""
    # Perform any Sonarr-specific initialization here
    pass
