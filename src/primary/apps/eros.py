from flask import Blueprint, request, jsonify
import datetime, os, requests
from primary import keys_manager
from src.primary.utils.logger import get_logger
from src.primary.state import get_state_file_path
from src.primary.settings_manager import load_settings, settings_manager, get_ssl_verify_setting

eros_bp = Blueprint('eros', __name__)
eros_logger = get_logger("eros")

# Make sure we're using the correct state files
PROCESSED_MISSING_FILE = get_state_file_path("eros", "processed_missing") 
PROCESSED_UPGRADES_FILE = get_state_file_path("eros", "processed_upgrades")

@eros_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to Eros API instance with comprehensive diagnostics"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')
    api_timeout = data.get('api_timeout', 30)  # Use longer timeout for connection test

    if not api_url or not api_key:
        return jsonify({"success": False, "message": "API URL and API Key are required"}), 400
    
    # Log the test attempt
    eros_logger.info(f"Testing connection to Eros API at {api_url}")
    
    # Auto-correct URL if missing http(s) scheme
    if not (api_url.startswith('http://') or api_url.startswith('https://')):
        eros_logger.warning(f"API URL missing http(s) scheme: {api_url}")
        api_url = f"http://{api_url}"
        eros_logger.warning(f"Auto-correcting URL to: {api_url}")
        
    # Create the test URL and set headers
    test_url = f"{api_url.rstrip('/')}/api/v3/system/status"
    headers = {'X-Api-Key': api_key}
    
    # Get SSL verification setting
    verify_ssl = get_ssl_verify_setting()
    
    if not verify_ssl:
        eros_logger.debug("SSL verification disabled by user setting for connection test")

    try:
        # Use a connection timeout separate from read timeout
        response = requests.get(test_url, headers=headers, timeout=(10, api_timeout), verify=verify_ssl)
        
        # Log HTTP status code for diagnostic purposes
        eros_logger.debug(f"Eros API status code: {response.status_code}")
        
        # Check HTTP status code
        if response.status_code == 404:
            # Try next path if 404
            return jsonify({"success": False, "message": "API path not found"}), 404
            
        response.raise_for_status()
    
        # Ensure the response is valid JSON
        try:
            response_data = response.json()
            eros_logger.debug(f"Eros API response: {response_data}")
            
            # Verify this is actually an Eros API by checking for version
            version = response_data.get('version', None)
            if not version:
                # No version info, try next path
                return jsonify({"success": False, "message": "API response doesn't contain version information"}), 400
            
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
                # Connected to some other version, try next path
                return jsonify({"success": False, "message": f"Connected to unknown version {version}, but Huntarr requires Eros V3"}), 400
                
        except ValueError:
            return jsonify({"success": False, "message": "Invalid JSON response from API"}), 400
            
    except requests.exceptions.Timeout:
        return jsonify({"success": False, "message": "Connection timed out after 10 seconds"}), 408
        
    except requests.exceptions.ConnectionError:
        return jsonify({"success": False, "message": "Failed to connect. Check that the URL is correct and that Eros is running."}), 503
        
    except requests.exceptions.HTTPError as e:
        return jsonify({"success": False, "message": f"HTTP error: {str(e)}"}), 500
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Unexpected error: {str(e)}"}), 500

# Function to check if Eros is configured
def is_configured():
    """Check if Eros API credentials are configured"""
    try:
        settings = load_settings("eros")
        instances = settings.get("instances", [])
        
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
        settings = load_settings("eros")
        instances = settings.get("instances", [])
        
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
