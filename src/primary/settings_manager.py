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
    # Include api_url and api_key in the defaults expected structure
    default_structure = {'api_url': '', 'api_key': ''} 
    default_file = os.path.join(DEFAULT_CONFIGS_DIR, f"{app_name}.json")
    try:
        if os.path.exists(default_file):
            with open(default_file, 'r') as f:
                app_defaults = json.load(f)
                # Ensure base keys exist even if not in the file
                default_structure.update(app_defaults) 
                return default_structure
        else:
            settings_logger.warning(f"Default settings file not found for app: {app_name}")
            # Return the base structure even if file is missing
            return default_structure 
    except Exception as e:
        settings_logger.error(f"Error loading default settings for {app_name}: {e}")
        # Return the base structure on error
        return default_structure 

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

    # Ensure 'ui' settings are handled if they exist
    if 'ui' in user_settings:
         merged_settings['ui'] = load_default_app_settings('ui') # Assuming ui.json exists
         merged_settings['ui'].update(user_settings.get('ui', {}))

    # Ensure 'global' settings are handled if they exist
    if 'global' in user_settings:
         merged_settings['global'] = load_default_app_settings('global') # Assuming global.json exists
         merged_settings['global'].update(user_settings.get('global', {}))

    for app_name, app_defaults in all_defaults.items():
        # Skip ui/global as handled above
        if app_name in ['ui', 'global']: 
            continue
            
        user_app_settings = user_settings.get(app_name, {})
        # Start with defaults, then update with user settings
        merged_app_settings = app_defaults.copy()
        merged_app_settings.update(user_app_settings)
        merged_settings[app_name] = merged_app_settings

    # Include any apps the user might have added that are not in defaults
    for app_name, user_app_settings in user_settings.items():
        if app_name not in merged_settings and app_name not in ['ui', 'global']:
             # Keep unknown sections if they look like app configs
            if isinstance(user_app_settings, dict) and ('api_key' in user_app_settings or 'api_url' in user_app_settings):
                settings_logger.warning(f"Keeping unknown settings section: {app_name}")
                merged_settings[app_name] = user_app_settings
            # else: # Optionally discard unknown sections
            #    settings_logger.warning(f"Discarding unknown settings section: {app_name}")
                
    # Remove the legacy 'connections' section if it exists
    if "connections" in merged_settings:
        del merged_settings["connections"]
        settings_logger.info("Removed legacy 'connections' section from settings.")

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
def save_settings(settings_data: Dict[str, Any]) -> bool:
    """Save settings to the JSON file."""
    try:
        # Remove the legacy 'connections' section before saving
        if "connections" in settings_data:
            del settings_data["connections"]
            
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings_data, f, indent=2)
        settings_logger.info(f"Settings saved successfully to {SETTINGS_FILE}")
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
    settings = get_all_settings()
    app_settings = settings.get(app_type, {})
    return {
        "api_url": app_settings.get("api_url", ""),
        "api_key": app_settings.get("api_key", "")
    }

# List configured apps
def list_configured_apps() -> Dict[str, bool]:
    """Check which apps have both API URL and API Key configured."""
    apps = ['sonarr', 'radarr', 'lidarr', 'readarr']
    configured_status = {}
    all_settings = get_all_settings() # Use the existing function to get all settings
    for app_name in apps:
        app_settings = all_settings.get(app_name, {})
        is_configured = bool(app_settings.get('api_url') and app_settings.get('api_key'))
        configured_status[app_name] = is_configured
    return configured_status

# Add default settings structure including API keys
DEFAULT_SETTINGS = get_all_default_settings()
# Add default UI and Global settings if they exist
DEFAULT_SETTINGS['ui'] = load_default_app_settings('ui')
DEFAULT_SETTINGS['global'] = load_default_app_settings('global')

# Ensure settings file exists on first load, merge with defaults
if not SETTINGS_FILE.exists():
    settings_logger.info("Settings file not found. Creating with default settings.")
    save_settings(DEFAULT_SETTINGS)
else:
    # Load existing settings and merge with defaults to ensure all keys are present
    current_settings = get_all_settings() # This loads from file
    merged = merge_settings_with_defaults(current_settings)
    # Save back if changes were made during merge (e.g., new defaults added or legacy removed)
    if merged != current_settings: 
        settings_logger.info("Merging settings with new defaults/structure.")
        save_settings(merged)