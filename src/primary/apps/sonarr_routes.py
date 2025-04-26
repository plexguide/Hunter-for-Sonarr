#!/usr/bin/env python3

from flask import Blueprint, request, jsonify
import datetime, os, requests
from src.primary import keys_manager
from src.primary.state import get_state_file_path, reset_state_file
from src.primary.utils.logger import get_logger
import traceback

sonarr_bp = Blueprint('sonarr', __name__)
sonarr_logger = get_logger("sonarr")

# Make sure we're using the correct state files
PROCESSED_MISSING_FILE = get_state_file_path("sonarr", "processed_missing") 
PROCESSED_UPGRADES_FILE = get_state_file_path("sonarr", "processed_upgrades")

@sonarr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a Sonarr API instance"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')
    
    if not api_url or not api_key:
        return jsonify({"success": False, "message": "API URL and API Key are required"}), 400
        
    sonarr_logger.info(f"Testing connection to Sonarr API at {api_url}")
    
    # For Sonarr, use api/v3
    url = f"{api_url}/api/v3/system/status"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        try:
            response_data = response.json()
            version = response_data.get('version', 'unknown')
            sonarr_logger.info(f"Successfully connected to Sonarr API version: {version}")
            
            return jsonify({
                "success": True,
                "message": "Successfully connected to Sonarr API",
                "version": version
            })
        except ValueError:
            error_msg = "Invalid JSON response from Sonarr API"
            sonarr_logger.error(f"{error_msg}. Response content: {response.text[:200]}")
            return jsonify({"success": False, "message": error_msg}), 500
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Connection test failed: {str(e)}"
        sonarr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500
