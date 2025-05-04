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
        
    # Try multiple API path combinations to handle different Whisparr V2 setups
    api_paths = [
        "/api/system/status",     # Standard V2 path
        "/api/v3/system/status",  # Some V2 instances use V3 API
        "/system/status"          # Direct path without /api prefix
    ]
    
    success = False
    last_error = None
    response_data = None
    
    for api_path in api_paths:
        test_url = f"{api_url.rstrip('/')}{api_path}"
        headers = {'X-Api-Key': api_key}
        whisparr_logger.debug(f"Trying Whisparr API path: {test_url}")
        
        try:
            # Use a connection timeout separate from read timeout
            response = requests.get(test_url, headers=headers, timeout=(10, api_timeout))
            
            # Log HTTP status code for diagnostic purposes
            whisparr_logger.debug(f"Whisparr API status code: {response.status_code} for path {api_path}")
            
            # Check HTTP status code
            if response.status_code == 404:
                # Try next path if 404
                continue
                
            response.raise_for_status()
    
            # Ensure the response is valid JSON
            try:
                response_data = response.json()
                whisparr_logger.debug(f"Whisparr API response: {response_data}")
                
                # Verify this is actually a Whisparr API by checking for version
                version = response_data.get('version', None)
                if not version:
                    # No version info, try next path
                    last_error = "API response doesn't contain version information"
                    continue
                
                # The version number should start with 2 for Whisparr
                if version.startswith('2'):
                    whisparr_logger.info(f"Successfully connected to Whisparr V2 API version {version} using path {api_path}")
                    success = True
                    break
                elif version.startswith('3'):
                    error_msg = f"Connected to Whisparr V3 (version {version}). Use the Eros integration for V3."
                    whisparr_logger.error(error_msg)
                    return jsonify({"success": False, "message": error_msg}), 400
                else:
                    # Connected to some other version, try next path
                    last_error = f"Connected to unknown version {version}, but Huntarr requires Whisparr V2"
                    continue
                    
            except ValueError:
                last_error = "Invalid JSON response from API"
                continue
                
        except requests.exceptions.Timeout:
            last_error = f"Connection timed out after {api_timeout} seconds"
            continue
            
        except requests.exceptions.ConnectionError:
            last_error = "Failed to connect. Check that the URL is correct and that Whisparr is running."
            continue
            
        except requests.exceptions.HTTPError as e:
            last_error = f"HTTP error: {str(e)}"
            continue
            
        except Exception as e:
            last_error = f"Unexpected error: {str(e)}"
            continue
    
    # After trying all paths
    if success:
        return jsonify({
            "success": True, 
            "message": f"Successfully connected to Whisparr V2 (version {response_data.get('version')})",
            "version": response_data.get('version')
        })
    else:
        error_msg = last_error or "Failed to connect to Whisparr API. Please check your URL and API key."
        whisparr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 400

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