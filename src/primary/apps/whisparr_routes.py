#!/usr/bin/env python3

from flask import Blueprint, request, jsonify
import datetime, os, requests
from src.primary import keys_manager
from src.primary.state import get_state_file_path, reset_state_file
from src.primary.utils.logger import get_logger, APP_LOG_FILES
import traceback

whisparr_bp = Blueprint('whisparr', __name__)
whisparr_logger = get_logger("whisparr")

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
        
    whisparr_logger.info(f"Testing connection to Whisparr API at {api_url}")
    
    # For Whisparr, use api/v3
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
            whisparr_logger.info(f"Successfully connected to Whisparr API version: {version}")
            
            return jsonify({
                "success": True,
                "message": "Successfully connected to Whisparr API",
                "version": version
            })
        except ValueError:
            error_msg = "Invalid JSON response from Whisparr API"
            whisparr_logger.error(f"{error_msg}. Response content: {response.text[:200]}")
            return jsonify({"success": False, "message": error_msg}), 500
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Connection test failed: {str(e)}"
        whisparr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500

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
    """Get recent log entries for Whisparr from the whisparr log file"""
    try:
        log_file = APP_LOG_FILES.get('whisparr')
        if not log_file or not os.path.exists(log_file):
            return jsonify({"success": False, "message": "Whisparr log file not found"}), 404
            
        with open(log_file, 'r') as f:
            log_content = f.readlines()
        
        # Return the most recent 100 log entries
        recent_logs = log_content[-100:] if len(log_content) > 100 else log_content
        
        return jsonify({"success": True, "logs": recent_logs})
    except Exception as e:
        whisparr_logger.error(f"Error reading log file: {str(e)}")
        return jsonify({"success": False, "message": f"Error reading log file: {str(e)}"}), 500

@whisparr_bp.route('/clear-processed', methods=['POST'])
def clear_processed():
    """Clear the processed missing and upgrade files for Whisparr"""
    try:
        data = request.json
        if data.get('missing'):
            reset_state_file("whisparr", "processed_missing")
            whisparr_logger.info("Reset Whisparr missing state")
        
        if data.get('upgrades'):
            reset_state_file("whisparr", "processed_upgrades")
            whisparr_logger.info("Reset Whisparr upgrades state")
        
        return jsonify({"success": True, "message": "Processed files cleared successfully"})
    except Exception as e:
        error_msg = f"Error clearing processed files: {str(e)}"
        whisparr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500