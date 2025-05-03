from flask import Blueprint, request, jsonify
import datetime, os, requests
from primary import keys_manager
from src.primary.utils.logger import get_logger
from src.primary.state import get_state_file_path
from src.primary.settings_manager import load_settings

whisparr_bp = Blueprint('whisparr', __name__)
whisparr_logger = get_logger("whisparr")

# Make sure we're using the correct state files
PROCESSED_MISSING_FILE = get_state_file_path("whisparr", "processed_missing") 
PROCESSED_UPGRADES_FILE = get_state_file_path("whisparr", "processed_upgrades")

@whisparr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a Whisparr API instance with comprehensive diagnostics"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')
    api_timeout = data.get('api_timeout', 30)  # Use longer timeout for connection test

    if not api_url or not api_key:
        return jsonify({"success": False, "message": "API URL and API Key are required"}), 400
    
    # Log the test attempt
    whisparr_logger.info(f"Testing connection to Whisparr V2 API at {api_url}")
    
    # First check if URL is properly formatted
    if not (api_url.startswith('http://') or api_url.startswith('https://')):
        error_msg = "API URL must start with http:// or https://"
        whisparr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 400
        
    # For Whisparr V2, we can try both with and without /api/v3 path
    # First try with direct API access
    test_url = f"{api_url.rstrip('/')}/api/system/status"
    headers = {'X-Api-Key': api_key}
    
    try:
        # Use a connection timeout separate from read timeout
        response = requests.get(test_url, headers=headers, timeout=(10, api_timeout))
        
        # Log HTTP status code for diagnostic purposes
        whisparr_logger.debug(f"Whisparr API status code: {response.status_code}")
        
        # If we get a 404, try with /api/v3 path since Whisparr V2 might be using API V3 format
        if response.status_code == 404:
            test_url = f"{api_url.rstrip('/')}/api/v3/system/status"
            whisparr_logger.debug(f"First attempt failed, trying alternate API path: {test_url}")
            response = requests.get(test_url, headers=headers, timeout=(10, api_timeout))
            whisparr_logger.debug(f"Whisparr API V3 status code: {response.status_code}")
        
        # Check HTTP status code
        response.raise_for_status()

        # Ensure the response is valid JSON
        try:
            response_data = response.json()
            whisparr_logger.debug(f"Whisparr API response: {response_data}")
            
            # Verify this is actually a Whisparr API by checking for version
            version = response_data.get('version', None)
            if not version:
                error_msg = "API response doesn't contain version information, may not be Whisparr"
                whisparr_logger.error(error_msg)
                return jsonify({"success": False, "message": error_msg}), 400
            
            # Accept both V2 and V3 API formats for Whisparr V2
            # The version number should still start with 2 for Whisparr V2, even if using API V3
            if version.startswith('2'):
                whisparr_logger.info(f"Successfully connected to Whisparr V2 API version {version}")
                return jsonify({
                    "success": True, 
                    "message": f"Successfully connected to Whisparr V2 (version {version})",
                    "version": version
                })
            elif version.startswith('3'):
                error_msg = f"Connected to Whisparr Eros (version {version}). Huntarr requires Whisparr V2."
                whisparr_logger.error(error_msg)
                return jsonify({"success": False, "message": error_msg}), 400
            else:
                # Connected to some other version
                error_msg = f"Connected to Whisparr version {version}, but Huntarr requires Whisparr V2"
                whisparr_logger.error(error_msg)
                return jsonify({"success": False, "message": error_msg}), 400
                
        except ValueError:
            error_msg = "Invalid JSON response from API. Are you sure this is a Whisparr API?"
            whisparr_logger.error(f"{error_msg}. Response: {response.text[:200]}")
            return jsonify({"success": False, "message": error_msg}), 400
            
    except requests.exceptions.Timeout:
        error_msg = f"Connection timed out after {api_timeout} seconds. Check that Whisparr is running and accessible."
        whisparr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 408
        
    except requests.exceptions.ConnectionError:
        error_msg = "Failed to connect. Check that the URL is correct and that Whisparr is running."
        whisparr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 502
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            error_msg = "API key invalid or unauthorized"
        elif response.status_code == 404:
            error_msg = "API endpoint not found. Check that the URL is correct."
        else:
            error_msg = f"HTTP error: {str(e)}"
        whisparr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), response.status_code
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        whisparr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500

# Function to check if Whisparr is configured
def is_configured():
    """Check if Whisparr API credentials are configured"""
    try:
        api_keys = keys_manager.load_api_keys("whisparr")
        instances = api_keys.get("instances", [])
        
        for instance in instances:
            if instance.get("enabled", True):
                return True
                
        return False
    except Exception as e:
        whisparr_logger.error(f"Error checking if Whisparr is configured: {str(e)}")
        return False

# Get all valid instances from settings
def get_configured_instances():
    """Get all configured and enabled Whisparr instances"""
    try:
        api_keys = keys_manager.load_api_keys("whisparr")
        instances = api_keys.get("instances", [])
        
        enabled_instances = []
        for instance in instances:
            if not instance.get("enabled", True):
                continue
                
            api_url = instance.get("api_url")
            api_key = instance.get("api_key")
            
            if not api_url or not api_key:
                continue
                
            # Add name and timeout
            instance_name = instance.get("name", "Default")
            api_timeout = instance.get("api_timeout", 90)
            
            enabled_instances.append({
                "api_url": api_url,
                "api_key": api_key,
                "instance_name": instance_name,
                "api_timeout": api_timeout
            })
            
        return enabled_instances
    except Exception as e:
        whisparr_logger.error(f"Error getting configured Whisparr instances: {str(e)}")
        return []