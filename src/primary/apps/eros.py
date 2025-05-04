from flask import Blueprint, request, jsonify
import datetime, os, requests
from primary import keys_manager
from src.primary.utils.logger import get_logger
from src.primary.state import get_state_file_path
from src.primary.settings_manager import load_settings

eros_bp = Blueprint('eros', __name__)
eros_logger = get_logger("eros")

# Make sure we're using the correct state files
PROCESSED_MISSING_FILE = get_state_file_path("eros", "processed_missing") 
PROCESSED_UPGRADES_FILE = get_state_file_path("eros", "processed_upgrades")

@eros_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to an Eros API instance with comprehensive diagnostics"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')
    api_timeout = data.get('api_timeout', 30)  # Use longer timeout for connection test

    if not api_url or not api_key:
        return jsonify({"success": False, "message": "API URL and API Key are required"}), 400
    
    # Log the test attempt
    eros_logger.info(f"Testing connection to Eros API at {api_url}")
    
    # First check if URL is properly formatted
    if not (api_url.startswith('http://') or api_url.startswith('https://')):
        error_msg = "API URL must start with http:// or https://"
        eros_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 400
        
    # For Eros, we always use /api/v3 path
    test_url = f"{api_url.rstrip('/')}/api/v3/system/status"
    headers = {'X-Api-Key': api_key}
    
    try:
        # Use a connection timeout separate from read timeout
        response = requests.get(test_url, headers=headers, timeout=(10, api_timeout))
        
        # Log HTTP status code for diagnostic purposes
        eros_logger.debug(f"Eros API status code: {response.status_code}")
        
        # Check HTTP status code
        response.raise_for_status()

        # Ensure the response is valid JSON
        try:
            response_data = response.json()
            eros_logger.debug(f"Eros API response: {response_data}")
            
            # Verify this is actually an Eros API by checking for version
            version = response_data.get('version', None)
            if not version:
                error_msg = "API response doesn't contain version information, may not be Eros"
                eros_logger.error(error_msg)
                return jsonify({"success": False, "message": error_msg}), 400
            
            # The version number should start with 3 for Eros
            if version.startswith('3'):
                eros_logger.info(f"Successfully connected to Eros API version {version}")
                return jsonify({
                    "success": True, 
                    "message": f"Successfully connected to Eros (version {version})",
                    "version": version
                })
            elif version.startswith('2'):
                error_msg = f"Connected to Whisparr V2 (version {version}). Use the Whisparr integration for V2."
                eros_logger.error(error_msg)
                return jsonify({"success": False, "message": error_msg}), 400
            else:
                # Connected to some other version
                error_msg = f"Connected to unknown version {version}, but Huntarr requires Eros V3"
                eros_logger.error(error_msg)
                return jsonify({"success": False, "message": error_msg}), 400
                
        except ValueError:
            error_msg = "Invalid JSON response from API. Are you sure this is an Eros API?"
            eros_logger.error(f"{error_msg}. Response: {response.text[:200]}")
            return jsonify({"success": False, "message": error_msg}), 400
            
    except requests.exceptions.Timeout:
        error_msg = f"Connection timed out after {api_timeout} seconds. Check that Eros is running and accessible."
        eros_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 408
        
    except requests.exceptions.ConnectionError:
        error_msg = "Failed to connect. Check that the URL is correct and that Eros is running."
        eros_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 502
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            error_msg = "API key invalid or unauthorized"
        elif response.status_code == 404:
            error_msg = "API endpoint not found. Check that the URL is correct."
        else:
            error_msg = f"HTTP error: {str(e)}"
        eros_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), response.status_code
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        eros_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500

# Function to check if Eros is configured
def is_configured():
    """Check if Eros API credentials are configured"""
    try:
        api_keys = keys_manager.load_api_keys("eros")
        instances = api_keys.get("instances", [])
        
        for instance in instances:
            if instance.get("enabled", True):
                return True
                
        return False
    except Exception as e:
        eros_logger.error(f"Error checking if Eros is configured: {str(e)}")
        return False

# Get all valid instances from settings
def get_configured_instances():
    """Get all configured and enabled Eros instances"""
    try:
        api_keys = keys_manager.load_api_keys("eros")
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
        eros_logger.error(f"Error getting configured Eros instances: {str(e)}")
        return []
