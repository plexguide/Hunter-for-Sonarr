from flask import Blueprint, request, jsonify
import datetime, os, requests
from primary import keys_manager
from src.primary.utils.logger import get_logger
from src.primary.state import get_state_file_path
from src.primary.settings_manager import load_settings, settings_manager

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
        
    # Try multiple API path combinations to handle different Whisparr V3/Eros setups
    api_paths = [
        "/api/v3/system/status",  # Standard V3 path
        "/api/system/status",     # Standard V2 path that might still work
        "/system/status"          # Direct path without /api prefix
    ]
    
    success = False
    last_error = None
    response_data = None
    
    for api_path in api_paths:
        test_url = f"{api_url.rstrip('/')}{api_path}"
        headers = {'X-Api-Key': api_key}
        eros_logger.debug(f"Trying Eros API path: {test_url}")
        
        try:
            # Use a connection timeout separate from read timeout
            response = requests.get(test_url, headers=headers, timeout=(10, api_timeout))
            
            # Log HTTP status code for diagnostic purposes
            eros_logger.debug(f"Eros API status code: {response.status_code} for path {api_path}")
            
            # Check HTTP status code
            if response.status_code == 404:
                # Try next path if 404
                continue
                
            response.raise_for_status()
    
            # Ensure the response is valid JSON
            try:
                response_data = response.json()
                eros_logger.debug(f"Eros API response: {response_data}")
                
                # Verify this is actually an Eros API by checking for version
                version = response_data.get('version', None)
                if not version:
                    # No version info, try next path
                    last_error = "API response doesn't contain version information"
                    continue
                
                # The version number should start with 3 for Eros
                if version.startswith('3'):
                    eros_logger.info(f"Successfully connected to Eros API version {version} using path {api_path}")
                    success = True
                    break
                elif version.startswith('2'):
                    error_msg = f"Connected to Whisparr V2 (version {version}). Use the Whisparr integration for V2."
                    eros_logger.error(error_msg)
                    return jsonify({"success": False, "message": error_msg}), 400
                else:
                    # Connected to some other version, try next path
                    last_error = f"Connected to unknown version {version}, but Huntarr requires Eros V3"
                    continue
                    
            except ValueError:
                last_error = "Invalid JSON response from API"
                continue
                
        except requests.exceptions.Timeout:
            last_error = f"Connection timed out after {api_timeout} seconds"
            continue
            
        except requests.exceptions.ConnectionError:
            last_error = "Failed to connect. Check that the URL is correct and that Eros is running."
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
            "message": f"Successfully connected to Eros (version {response_data.get('version')})",
            "version": response_data.get('version')
        })
    else:
        error_msg = last_error or "Failed to connect to Eros API. Please check your URL and API key."
        eros_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 400

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
