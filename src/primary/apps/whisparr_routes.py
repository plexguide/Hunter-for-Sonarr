#!/usr/bin/env python3

from flask import Blueprint, request, jsonify
import datetime, os, requests
from src.primary import keys_manager
from src.primary.state import get_state_file_path
from src.primary.apps.whisparr.api import check_connection

whisparr_bp = Blueprint('whisparr', __name__)

LOG_FILE = "/tmp/huntarr-logs/huntarr.log"

# Make sure we're using the correct state files
PROCESSED_MISSING_FILE = get_state_file_path("whisparr", "processed_missing") 
PROCESSED_UPGRADES_FILE = get_state_file_path("whisparr", "processed_upgrades")

@whisparr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a Whisparr API instance"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')

    if not api_url or not api_key:
        return jsonify({"success": False, "message": "API URL and API Key are required"}), 400

    headers = {'X-Api-Key': api_key}
    test_url = f"{api_url.rstrip('/')}/api/v3/system/status"

    try:
        response = requests.get(test_url, headers=headers, timeout=10)
        response.raise_for_status()

        # Save keys if connection is successful
        keys_manager.save_api_keys("whisparr", api_url, api_key)

        # Ensure the response is valid JSON
        try:
            response_data = response.json()
        except ValueError:
            return jsonify({"success": False, "message": "Invalid JSON response from Whisparr API"}), 500

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, 'a') as f:
            f.write(f"{timestamp} - whisparr - INFO - Successfully connected to Whisparr API\n")

        return jsonify({"success": True, "message": "Successfully connected to Whisparr API"})

    except requests.exceptions.Timeout:
        return jsonify({"success": False, "message": "Connection timed out"}), 504
    except requests.exceptions.RequestException as e:
        error_message = f"Connection failed: {str(e)}"
        if e.response is not None:
            try:
                error_details = e.response.json()
                error_message += f" - {error_details.get('message', 'No details')}"
            except ValueError:
                error_message += f" - Status Code: {e.response.status_code}"
        return jsonify({"success": False, "message": error_message}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"An unexpected error occurred: {str(e)}"}), 500

# Function to check if Whisparr is configured
def is_configured():
    """Check if Whisparr API credentials are configured"""
    api_keys = keys_manager.load_api_keys("whisparr")
    return api_keys.get("api_url") and api_keys.get("api_key")

@whisparr_bp.route('/get-versions', methods=['GET'])
def get_versions():
    """Get the version information from the Whisparr API"""
    api_keys = keys_manager.load_api_keys("whisparr")
    api_url = api_keys.get("api_url")
    api_key = api_keys.get("api_key")

    if not api_url or not api_key:
        return jsonify({"success": False, "message": "Whisparr API is not configured"}), 400

    headers = {'X-Api-Key': api_key}
    version_url = f"{api_url.rstrip('/')}/api/v3/system/status"

    try:
        response = requests.get(version_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        version_data = response.json()
        version = version_data.get("version", "Unknown")
        
        return jsonify({"success": True, "version": version})
    except requests.exceptions.RequestException as e:
        error_message = f"Error fetching Whisparr version: {str(e)}"
        return jsonify({"success": False, "message": error_message}), 500

@whisparr_bp.route('/logs', methods=['GET'])
def get_logs():
    """Get recent log entries for Whisparr from the huntarr log file"""
    try:
        with open(LOG_FILE, 'r') as f:
            log_content = f.readlines()
        
        # Filter log entries related to Whisparr
        whisparr_logs = [line for line in log_content if " - whisparr - " in line]
        
        # Return the most recent 100 log entries
        recent_logs = whisparr_logs[-100:] if len(whisparr_logs) > 100 else whisparr_logs
        
        return jsonify({"success": True, "logs": recent_logs})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error reading log file: {str(e)}"}), 500

@whisparr_bp.route('/clear-processed', methods=['POST'])
def clear_processed():
    """Clear the processed missing and upgrade files for Whisparr"""
    try:
        data = request.json
        if data.get('missing'):
            with open(PROCESSED_MISSING_FILE, 'w') as f:
                f.write('[]')
        
        if data.get('upgrades'):
            with open(PROCESSED_UPGRADES_FILE, 'w') as f:
                f.write('[]')
        
        return jsonify({"success": True, "message": "Processed files cleared successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error clearing processed files: {str(e)}"}), 500