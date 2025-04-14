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

# Default settings - updated to have a flat structure with no global section or UI settings
DEFAULT_SETTINGS = {
    "app_type": "sonarr",  # Default app type
    "connections": {},     # Holds API URLs and keys
    "sonarr": {            # Sonarr-specific settings - all settings at this level, no nesting
        "hunt_missing_shows": 1,
        "hunt_upgrade_episodes": 0,
        "sleep_duration": 900,
        "state_reset_interval_hours": 168,
        "monitored_only": True,
        "skip_future_episodes": True,
        "skip_series_refresh": False,
        "random_missing": True,
        "random_upgrades": True,
        "debug_mode": False,
        "api_timeout": 60,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "log_refresh_interval_seconds": 30
    },
    "radarr": {            # Radarr-specific settings
        "hunt_missing_movies": 1,
        "hunt_upgrade_movies": 0,
        "sleep_duration": 900,
        "state_reset_interval_hours": 168,
        "monitored_only": True,
        "skip_future_releases": True,
        "skip_movie_refresh": False,
        "random_missing": True,
        "random_upgrades": True,
        "debug_mode": False,
        "api_timeout": 60,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "log_refresh_interval_seconds": 30
    },
    "lidarr": {            # Lidarr-specific settings
        "hunt_missing_albums": 1,
        "hunt_upgrade_tracks": 0,
        "sleep_duration": 900,
        "state_reset_interval_hours": 168,
        "monitored_only": True,
        "skip_future_releases": True,
        "skip_artist_refresh": False,
        "random_missing": True,
        "random_upgrades": True,
        "debug_mode": False,
        "api_timeout": 60,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "log_refresh_interval_seconds": 30
    },
    "readarr": {           # Readarr-specific settings
        "hunt_missing_books": 1,
        "hunt_upgrade_books": 0,
        "sleep_duration": 900,
        "state_reset_interval_hours": 168,
        "monitored_only": True,
        "skip_future_releases": True,
        "skip_author_refresh": False,
        "random_missing": True,
        "random_upgrades": True,
        "debug_mode": False,
        "api_timeout": 60,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "log_refresh_interval_seconds": 30
    }
}

def _deep_update(d, u):
    """Recursively update a dictionary without overwriting entire nested dicts"""
    for k, v in u.items():
        if isinstance(v, dict) and k in d and isinstance(d[k], dict):
            _deep_update(d[k], v)
        else:
            d[k] = v

# Load settings from file
def load_settings() -> Dict[str, Any]:
    """Load settings from JSON file"""
    try:
        # Start with default settings
        settings = DEFAULT_SETTINGS.copy()
        
        # Then load from file if it exists
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
                user_settings = json.load(file)
                # Deep merge user settings
                _deep_update(settings, user_settings)
                
        # Remove any "huntarr" nested sections from app configs
        for app in ["sonarr", "radarr", "lidarr", "readarr"]:
            if app in settings and "huntarr" in settings[app]:
                # Move all settings from app.huntarr directly to app level
                for key, value in settings[app]["huntarr"].items():
                    if key not in settings[app]:  # Don't overwrite existing settings
                        settings[app][key] = value
                # Remove the huntarr section
                del settings[app]["huntarr"]
        
        # Remove any "global" section
        if "global" in settings:
            del settings["global"]
            
        # Remove any "ui" section
        if "ui" in settings:
            del settings["ui"]
                
        return settings
    except Exception as e:
        settings_logger.error(f"Error loading settings: {e}")
        return DEFAULT_SETTINGS.copy()

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