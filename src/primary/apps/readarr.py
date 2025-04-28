from flask import Blueprint, request, jsonify
import datetime, os, requests
from primary import keys_manager
from src.primary.utils.logger import get_logger
from src.primary.state import get_state_file_path
from src.primary.settings_manager import load_settings

readarr_bp = Blueprint('readarr', __name__)
readarr_logger = get_logger("readarr")

# Make sure we're using the correct state files
PROCESSED_MISSING_FILE = get_state_file_path("readarr", "processed_missing") 
PROCESSED_UPGRADES_FILE = get_state_file_path("readarr", "processed_upgrades")

@readarr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a Readarr API instance with comprehensive diagnostics"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')
    api_timeout = data.get('api_timeout', 30)  # Use longer timeout for connection test

    if not api_url or not api_key:
        return jsonify({"success": False, "message": "API URL and API Key are required"}), 400
    
    # Log the test attempt
    readarr_logger.info(f"Testing connection to Readarr API at {api_url}")
    
    # First check if URL is properly formatted
    if not (api_url.startswith('http://') or api_url.startswith('https://')):
        error_msg = "API URL must start with http:// or https://"
        readarr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 400
        
    # For Readarr, use api/v1
    api_base = "api/v1"
    test_url = f"{api_url.rstrip('/')}/{api_base}/system/status"
    headers = {'X-Api-Key': api_key}

    try:
        # Use a connection timeout separate from read timeout
        response = requests.get(test_url, headers=headers, timeout=(10, api_timeout))
        
        # Log HTTP status code for diagnostic purposes
        readarr_logger.debug(f"Readarr API status code: {response.status_code}")
        
        # Check HTTP status code
        response.raise_for_status()

        # Ensure the response is valid JSON
        try:
            response_data = response.json()
            
            # We no longer save keys here since we use instances
            # keys_manager.save_api_keys("readarr", api_url, api_key)
            
            readarr_logger.info(f"Successfully connected to Readarr API version: {response_data.get('version', 'unknown')}")

            # Return success with some useful information
            return jsonify({
                "success": True,
                "message": "Successfully connected to Readarr API",
                "version": response_data.get('version', 'unknown')
            })
        except ValueError:
            error_msg = "Invalid JSON response from Readarr API"
            readarr_logger.error(f"{error_msg}. Response content: {response.text[:200]}")
            return jsonify({"success": False, "message": error_msg}), 500

    except requests.exceptions.Timeout as e:
        error_msg = f"Connection timed out after {api_timeout} seconds"
        readarr_logger.error(f"{error_msg}: {str(e)}")
        return jsonify({"success": False, "message": error_msg}), 504
        
    except requests.exceptions.ConnectionError as e:
        error_msg = "Connection error - check hostname and port"
        details = str(e)
        # Check for common DNS resolution errors
        if "Name or service not known" in details or "getaddrinfo failed" in details:
            error_msg = "DNS resolution failed - check hostname"
        # Check for common connection refused errors
        elif "Connection refused" in details:
            error_msg = "Connection refused - check if Readarr is running and the port is correct"
        
        readarr_logger.error(f"{error_msg}: {details}")
        return jsonify({"success": False, "message": f"{error_msg}: {details}"}), 502
        
    except requests.exceptions.RequestException as e:
        error_message = f"Connection failed: {str(e)}"
        
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            
            # Add specific messages based on common status codes
            if status_code == 401:
                error_message = "Authentication failed: Invalid API key"
            elif status_code == 403:
                error_message = "Access forbidden: Check API key permissions"
            elif status_code == 404:
                error_message = "API endpoint not found: Check API URL"
            elif status_code >= 500:
                error_message = f"Readarr server error (HTTP {status_code}): The Readarr server is experiencing issues"
            
            # Try to extract more error details if available
            try:
                error_details = e.response.json()
                error_message += f" - {error_details.get('message', 'No details')}"
            except ValueError:
                if e.response.text:
                    error_message += f" - Response: {e.response.text[:200]}"
        
        readarr_logger.error(error_message)
        return jsonify({"success": False, "message": error_message}), 500
        
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        readarr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500

# Function to check if Readarr is configured
def is_configured():
    """Check if Readarr API credentials are configured by checking if at least one instance is enabled"""
    settings = load_settings("readarr")
    
    if not settings:
        readarr_logger.debug("No settings found for Readarr")
        return False
        
    # Check if instances are configured
    if "instances" in settings and isinstance(settings["instances"], list) and settings["instances"]:
        for instance in settings["instances"]:
            if instance.get("enabled", True) and instance.get("api_url") and instance.get("api_key"):
                readarr_logger.debug(f"Found configured Readarr instance: {instance.get('name', 'Unnamed')}")
                return True
                
        readarr_logger.debug("No enabled Readarr instances found with valid API URL and key")
        return False
    
    # Fallback to legacy single-instance config
    api_url = settings.get("api_url")
    api_key = settings.get("api_key")
    return bool(api_url and api_key)

# Get all valid instances from settings
def get_configured_instances():
    """Get all configured and enabled Readarr instances"""
    settings = load_settings("readarr")
    instances = []
    
    if not settings:
        readarr_logger.debug("No settings found for Readarr")
        return instances
        
    # Check if instances are configured
    if "instances" in settings and isinstance(settings["instances"], list) and settings["instances"]:
        for instance in settings["instances"]:
            if instance.get("enabled", True) and instance.get("api_url") and instance.get("api_key"):
                # Create a settings object for this instance by combining global settings with instance-specific ones
                instance_settings = settings.copy()
                # Remove instances list to avoid confusion
                if "instances" in instance_settings:
                    del instance_settings["instances"]
                
                # Override with instance-specific connection settings
                instance_settings["api_url"] = instance.get("api_url")
                instance_settings["api_key"] = instance.get("api_key")
                instance_settings["instance_name"] = instance.get("name", "Default")
                
                instances.append(instance_settings)
    else:
        # Fallback to legacy single-instance config
        api_url = settings.get("api_url")
        api_key = settings.get("api_key")
        if api_url and api_key:
            settings["instance_name"] = "Default"
            instances.append(settings)
    
    readarr_logger.info(f"Found {len(instances)} configured and enabled Readarr instances")
    return instances
