#!/usr/bin/env python3

from flask import Blueprint, request, jsonify
import datetime, os, requests
from src.primary import settings_manager
from src.primary.state import get_state_file_path

readarr_bp = Blueprint('readarr', __name__)

LOG_FILE = "/tmp/huntarr-logs/huntarr.log"

# Make sure we're using the correct state files
PROCESSED_MISSING_FILE = get_state_file_path("readarr", "processed_missing") 
PROCESSED_UPGRADES_FILE = get_state_file_path("readarr", "processed_upgrades")

@readarr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a Readarr API instance"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')

    if not api_url or not api_key:
        return jsonify({"success": False, "message": "API URL and API Key are required"}), 400

    headers = {'X-Api-Key': api_key}
    test_url = f"{api_url.rstrip('/')}/api/v1/system/status"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # This is similar to: curl -H "X-Api-Key: api-key" http://ip-address/api/v1/system/status
        response = requests.get(test_url, headers=headers, timeout=10)
        
        # Check status code explicitly
        if response.status_code == 401:
            with open(LOG_FILE, 'a') as f:
                f.write(f"{timestamp} - readarr - ERROR - Connection test failed: 401 Unauthorized - Invalid API key\n")
            return jsonify({"success": False, "message": "Unauthorized - Invalid API key"}), 401
        
        response.raise_for_status()
        
        # Test if response is valid JSON
        try:
            response_data = response.json()
            
            # Save the API keys only if connection test is successful
            settings_manager.save_setting("readarr", "api_url", api_url)
            settings_manager.save_setting("readarr", "api_key", api_key)
            
            with open(LOG_FILE, 'a') as f:
                f.write(f"{timestamp} - readarr - INFO - Connection test successful: {api_url}\n")
                
            return jsonify({
                "success": True, 
                "message": "Successfully connected to Readarr API",
                "data": response_data
            })
            
        except ValueError:
            with open(LOG_FILE, 'a') as f:
                f.write(f"{timestamp} - readarr - ERROR - Invalid JSON response from Readarr API\n")
            return jsonify({"success": False, "message": "Invalid JSON response from Readarr API"}), 500
            
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        with open(LOG_FILE, 'a') as f:
            f.write(f"{timestamp} - readarr - ERROR - Connection test failed: {api_url} - {error_message}\n")
        
        # Provide more specific error messages for common issues
        if "NewConnectionError" in error_message or "ConnectionError" in error_message:
            return jsonify({"success": False, "message": f"Cannot connect to Readarr at {api_url} - Check if the service is running and URL is correct"}), 500
        elif "Timeout" in error_message:
            return jsonify({"success": False, "message": "Connection timed out - Readarr is taking too long to respond"}), 500
        else:
            return jsonify({"success": False, "message": error_message}), 500
