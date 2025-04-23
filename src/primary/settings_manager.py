#!/usr/bin/env python3
"""
Settings manager for Huntarr
Handles loading, saving, and providing settings from a JSON file
Supports default configurations for different Arr applications
"""

import os
import json
import pathlib
import logging
from typing import Dict, Any, Optional

# Create a simple logger for settings_manager
logging.basicConfig(level=logging.INFO)
settings_logger = logging.getLogger("settings_manager")

# Settings directory setup - Changed to use the root config directory
SETTINGS_DIR = pathlib.Path("/config")
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = SETTINGS_DIR / "huntarr.json"
DEFAULT_CONFIGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'default_configs'))

# Helper function to load default settings for a specific app
def load_default_app_settings(app_name: str) -> Dict[str, Any]:
    """Load default settings for a specific app from its JSON file."""
    default_file = os.path.join(DEFAULT_CONFIGS_DIR, f"{app_name}.json")
    try:
        if os.path.exists(default_file):
            with open(default_file, 'r') as f:
                return json.load(f)
        else:
            settings_logger.warning(f"Default settings file not found for app: {app_name}")
            return {}
    except Exception as e:
        settings_logger.error(f"Error loading default settings for {app_name}: {e}")
        return {}

# Helper function to get all default settings combined
def get_all_default_settings() -> Dict[str, Any]:
    """Load and combine default settings for all known apps."""
    all_defaults = {}
    for app_name in ['sonarr', 'radarr', 'lidarr', 'readarr']: # Add other apps if needed
        defaults = load_default_app_settings(app_name)
        if defaults:
            all_defaults[app_name] = defaults
    return all_defaults

# Function to merge user settings with defaults
def merge_settings_with_defaults(user_settings: Dict[str, Any]) -> Dict[str, Any]:
    """Merge user settings with default settings, ensuring all keys are present."""
    merged_settings = {}
    all_defaults = get_all_default_settings()

    for app_name, app_defaults in all_defaults.items():
        user_app_settings = user_settings.get(app_name, {})
        # Start with defaults, then update with user settings
        merged_app_settings = app_defaults.copy()
        merged_app_settings.update(user_app_settings)
        merged_settings[app_name] = merged_app_settings

    # Include any apps the user might have added that are not in defaults (though unlikely)
    for app_name, user_app_settings in user_settings.items():
        if app_name not in merged_settings:
             # Check if it looks like a valid app config (has api_key/api_url)
             # Or decide if unknown sections should be kept or discarded
            if isinstance(user_app_settings, dict) and ('api_key' in user_app_settings or 'api_url' in user_app_settings):
                settings_logger.warning(f"Keeping unknown settings section: {app_name}")
                merged_settings[app_name] = user_app_settings
            else:
                 settings_logger.warning(f"Discarding unknown or invalid settings section: {app_name}")

    return merged_settings

def _deep_update(d, u):
    """Recursively update a dictionary without overwriting entire nested dicts"""
    for k, v in u.items():
        if isinstance(v, dict) and k in d and isinstance(d[k], dict):
            _deep_update(d[k], v)
        else:
            d[k] = v

# Load settings from file
def load_settings() -> Dict[str, Any]:
    """Load settings from JSON file and merge with defaults."""
    user_settings = {}
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                content = f.read()
                if content.strip(): # Check if file is not empty
                    user_settings = json.loads(content)
                else:
                    settings_logger.warning(f"Settings file {SETTINGS_FILE} is empty. Using defaults.")
        else:
            settings_logger.warning(f"Settings file {SETTINGS_FILE} not found. Using defaults.")

        # Remove legacy global/ui sections if they exist before merging
        if "global" in user_settings:
            del user_settings["global"]
        if "ui" in user_settings:
            del user_settings["ui"]

        # Merge the loaded user settings with the defaults
        merged_settings = merge_settings_with_defaults(user_settings)
        return merged_settings

    except json.JSONDecodeError as e:
        settings_logger.error(f"Error decoding JSON from {SETTINGS_FILE}: {e}. Using defaults.")
        return get_all_default_settings()
    except Exception as e:
        settings_logger.error(f"Error loading settings: {e}. Using defaults.")
        return get_all_default_settings()

# Get all settings
def get_all_settings() -> Dict[str, Any]:
    """Get all settings as a dictionary"""
    return load_settings()

# Save settings to file
def save_settings(settings: Dict[str, Any]) -> bool:
    """Save settings to JSON file"""
    try:
        # Clean up any potential huntarr sections before saving
        for app in ["sonarr", "radarr", "lidarr", "readarr"]:
            if app in settings and "huntarr" in settings[app]:
                # Move all settings from app.huntarr directly to app level
                for key, value in settings[app]["huntarr"].items():
                    if key not in settings[app]:  # Don't overwrite existing settings
                        settings[app][key] = value
                # Remove the huntarr section
                del settings[app]["huntarr"]
        
        # Remove global section if present
        if "global" in settings:
            del settings["global"]
            
        # Remove UI section if present
        if "ui" in settings:
            del settings["ui"]
        
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
            json.dump(settings, file, indent=2)
        return True
    except Exception as e:
        settings_logger.error(f"Error saving settings: {e}")
        return False

# Update a specific setting
def update_setting(section: str, key: str, value: Any) -> bool:
    """Update a specific setting in a section"""
    settings = load_settings()
    
    # Create section if it doesn't exist
    if section not in settings:
        settings[section] = {}
    
    # Update the setting
    settings[section][key] = value
    
    # Save the updated settings
    return save_settings(settings)

# Get a specific setting
def get_setting(section: str, key: str, default: Any = None) -> Any:
    """Get a specific setting from a section"""
    settings = load_settings()
    
    # Check for settings directly in the section
    if section in settings:
        # Only check directly in the section, no huntarr sub-section backwards compatibility
        if key in settings[section]:
            return settings[section][key]
    
    # Return the default if the setting doesn't exist
    return default

# Get app type
def get_app_type() -> str:
    """Get the current app type"""
    settings = load_settings()
    return settings.get("app_type", "sonarr")

# Get API URL for the current app
def get_api_url() -> str:
    """Get the API URL for the current app type"""
    app_type = get_app_type()
    settings = load_settings()
    
    # Try to get from connections first
    connections = settings.get("connections", {})
    if app_type in connections and "api_url" in connections[app_type]:
        return connections[app_type]["api_url"]
    
    # Fallback to app section
    if app_type in settings and "api_url" in settings[app_type]:
        return settings[app_type]["api_url"]
    
    return ""

# Get API key for the current app
def get_api_key() -> str:
    """Get the API key for the current app type"""
    app_type = get_app_type()
    settings = load_settings()
    
    # Try to get from connections first
    connections = settings.get("connections", {})
    if app_type in connections and "api_key" in connections[app_type]:
        return connections[app_type]["api_key"]
    
    # Fallback to app section
    if app_type in settings and "api_key" in settings[app_type]:
        return settings[app_type]["api_key"]
    
    return ""

# Save API connection details
def save_api_details(app_type: str, api_url: str, api_key: str) -> bool:
    """Save API connection details for an app"""
    if app_type.lower() not in ["sonarr", "radarr", "lidarr", "readarr"]:
        return False
    
    settings = load_settings()
    
    # Ensure the connections section exists
    if "connections" not in settings:
        settings["connections"] = {}
    
    # Update the connection details
    settings["connections"][f"{app_type.lower()}_url"] = api_url
    settings["connections"][f"{app_type.lower()}_apikey"] = api_key
    
    return save_settings(settings)

# Get API details for a specific app
def get_api_details(app_type: str) -> Dict[str, str]:
    """Get API connection details for an app"""
    settings = load_settings()
    connections = settings.get("connections", {})
    
    return {
        "api_url": connections.get(f"{app_type.lower()}_url", ""),
        "api_key": connections.get(f"{app_type.lower()}_apikey", "")
    }

# Initialize settings file if it doesn't exist
if not SETTINGS_FILE.exists():
    save_settings(load_settings())