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
    """Get the log file for Whisparr"""
    try:
        # Get the log file path
        log_file = APP_LOG_FILES.get("whisparr")
        
        if not log_file or not os.path.exists(log_file):
            return jsonify({"success": False, "message": "Log file not found"}), 404
            
        # Read the log file (last 200 lines)
        with open(log_file, 'r') as f:
            lines = f.readlines()
            log_content = ''.join(lines[-200:])
            
        return jsonify({"success": True, "logs": log_content})
    except Exception as e:
        error_message = f"Error fetching Whisparr logs: {str(e)}"
        whisparr_logger.error(error_message)
        traceback.print_exc()
        return jsonify({"success": False, "message": error_message}), 500

@whisparr_bp.route('/clear-processed', methods=['POST'])
def clear_processed():
    """Clear the processed missing and upgrade files for Whisparr"""
    try:
        # Reset missing items state file
        whisparr_logger.info("Clearing processed missing items state")
        reset_state_file("whisparr", "processed_missing")
        
        # Reset upgrade state file
        whisparr_logger.info("Clearing processed quality upgrade state")
        reset_state_file("whisparr", "processed_upgrades")
        
        return jsonify({
            "success": True,
            "message": "Successfully cleared Whisparr processed state"
        })
    except Exception as e:
        error_message = f"Error clearing Whisparr processed state: {str(e)}"
        whisparr_logger.error(error_message)
        return jsonify({"success": False, "message": error_message}), 500