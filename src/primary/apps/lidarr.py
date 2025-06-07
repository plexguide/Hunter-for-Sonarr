#!/usr/bin/env python3
"""
Lidarr Blueprint for Huntarr
Defines Flask routes for interacting with Lidarr
"""

import json
import traceback
import requests
from flask import Blueprint, jsonify, request
from src.primary.utils.logger import get_logger
from src.primary.apps.lidarr import api as lidarr_api
from src.primary.state import reset_state_file, get_state_file_path
from src.primary.settings_manager import load_settings
import src.primary.config as config

# Create a logger for this module
lidarr_logger = get_logger("lidarr")

# Create Blueprint for Lidarr routes
lidarr_bp = Blueprint('lidarr', __name__)

# Make sure we're using the correct state files
PROCESSED_MISSING_FILE = get_state_file_path("lidarr", "processed_missing") 
PROCESSED_UPGRADES_FILE = get_state_file_path("lidarr", "processed_upgrades")

# Function to check if Lidarr is configured
def is_configured():
    """Check if Lidarr API credentials are configured by checking if at least one instance is enabled"""
    settings = load_settings("lidarr")
    
    if not settings:
        lidarr_logger.debug("No settings found for Lidarr")
        return False
        
    # Check if instances are configured
    if "instances" in settings and isinstance(settings["instances"], list) and settings["instances"]:
        for instance in settings["instances"]:
            if instance.get("enabled", True) and instance.get("api_url") and instance.get("api_key"):
                lidarr_logger.debug(f"Found configured Lidarr instance: {instance.get('name', 'Unnamed')}")
                return True
                
        lidarr_logger.debug("No enabled Lidarr instances found with valid API URL and key")
        return False
    
    # Fallback to legacy single-instance config
    api_url = settings.get("api_url")
    api_key = settings.get("api_key")
    return bool(api_url and api_key)

# Get all valid instances from settings
def get_configured_instances():
    """Get all configured and enabled Lidarr instances"""
    settings = load_settings("lidarr")
    instances = []
    
    if not settings:
        lidarr_logger.debug("No settings found for Lidarr")
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
    
    lidarr_logger.info(f"Found {len(instances)} configured and enabled Lidarr instances")
    return instances

@lidarr_bp.route('/status', methods=['GET'])
def status():
    """Get Lidarr connection status and version."""
    try:
        # Get API settings from config
        settings = config.get_app_settings("lidarr")
        
        if not settings or not settings.get("api_url") or not settings.get("api_key"):
            return jsonify({"connected": False, "message": "Lidarr is not configured"}), 200
            
        api_url = settings["api_url"]
        api_key = settings["api_key"]
        api_timeout = settings.get("api_timeout", 30)
        
        # Check connection and get system status
        system_status = lidarr_api.get_system_status(api_url, api_key, api_timeout)
        
        if system_status is not None:
            version = system_status.get("version", "Unknown")
            return jsonify({
                "connected": True,
                "version": version,
                "message": f"Connected to Lidarr {version}"
            }), 200
        else:
            return jsonify({
                "connected": False,
                "message": "Failed to connect to Lidarr"
            }), 200
            
    except Exception as e:
        error_message = f"Error checking Lidarr status: {str(e)}"
        lidarr_logger.error(error_message)
        lidarr_logger.error(traceback.format_exc())
        return jsonify({"connected": False, "message": error_message}), 500

@lidarr_bp.route('/test-connection', methods=['POST'])
def test_connection():
    """Test connection to Lidarr with provided API settings."""
    try:
        # Extract API settings from request
        data = request.json
        api_url = data.get("api_url", "").rstrip('/')
        api_key = data.get("api_key", "")
        api_timeout = int(data.get("api_timeout", 30))
        
        if not api_url or not api_key:
            return jsonify({"success": False, "message": "API URL and API Key are required"}), 400
            
        # Auto-correct URL if missing http(s) scheme
        if not (api_url.startswith('http://') or api_url.startswith('https://')):
            lidarr_logger.warning(f"API URL missing http(s) scheme: {api_url}")
            api_url = f"http://{api_url}"
            lidarr_logger.warning(f"Auto-correcting URL to: {api_url}")
            
        # Test connection to Lidarr
        system_status = lidarr_api.get_system_status(api_url, api_key, api_timeout)
        
        if system_status is not None:
            version = system_status.get("version", "Unknown")
            return jsonify({
                "success": True,
                "version": version,
                "message": f"Successfully connected to Lidarr {version}"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Failed to connect to Lidarr. Check URL and API Key."
            }), 400
            
    except requests.exceptions.RequestException as e:
        error_message = f"Connection error: {str(e)}"
        if hasattr(e, 'response'):
            if e.response is not None:
                error_message += f" - Status Code: {e.response.status_code}, Response: {e.response.text[:200]}"
        lidarr_logger.error(f"Lidarr connection error: {error_message}")
        return jsonify({"success": False, "message": error_message}), 500
    except Exception as e: # Catch any other unexpected errors
        lidarr_logger.error(f"An unexpected error occurred during Lidarr connection test: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": f"An unexpected error occurred: {str(e)}"}), 500

@lidarr_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get statistics about Lidarr library."""
    try:
        # Get API settings from config
        settings = config.get_app_settings("lidarr")
        
        if not settings or not settings.get("api_url") or not settings.get("api_key"):
            return jsonify({"error": "Lidarr is not configured"}), 400
            
        api_url = settings["api_url"]
        api_key = settings["api_key"]
        api_timeout = settings.get("api_timeout", 30)
        monitored_only = settings.get("monitored_only", True)
        
        # Get all artists from Lidarr
        all_artists = lidarr_api.get_artists(api_url, api_key, api_timeout)
        if all_artists is None:
            return jsonify({"error": "Failed to get artists from Lidarr"}), 500
            
        # Count total artists and monitored artists
        total_artists = len(all_artists)
        monitored_artists = sum(1 for artist in all_artists if artist.get("monitored", False))
        
        # Get missing albums
        missing_albums = lidarr_api.get_missing_albums(api_url, api_key, api_timeout, monitored_only)
        total_missing = len(missing_albums) if missing_albums is not None else 0
        
        # Get cutoff unmet albums
        cutoff_unmet = lidarr_api.get_cutoff_unmet_albums(api_url, api_key, api_timeout, monitored_only)
        total_upgradable = len(cutoff_unmet) if cutoff_unmet is not None else 0
        
        # Get download queue
        queue_size = lidarr_api.get_download_queue_size(api_url, api_key, api_timeout)
        
        # Return stats
        return jsonify({
            "total_artists": total_artists,
            "monitored_artists": monitored_artists,
            "missing_albums": total_missing,
            "upgradable_albums": total_upgradable,
            "queue_size": queue_size
        }), 200
        
    except Exception as e:
        error_message = f"Error getting Lidarr stats: {str(e)}"
        lidarr_logger.error(error_message)
        lidarr_logger.error(traceback.format_exc())
        return jsonify({"error": error_message}), 500

@lidarr_bp.route('/reset-state', methods=['POST'])
def reset_state():
    """Reset the Lidarr state files to clear processed IDs."""
    try:
        # JSON object with flags for which states to reset
        data = request.json or {}
        reset_missing = data.get('reset_missing', True)
        reset_upgrades = data.get('reset_upgrades', True)
        
        # Reset missing state if requested
        if reset_missing:
            reset_state_file("lidarr", "processed_missing")
            lidarr_logger.info("Reset Lidarr missing albums state")
            
        # Reset upgrades state if requested
        if reset_upgrades:
            reset_state_file("lidarr", "processed_upgrades")
            lidarr_logger.info("Reset Lidarr upgrades state")
            
        return jsonify({
            "success": True,
            "message": "Lidarr state reset successfully"
        }), 200
        
    except Exception as e:
        error_message = f"Error resetting Lidarr state: {str(e)}"
        lidarr_logger.error(error_message)
        lidarr_logger.error(traceback.format_exc())
        return jsonify({"error": error_message}), 500