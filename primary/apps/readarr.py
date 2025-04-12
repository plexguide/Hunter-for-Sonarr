from flask import Blueprint, request, jsonify
import datetime, os, requests
from primary import keys_manager

readarr_bp = Blueprint('readarr', __name__)

LOG_FILE = "/tmp/huntarr-logs/huntarr.log"

@readarr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a Readarr API instance"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')
    if not api_url or not api_key:
        return jsonify({"success": False, "message": "Missing API URL or API key"}), 400

    # For Readarr, use api/v1
    api_base = "api/v1"
    url = f"{api_url}/{api_base}/system/status"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        keys_manager.save_api_keys("readarr", api_url, api_key)

        # Ensure the response is valid JSON
        try:
            response_data = response.json()
        except ValueError:
            return jsonify({"success": False, "message": "Invalid JSON response from Readarr API"}), 500

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, 'a') as f:
            f.write(f"{timestamp} - readarr - INFO - Connection test successful: {api_url}\n")
        return jsonify({"success": True, "data": response_data})
    except requests.exceptions.RequestException as e:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, 'a') as f:
            f.write(f"{timestamp} - readarr - ERROR - Connection test failed: {api_url} - {str(e)}\n")
        return jsonify({"success": False, "message": str(e)}), 500
