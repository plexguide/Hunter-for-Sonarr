#!/usr/bin/env python3
"""
Settings manager for Huntarr
Handles loading, saving, and providing settings from a JSON file
Simplified for Sonarr only
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

# Default settings - simplified for Sonarr only
DEFAULT_SETTINGS = {
    "ui": {
        "dark_mode": True
    },
    "app_type": "sonarr",  # Fixed to sonarr
    "connections": {},     # Holds API URL and key
    "global": {            # Global settings (UI preferences etc)
        "debug_mode": False,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "log_refresh_interval_seconds": 30
    },
    "sonarr": {            # Sonarr-specific settings
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
        
        # Remove any nested huntarr sections
        if "sonarr" in settings and "huntarr" in settings["sonarr"]:
            # Move all settings from sonarr.huntarr directly to sonarr level
            for key, value in settings["sonarr"]["huntarr"].items():
                if key not in settings["sonarr"]:  # Don't overwrite existing settings
                    settings["sonarr"][key] = value
            # Remove the huntarr section
            del settings["sonarr"]["huntarr"]
        
        # Force app_type to be sonarr
        settings["app_type"] = "sonarr"
        
        # Remove other app settings if they exist
        for app in ["radarr", "lidarr", "readarr"]:
            if app in settings:
                del settings[app]
                
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
        if "sonarr" in settings and "huntarr" in settings["sonarr"]:
            # Move all settings from sonarr.huntarr directly to sonarr level
            for key, value in settings["sonarr"]["huntarr"].items():
                if key not in settings["sonarr"]:  # Don't overwrite existing settings
                    settings["sonarr"][key] = value
            # Remove the huntarr section
            del settings["sonarr"]["huntarr"]
        
        # Force app_type to be sonarr
        settings["app_type"] = "sonarr"
        
        # Remove other app settings if they exist
        for app in ["radarr", "lidarr", "readarr"]:
            if app in settings:
                del settings[app]
        
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
    
    # Update the setting directly at section level, not under huntarr
    settings[section][key] = value
    
    # Save the updated settings
    return save_settings(settings)

# Get a specific setting
def get_setting(section: str, key: str, default: Any = None) -> Any:
    """Get a specific setting from a section"""
    settings = load_settings()
    
    # Check for nested huntarr settings and prefer them if they exist
    if section in settings:
        # First check direct in the section
        if key in settings[section]:
            return settings[section][key]
        
        # Check in the huntarr sub-section if it exists (for backwards compatibility)
        if "huntarr" in settings[section] and key in settings[section]["huntarr"]:
            # Get the value from the huntarr sub-section
            value = settings[section]["huntarr"][key]
            # Also move this setting to the top level for future access
            settings[section][key] = value
            save_settings(settings)
            return value
    
    # Return the default if the setting doesn't exist
    return default

# Get app type - always returns "sonarr"
def get_app_type() -> str:
    """Get the current app type - always sonarr"""
    return "sonarr"

# Save API details for Sonarr
def save_api_keys(app_type: str, api_url: str, api_key: str) -> bool:
    """Save API keys for Sonarr"""
    if app_type.lower() != "sonarr":
        return False
    
    settings = load_settings()
    
    # Ensure the connections section exists
    if "connections" not in settings:
        settings["connections"] = {}
    
    # Store for sonarr
    settings["connections"]["sonarr"] = {
        "api_url": api_url,
        "api_key": api_key
    }
    
    return save_settings(settings)

# Get API details for Sonarr
def get_api_keys(app_type: str = "sonarr") -> tuple:
    """Get API keys for Sonarr"""
    settings = load_settings()
    
    # Initialize with empty values
    api_url = ""
    api_key = ""
    
    # Check in connections section first
    connections = settings.get("connections", {})
    if "sonarr" in connections:
        api_url = connections["sonarr"].get("api_url", "")
        api_key = connections["sonarr"].get("api_key", "")
    
    # If not found, check in old format for backward compatibility
    if not api_url and not api_key:
        api_url = connections.get("sonarr_url", "")
        api_key = connections.get("sonarr_apikey", "")
    
    return api_url, api_key

# Initialize settings file if it doesn't exist
if not SETTINGS_FILE.exists():
    save_settings(load_settings())