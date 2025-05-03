#!/usr/bin/env python3

from flask import Blueprint, request, jsonify
import datetime, os, requests
from src.primary import keys_manager
from src.primary.state import get_state_file_path, reset_state_file
from src.primary.utils.logger import get_logger, APP_LOG_FILES
import traceback
from src.primary.apps.whisparr import api as whisparr_api

whisparr_bp = Blueprint('whisparr', __name__)
whisparr_logger = get_logger("whisparr")

# Make sure we're using the correct state files
PROCESSED_MISSING_FILE = get_state_file_path("whisparr", "processed_missing") 
PROCESSED_UPGRADES_FILE = get_state_file_path("whisparr", "processed_upgrades")

@whisparr_bp.route('/status', methods=['GET'])
def get_status():
    """Get the status of all configured Whisparr instances"""
    try:
        # Get all configured instances
        api_keys = keys_manager.load_api_keys("whisparr")
        instances = api_keys.get("instances", [])
        
        connected_count = 0
        total_configured = len(instances)
        
        for instance in instances:
            api_url = instance.get("api_url")
            api_key = instance.get("api_key")
            if api_url and api_key and instance.get("enabled", True):
                # Use a short timeout for status checks
                if whisparr_api.check_connection(api_url, api_key, 5):
                    connected_count += 1
        
        return jsonify({
            "configured": total_configured > 0,
            "connected": connected_count > 0,
            "connected_count": connected_count,
            "total_configured": total_configured
        })
    except Exception as e:
        whisparr_logger.error(f"Error getting Whisparr status: {str(e)}")
        return jsonify({
            "configured": False,
            "connected": False,
            "error": str(e)
        }), 500

@whisparr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a Whisparr API instance"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')
    
    if not api_url or not api_key:
        return jsonify({"success": False, "message": "API URL and API Key are required"}), 400
        
    whisparr_logger.info(f"Testing connection to Whisparr V2 API at {api_url}")
    
    # First try the standard API endpoint
    url = f"{api_url.rstrip('/')}/api/system/status"
    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        # If we get a 404, try with the v3 path format
        if response.status_code == 404:
            whisparr_logger.debug("Standard API path returned 404, trying V3 path format")
            v3_url = f"{api_url.rstrip('/')}/api/v3/system/status"
            response = requests.get(v3_url, headers=headers, timeout=10)
            whisparr_logger.debug(f"V3 path request returned status code: {response.status_code}")
        
        # Direct request to V2 API
        if response.status_code == 200:
            try:
                response_data = response.json()
                version = response_data.get('version', 'unknown')
                
                # Make sure it's a version 2.x
                if version and version.startswith('2'):
                    whisparr_logger.info(f"Successfully connected to Whisparr V2 API version: {version}")
                    return jsonify({
                        "success": True,
                        "message": f"Successfully connected to Whisparr V2 API (version {version})",
                        "version": version,
                        "is_v2": True
                    })
                elif version and version.startswith('3'):
                    # Detected Eros API (V3)
                    error_msg = f"Incompatible Whisparr version {version} detected. Huntarr requires Whisparr V2."
                    whisparr_logger.error(error_msg)
                    return jsonify({"success": False, "message": error_msg}), 400
                else:
                    error_msg = f"Unexpected Whisparr version {version} detected. Huntarr requires Whisparr V2."
                    whisparr_logger.error(error_msg)
                    return jsonify({"success": False, "message": error_msg}), 400
            except ValueError:
                error_msg = "Invalid JSON response from Whisparr V2 API"
                whisparr_logger.error(f"{error_msg}. Response content: {response.text[:200]}")
                return jsonify({"success": False, "message": error_msg}), 500
        else:
            error_msg = f"Received HTTP {response.status_code} from Whisparr API"
            whisparr_logger.error(error_msg)
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

@whisparr_bp.route('/versions', methods=['GET'])
def get_versions():
    """Get the version information from the Whisparr API"""
    try:
        # Get all configured instances
        api_keys = keys_manager.load_api_keys("whisparr")
        instances = api_keys.get("instances", [])
        
        if not instances:
            return jsonify({"success": False, "message": "No Whisparr instances configured"}), 404
            
        results = []
        for instance in instances:
            if not instance.get("enabled", True):
                continue
                
            api_url = instance.get("api_url")
            api_key = instance.get("api_key")
            instance_name = instance.get("name", "Default")
            
            if not api_url or not api_key:
                results.append({
                    "name": instance_name,
                    "success": False,
                    "message": "API URL or API Key missing"
                })
                continue
            
            # First try standard API endpoint
            version_url = f"{api_url.rstrip('/')}/api/system/status"
            headers = {"X-Api-Key": api_key}
            
            try:
                response = requests.get(version_url, headers=headers, timeout=10)
                
                # If we get a 404, try with the v3 path
                if response.status_code == 404:
                    whisparr_logger.debug(f"Standard API path failed for {instance_name}, trying v3 path")
                    v3_url = f"{api_url.rstrip('/')}/api/v3/system/status"
                    response = requests.get(v3_url, headers=headers, timeout=10)
                    
                if response.status_code == 200:
                    version_data = response.json()
                    version = version_data.get("version", "Unknown")
                    
                    # Validate that it's a V2 version
                    if version and version.startswith('2'):
                        results.append({
                            "name": instance_name,
                            "success": True,
                            "version": version,
                            "is_v2": True
                        })
                    elif version and version.startswith('3'):
                        # Reject Eros API version
                        results.append({
                            "name": instance_name,
                            "success": False,
                            "message": f"Incompatible Whisparr version {version} detected. Huntarr requires Whisparr V2.",
                            "version": version
                        })
                    else:
                        # Unexpected version
                        results.append({
                            "name": instance_name,
                            "success": False,
                            "message": f"Unexpected Whisparr version {version} detected. Huntarr requires Whisparr V2.",
                            "version": version
                        })
                else:
                    # API call failed
                    results.append({
                        "name": instance_name,
                        "success": False,
                        "message": f"Failed to get version information: HTTP {response.status_code}"
                    })
            except requests.exceptions.RequestException as e:
                results.append({
                    "name": instance_name,
                    "success": False,
                    "message": f"Connection error: {str(e)}"
                })
                
        return jsonify({"success": True, "results": results})
    except Exception as e:
        whisparr_logger.error(f"Error getting Whisparr versions: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

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