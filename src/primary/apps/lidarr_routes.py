#!/usr/bin/env python3

from flask import Blueprint, request, jsonify
import datetime, os, requests
from src.primary import keys_manager
from src.primary.state import get_state_file_path

lidarr_bp = Blueprint('lidarr', __name__)

LOG_FILE = "/tmp/huntarr-logs/huntarr.log"

# Make sure we're using the correct state files
PROCESSED_MISSING_FILE = get_state_file_path("lidarr", "processed_missing") 
PROCESSED_UPGRADES_FILE = get_state_file_path("lidarr", "processed_upgrades")

@lidarr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a Lidarr API instance"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')

    if not api_url or not api_key:
        return jsonify({"success": False, "message": "API URL and API Key are required"}), 400

    headers = {'X-Api-Key': api_key}
    test_url = f"{api_url.rstrip('/')}/api/v1/system/status"

    try:
        response = requests.get(test_url, headers=headers, timeout=10)
        response.raise_for_status()

        # Save keys if connection is successful
        keys_manager.save_api_keys("lidarr", api_url, api_key)

        # Ensure the response is valid JSON
        try:
            response_data = response.json()
        except ValueError:
            return jsonify({"success": False, "message": "Invalid JSON response from Lidarr API"}), 500

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, 'a') as f:
            f.write(f"{timestamp} - lidarr - INFO - Successfully connected to Lidarr API\n")

        return jsonify({"success": True, "message": "Successfully connected to Lidarr API"})

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
