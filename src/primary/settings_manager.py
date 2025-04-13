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

# Default settings - updated to have a flat structure with no nesting
DEFAULT_SETTINGS = {
    "ui": {
        "dark_mode": True
    },
    "app_type": "sonarr",  # Default app type
    "connections": {},     # Holds API URLs and keys
    "global": {            # Global settings (UI preferences etc)
    },
    "sonarr": {            # Sonarr-specific settings - all settings at this level, no nesting
        "hunt_missing_shows": 1,
        "hunt_upgrade_episodes": 0,
        "monitored_only": True,
        "skip_future_episodes": True,
        "skip_series_refresh": False,
        "sleep_duration": 900,
        "state_reset_interval_hours": 168,
        "api_timeout": 60,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "debug_mode": False,
        "random_missing": True,
        "random_upgrades": True,
        "log_refresh_interval_seconds": 30
    },
    "radarr": {            # Radarr-specific settings - all settings at this level, no nesting
        "hunt_missing_movies": 1,
        "hunt_upgrade_movies": 0,
        "monitored_only": True,
        "skip_future_releases": True,
        "skip_movie_refresh": False,
        "sleep_duration": 900,
        "state_reset_interval_hours": 168,
        "api_timeout": 60,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "debug_mode": False,
        "random_missing": True,
        "random_upgrades": True,
        "log_refresh_interval_seconds": 30
    },
    "lidarr": {            # Lidarr-specific settings - all settings at this level, no nesting
        "hunt_missing_albums": 1,
        "hunt_upgrade_tracks": 0,
        "monitored_only": True,
        "skip_future_releases": True,
        "skip_artist_refresh": False,
        "sleep_duration": 900,
        "state_reset_interval_hours": 168,
        "api_timeout": 60,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "debug_mode": False,
        "random_missing": True,
        "random_upgrades": True,
        "log_refresh_interval_seconds": 30
    },
    "readarr": {           # Readarr-specific settings - all settings at this level, no nesting
        "hunt_missing_books": 1,
        "hunt_upgrade_books": 0,
        "monitored_only": True,
        "skip_future_releases": True,
        "skip_author_refresh": False,
        "sleep_duration": 900,
        "state_reset_interval_hours": 168,
        "api_timeout": 60,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "debug_mode": False,
        "random_missing": True,
        "random_upgrades": True,
        "log_refresh_interval_seconds": 30
    }
}

# Load settings from file
def load_settings() -> Dict[str, Any]:
    """Load settings from JSON file"""
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
                loaded_settings = json.load(file)
                
                # Check loaded settings structure, remove any nested huntarr/advanced sections
                for app_type in ["sonarr", "radarr", "lidarr", "readarr"]:
                    if app_type in loaded_settings:
                        app_settings = loaded_settings[app_type]
                        
                        # If we find a nested huntarr or advanced section, flatten it
                        if isinstance(app_settings, dict):
                            # Extract nested huntarr settings
                            if "huntarr" in app_settings and isinstance(app_settings["huntarr"], dict):
                                for key, value in app_settings["huntarr"].items():
                                    # Only copy if not already set at top level
                                    if key not in app_settings:
                                        app_settings[key] = value
                                # Remove the nested section
                                app_settings.pop("huntarr", None)
                                
                            # Extract nested advanced settings
                            if "advanced" in app_settings and isinstance(app_settings["advanced"], dict):
                                for key, value in app_settings["advanced"].items():
                                    # Only copy if not already set at top level
                                    if key not in app_settings:
                                        app_settings[key] = value
                                # Remove the nested section
                                app_settings.pop("advanced", None)
                
                # Merge with defaults to ensure all required keys exist
                merged_settings = DEFAULT_SETTINGS.copy()
                
                # Update defaults with loaded settings
                def deep_update(source, updates):
                    for key, value in updates.items():
                        if key in source and isinstance(source[key], dict) and isinstance(value, dict):
                            source[key] = deep_update(source[key], value)
                        else:
                            source[key] = value
                    return source
                
                merged_settings = deep_update(merged_settings, loaded_settings)
                
                return merged_settings
        else:
            # If file doesn't exist, create it with default settings
            save_settings(DEFAULT_SETTINGS)
            return DEFAULT_SETTINGS
    except Exception as e:
        settings_logger.error(f"Error loading settings: {e}")
        # If there's an error, return defaults and try to save them
        try:
            save_settings(DEFAULT_SETTINGS)
        except Exception as save_error:
            settings_logger.error(f"Error saving default settings: {save_error}")
        return DEFAULT_SETTINGS

# Save settings to file
def save_settings(settings: Dict[str, Any]) -> bool:
    """Save settings to JSON file"""
    try:
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
    
    # Check if the section exists
    if section not in settings:
        return default
    
    # Check if the key exists in the section
    if key not in settings[section]:
        return default
    
    # Return the setting value
    return settings[section][key]

# Get the current app type
def get_app_type() -> str:
    """Get the current app type from settings or environment"""
    # Check for environment variable first
    env_app_type = os.environ.get("APP_TYPE")
    if env_app_type and env_app_type.lower() in ["sonarr", "radarr", "lidarr", "readarr"]:
        return env_app_type.lower()
    
    # Fall back to settings file
    app_type = get_setting("app_type", None)
    if app_type and app_type.lower() in ["sonarr", "radarr", "lidarr", "readarr"]:
        return app_type.lower()
    
    # Default to sonarr if nothing else is specified
    return "sonarr"

# Set the app type
def set_app_type(app_type: str) -> bool:
    """Set the app type"""
    if app_type.lower() not in ["sonarr", "radarr", "lidarr", "readarr"]:
        return False
    
    settings = load_settings()
    settings["app_type"] = app_type.lower()
    return save_settings(settings)

# Get the API URL for the current app
def get_api_url() -> str:
    """Get the API URL for the current app"""
    app_type = get_app_type()
    api_url = os.environ.get(f"{app_type.upper()}_URL")
    
    if not api_url:
        # Try to get from connections in settings
        settings = load_settings()
        connections = settings.get("connections", {})
        api_url = connections.get(f"{app_type}_url", "")
    
    return api_url

# Get the API key for the current app
def get_api_key() -> str:
    """Get the API key for the current app"""
    app_type = get_app_type()
    api_key = os.environ.get(f"{app_type.upper()}_APIKEY")
    
    if not api_key:
        # Try to get from connections in settings
        settings = load_settings()
        connections = settings.get("connections", {})
        api_key = connections.get(f"{app_type}_apikey", "")
    
    return api_key

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