from flask import Blueprint, request, jsonify
import datetime, os, requests
from primary import keys_manager
from src.primary.utils.logger import get_logger

radarr_bp = Blueprint('radarr', __name__)
radarr_logger = get_logger("radarr")

@radarr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a Radarr API instance"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')
    if not api_url or not api_key:
        return jsonify({"success": False, "message": "Missing API URL or API key"}), 400

    # For Radarr, use api/v3
    api_base = "api/v3"
    url = f"{api_url}/{api_base}/system/status"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    try:
        radarr_logger.info(f"Testing connection to Radarr API at {api_url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        keys_manager.save_api_keys("radarr", api_url, api_key)

        # Ensure the response is valid JSON
        try:
            response_data = response.json()
            radarr_logger.info(f"Successfully connected to Radarr API version: {response_data.get('version', 'unknown')}")
            return jsonify({
                "success": True, 
                "message": "Successfully connected to Radarr API",
                "version": response_data.get('version', 'unknown')
            })
        except ValueError:
            error_msg = "Invalid JSON response from Radarr API"
            radarr_logger.error(f"{error_msg}. Response content: {response.text[:200]}")
            return jsonify({"success": False, "message": error_msg}), 500
    except requests.exceptions.RequestException as e:
        error_msg = f"Connection test failed: {str(e)}"
        radarr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500
