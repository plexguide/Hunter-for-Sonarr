from flask import Blueprint, request, jsonify
import datetime, os, requests
from primary import keys_manager
from src.primary.utils.logger import get_logger

readarr_bp = Blueprint('readarr', __name__)
readarr_logger = get_logger("readarr")

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
        readarr_logger.info(f"Testing connection to Readarr API at {api_url}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        keys_manager.save_api_keys("readarr", api_url, api_key)

        # Ensure the response is valid JSON
        try:
            response_data = response.json()
            readarr_logger.info(f"Successfully connected to Readarr API version: {response_data.get('version', 'unknown')}")
            return jsonify({
                "success": True, 
                "message": "Successfully connected to Readarr API",
                "version": response_data.get('version', 'unknown')
            })
        except ValueError:
            error_msg = "Invalid JSON response from Readarr API"
            readarr_logger.error(f"{error_msg}. Response content: {response.text[:200]}")
            return jsonify({"success": False, "message": error_msg}), 500
    except requests.exceptions.RequestException as e:
        error_msg = f"Connection test failed: {str(e)}"
        readarr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500
