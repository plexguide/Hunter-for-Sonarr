from flask import Blueprint, request, jsonify
import datetime, os, requests
from src.primary import keys_manager
from src.primary.utils.logger import get_logger
from src.primary.state import get_state_file_path
from src.primary.settings_manager import load_settings, get_ssl_verify_setting
from src.primary.apps.radarr.api import arr_request

radarr_bp = Blueprint('radarr', __name__)
radarr_logger = get_logger("radarr")

# Make sure we're using the correct state files
PROCESSED_MISSING_FILE = get_state_file_path("radarr", "processed_missing") 
PROCESSED_UPGRADES_FILE = get_state_file_path("radarr", "processed_upgrades")

@radarr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a Radarr API instance with comprehensive diagnostics"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')
    api_timeout = data.get('api_timeout', 30)  # Use longer timeout for connection test

    if not api_url or not api_key:
        return jsonify({"success": False, "message": "API URL and API Key are required"}), 400
    
    radarr_logger.info(f"Testing connection to Radarr API at {api_url}")
    
    if not (api_url.startswith('http://') or api_url.startswith('https://')):
        error_msg = "API URL must start with http:// or https://"
        radarr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 400
    
    verify_ssl = get_ssl_verify_setting()
    if not verify_ssl:
        radarr_logger.debug("SSL verification disabled by user setting for connection test")

    try:
        response_data = arr_request(api_url, api_key, api_timeout, "system/status", verify_ssl=verify_ssl)
        if not response_data:
            error_msg = "No response or invalid response from Radarr API"
            radarr_logger.error(error_msg)
            return jsonify({"success": False, "message": error_msg}), 500
        radarr_logger.info(f"Successfully connected to Radarr API version: {response_data.get('version', 'unknown')}")
        return jsonify({
            "success": True,
            "message": "Successfully connected to Radarr API",
            "version": response_data.get('version', 'unknown')
        })
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        radarr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500

# Function to check if Radarr is configured
def is_configured():
    """Check if Radarr API credentials are configured by checking if at least one instance is enabled"""
    settings = load_settings("radarr")
    
    if not settings:
        radarr_logger.debug("No settings found for Radarr")
        return False
        
    # Check if instances are configured
    if "instances" in settings and isinstance(settings["instances"], list) and settings["instances"]:
        for instance in settings["instances"]:
            if instance.get("enabled", True) and instance.get("api_url") and instance.get("api_key"):
                radarr_logger.debug(f"Found configured Radarr instance: {instance.get('name', 'Unnamed')}")
                return True
                
        radarr_logger.debug("No enabled Radarr instances found with valid API URL and key")
        return False
    
    # Fallback to legacy single-instance config
    api_url = settings.get("api_url")
    api_key = settings.get("api_key")
    return bool(api_url and api_key)

# Get all valid instances from settings
# get_configured_instances function has been moved to src/primary/apps/radarr/__init__.py

# Function to reset the processed IDs files
