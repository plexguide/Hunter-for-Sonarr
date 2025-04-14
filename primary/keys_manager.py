#!/usr/bin/env python3
"""
Keys manager for Huntarr
Handles storage and retrieval of Sonarr API keys and URLs from huntarr.json
Simplified for Sonarr only
"""

import os
import json
import pathlib
import logging
from typing import Dict, Any, Optional, Tuple

# Create a simple logger
logging.basicConfig(level=logging.INFO)
keys_logger = logging.getLogger("keys_manager")

# Settings directory - Changed to match the updated settings_manager.py
SETTINGS_DIR = pathlib.Path("/config")
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SETTINGS_DIR / "huntarr.json"

def save_api_keys(app_type: str, api_url: str, api_key: str) -> bool:
    """
    Save API keys and URL for Sonarr.
    
    Args:
        app_type: The type of app (should always be sonarr)
        api_url: The API URL for Sonarr
        api_key: The API key
    
    Returns:
        bool: True if successful, False otherwise
    """
    if app_type.lower() != "sonarr":
        keys_logger.warning(f"Attempted to save keys for non-Sonarr app: {app_type}")
        return False
        
    try:
        # Ensure settings file exists
        if not SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'w') as f:
                json.dump({}, f)
        
        # Load existing settings
        with open(SETTINGS_FILE, 'r') as f:
            settings_data = json.load(f)
        
        # Ensure we have a connections section
        if "connections" not in settings_data:
            settings_data["connections"] = {}
            
        # Create or update connection info for Sonarr
        settings_data["connections"]["sonarr"] = {
            'api_url': api_url,
            'api_key': api_key
        }
        
        # Save the file
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings_data, f, indent=2)
        
        keys_logger.info("Saved Sonarr API keys")
        return True
    except Exception as e:
        keys_logger.error(f"Error saving Sonarr API keys: {e}")
        return False

def get_api_keys(app_type: str = "sonarr") -> Tuple[str, str]:
    """
    Get API keys and URL for Sonarr.
    
    Args:
        app_type: The type of app (should always be sonarr)
    
    Returns:
        Tuple[str, str]: (api_url, api_key)
    """
    if app_type.lower() != "sonarr":
        keys_logger.warning(f"Attempted to get keys for non-Sonarr app: {app_type}")
        return '', ''
        
    try:
        # Check if settings file exists
        if not SETTINGS_FILE.exists():
            keys_logger.warning(f"Settings file not found at {SETTINGS_FILE}")
            return '', ''
            
        # Load settings file
        with open(SETTINGS_FILE, 'r') as f:
            settings_data = json.load(f)
        
        # Get connection info
        connections = settings_data.get("connections", {})
        app_config = connections.get("sonarr", {})
        
        api_url = app_config.get('api_url', '')
        api_key = app_config.get('api_key', '')
        
        # Log what we found (without revealing the full API key)
        masked_key = "****" + api_key[-4:] if len(api_key) > 4 else "****" if api_key else ""
        keys_logger.debug(f"Retrieved Sonarr API info: URL={api_url}, Key={masked_key}")
        
        # Return URL and key
        return api_url, api_key
    except Exception as e:
        keys_logger.error(f"Error getting Sonarr API keys: {e}")
        return '', ''

def is_sonarr_configured() -> bool:
    """
    Check if Sonarr is configured.
    
    Returns:
        bool: True if Sonarr is configured, False otherwise
    """
    try:
        # Check if settings file exists
        if not SETTINGS_FILE.exists():
            return False
            
        # Load settings file
        with open(SETTINGS_FILE, 'r') as f:
            settings_data = json.load(f)
        
        # Get connection info
        connections = settings_data.get("connections", {})
        sonarr_config = connections.get("sonarr", {})
        
        # Check if Sonarr is configured with both URL and API key
        return bool(sonarr_config.get('api_url') and sonarr_config.get('api_key'))
    except Exception as e:
        keys_logger.error(f"Error checking if Sonarr is configured: {e}")
        return False