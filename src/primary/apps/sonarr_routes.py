#!/usr/bin/env python3

from flask import Blueprint, request, jsonify
import datetime, os, requests
from src.primary import keys_manager
from src.primary.state import get_state_file_path, reset_state_file
from src.primary.utils.logger import get_logger
import traceback
import socket
from urllib.parse import urlparse

sonarr_bp = Blueprint('sonarr', __name__)
sonarr_logger = get_logger("sonarr")

# Make sure we're using the correct state files
PROCESSED_MISSING_FILE = get_state_file_path("sonarr", "processed_missing") 
PROCESSED_UPGRADES_FILE = get_state_file_path("sonarr", "processed_upgrades")

@sonarr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to a Sonarr API instance with comprehensive diagnostics"""
    data = request.json
    api_url = data.get('api_url')
    api_key = data.get('api_key')
    api_timeout = data.get('api_timeout', 30)  # Use longer timeout for connection test

    if not api_url or not api_key:
        return jsonify({"success": False, "message": "API URL and API Key are required"}), 400
    
    # Log the test attempt
    sonarr_logger.info(f"Testing connection to Sonarr API at {api_url}")
    
    # First check if URL is properly formatted
    if not (api_url.startswith('http://') or api_url.startswith('https://')):
        error_msg = "API URL must start with http:// or https://"
        sonarr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 400
    
    # Try to establish a socket connection first to check basic connectivity
    parsed_url = urlparse(api_url)
    hostname = parsed_url.hostname
    port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
    
    try:
        # Try socket connection for quick feedback on connectivity issues
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)  # Short timeout for quick feedback
        result = sock.connect_ex((hostname, port))
        sock.close()
        
        if result != 0:
            error_msg = f"Connection refused - Unable to connect to {hostname}:{port}. Please check if the server is running and the port is correct."
            sonarr_logger.error(error_msg)
            return jsonify({"success": False, "message": error_msg}), 404
    except socket.gaierror:
        error_msg = f"DNS resolution failed - Cannot resolve hostname: {hostname}. Please check your URL."
        sonarr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 404
    except Exception as e:
        # Log the socket testing error but continue with the full request
        sonarr_logger.debug(f"Socket test error, continuing with full request: {str(e)}")
        
    # Create the test URL and set headers
    test_url = f"{api_url.rstrip('/')}/api/v3/system/status"
    headers = {'X-Api-Key': api_key}

    try:
        # Now proceed with the actual API request
        response = requests.get(test_url, headers=headers, timeout=(10, api_timeout))
        
        # For HTTP errors, provide more specific feedback
        if response.status_code == 401:
            error_msg = "Authentication failed: Invalid API key"
            sonarr_logger.error(error_msg)
            return jsonify({"success": False, "message": error_msg}), 401
        elif response.status_code == 403:
            error_msg = "Access forbidden: Check API key permissions"
            sonarr_logger.error(error_msg)
            return jsonify({"success": False, "message": error_msg}), 403
        elif response.status_code == 404:
            error_msg = "API endpoint not found: This doesn't appear to be a valid Sonarr server. Check your URL."
            sonarr_logger.error(error_msg)
            return jsonify({"success": False, "message": error_msg}), 404
        elif response.status_code >= 500:
            error_msg = f"Sonarr server error (HTTP {response.status_code}): The Sonarr server is experiencing issues"
            sonarr_logger.error(error_msg)
            return jsonify({"success": False, "message": error_msg}), response.status_code
        
        # Raise for other HTTP errors
        response.raise_for_status()
        
        # Log HTTP status code for diagnostic purposes
        sonarr_logger.debug(f"Sonarr API status code: {response.status_code}")

        # Ensure the response is valid JSON
        try:
            response_data = response.json()
            
            # We no longer save keys here since we use instances
            # keys_manager.save_api_keys("sonarr", api_url, api_key)
            
            sonarr_logger.info(f"Successfully connected to Sonarr API version: {response_data.get('version', 'unknown')}")

            # Return success with some useful information
            return jsonify({
                "success": True,
                "message": "Successfully connected to Sonarr API",
                "version": response_data.get('version', 'unknown')
            })
        except ValueError:
            error_msg = "Invalid JSON response from Sonarr API - This doesn't appear to be a valid Sonarr server"
            sonarr_logger.error(f"{error_msg}. Response content: {response.text[:200]}")
            return jsonify({"success": False, "message": error_msg}), 500

    except requests.exceptions.Timeout as e:
        error_msg = f"Connection timed out after {api_timeout} seconds"
        sonarr_logger.error(f"{error_msg}: {str(e)}")
        return jsonify({"success": False, "message": error_msg}), 504
        
    except requests.exceptions.ConnectionError as e:
        # Handle different types of connection errors
        error_details = str(e)
        if "Connection refused" in error_details:
            error_msg = f"Connection refused - Sonarr is not running on {api_url} or the port is incorrect"
        elif "Name or service not known" in error_details or "getaddrinfo failed" in error_details:
            error_msg = f"DNS resolution failed - Cannot find host '{urlparse(api_url).hostname}'. Check your URL."
        else:
            error_msg = f"Connection error - Check if Sonarr is running: {error_details}"
            
        sonarr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 404
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Connection test failed: {str(e)}"
        sonarr_logger.error(error_msg)
        return jsonify({"success": False, "message": error_msg}), 500
