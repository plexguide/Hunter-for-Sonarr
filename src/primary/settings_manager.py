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

# Default settings
DEFAULT_SETTINGS = {
    "ui": {
        "dark_mode": True
    },
    "app_type": "sonarr",  # Default app type
    "connections": {},     # Holds API URLs and keys
    "global": {            # Global settings (UI preferences etc)
    },
    "sonarr": {            # Sonarr-specific settings
    },
    "radarr": {            # Radarr-specific settings
    },
    "lidarr": {            # Lidarr-specific settings
    },
    "readarr": {           # Readarr-specific settings
    }
}

# Define default configurations directly in this file instead of loading from external JSON
DEFAULT_CONFIGS = {
    "sonarr": {
        "hunt_missing_shows": 1,
        "hunt_upgrade_episodes": 0,
        "monitored_only": True,
        "skip_future_episodes": True,
        "skip_series_refresh": False,
        "log_refresh_interval_seconds": 30,
        "sleep_duration": 900,
        "state_reset_interval_hours": 168,
        "api_timeout": 60,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "debug_mode": False,
        "random_missing": True,
        "random_upgrades": True
    },
    "radarr": {
        "hunt_missing_movies": 1,
        "hunt_upgrade_movies": 0,
        "monitored_only": True,
        "skip_future_releases": True,
        "skip_movie_refresh": False,
        "log_refresh_interval_seconds": 30,
        "sleep_duration": 900,
        "state_reset_interval_hours": 168,
        "api_timeout": 60,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "debug_mode": False,
        "random_missing": True,
        "random_upgrades": True
    },
    "lidarr": {
        "hunt_missing_albums": 1,
        "hunt_upgrade_tracks": 0,
        "monitored_only": True,
        "skip_future_releases": True,
        "skip_artist_refresh": False,
        "log_refresh_interval_seconds": 30,
        "sleep_duration": 900,
        "state_reset_interval_hours": 168,
        "api_timeout": 60,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "debug_mode": False,
        "random_missing": True,
        "random_upgrades": True
    },
    "readarr": {
        "hunt_missing_books": 1,
        "hunt_upgrade_books": 0,
        "monitored_only": True,
        "skip_future_releases": True,
        "skip_author_refresh": False,
        "log_refresh_interval_seconds": 30,
        "sleep_duration": 900,
        "state_reset_interval_hours": 168,
        "api_timeout": 60,
        "command_wait_delay": 1,
        "command_wait_attempts": 600,
        "minimum_download_queue_size": -1,
        "debug_mode": False,
        "random_missing": True,
        "random_upgrades": True
    }
}

def get_default_config_for_app(app_type: str) -> Dict[str, Any]:
    """Get default config for a specific app type"""
    if app_type in DEFAULT_CONFIGS:
        return DEFAULT_CONFIGS[app_type]
    settings_logger.warning(f"No default config found for app_type: {app_type}, falling back to sonarr")
    return DEFAULT_CONFIGS.get("sonarr", {})

def get_app_defaults(app_type):
    """Get default settings for a specific app type"""
    if app_type in DEFAULT_CONFIGS:
        return DEFAULT_CONFIGS[app_type]
    else:
        settings_logger.warning(f"No default config found for app_type: {app_type}, falling back to sonarr")
        return DEFAULT_CONFIGS.get("sonarr", {})

def get_env_settings():
    """Get settings from environment variables"""
    env_settings = {
        "app_type": os.environ.get("APP_TYPE", "sonarr").lower()
    }
    
    # Optional environment variables
    if "API_TIMEOUT" in os.environ:
        try:
            env_settings["api_timeout"] = int(os.environ.get("API_TIMEOUT"))
        except ValueError:
            pass
            
    if "MONITORED_ONLY" in os.environ:
        env_settings["monitored_only"] = os.environ.get("MONITORED_ONLY", "true").lower() == "true"
        
    # All other environment variables that might override defaults
    for key, value in os.environ.items():
        if key.startswith(("HUNT_", "SLEEP_", "STATE_", "SKIP_", "RANDOM_", "COMMAND_", "MINIMUM_", "DEBUG_")):
            # Convert to lowercase with underscores
            settings_key = key.lower()
            
            # Try to convert to appropriate type
            if value.lower() in ("true", "false"):
                env_settings[settings_key] = value.lower() == "true"
            else:
                try:
                    env_settings[settings_key] = int(value)
                except ValueError:
                    env_settings[settings_key] = value
    
    return env_settings

# Modify the load_settings function to use the hardcoded defaults
def load_settings() -> Dict[str, Any]:
    """
    Load settings with the following priority:
    1. User-defined settings in the huntarr.json file
    2. Environment variables 
    3. Default settings for the selected app_type
    """
    try:
        # Start with default settings structure
        settings = dict(DEFAULT_SETTINGS)
        
        # Get environment variables
        env_settings = get_env_settings()
        
        # If we have an app_type, update the settings
        app_type = env_settings.get("app_type", "sonarr")
        settings["app_type"] = app_type
        
        # Load default configs for all apps
        supported_apps = ["sonarr", "radarr", "lidarr", "readarr"]
        for app in supported_apps:
            app_defaults = get_app_defaults(app)
            # Initialize app-specific settings
            if app not in settings:
                settings[app] = {}
            settings[app].update(app_defaults)
        
        # Apply environment settings to the current app type
        for key, value in env_settings.items():
            if key == "app_type":
                settings[key] = value
            else:
                # Put environment variables in the appropriate app section
                settings[app_type][key] = value
        
        # Use hardcoded defaults instead of trying to load from file
        default_configs = DEFAULT_CONFIGS
        
        # Finally, load user settings from file (highest priority)
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, 'r') as f:
                user_settings = json.load(f)
                # Deep merge user settings
                _deep_update(settings, user_settings)
                
                # Log API settings for debugging
                conn = user_settings.get("connections", {}).get(app_type, {})
                api_url = conn.get("api_url", "")
                has_api_key = bool(conn.get("api_key", ""))
                settings_logger.debug(f"Loaded settings from {SETTINGS_FILE}. API URL={api_url}, Has API Key: {has_api_key}")
        else:
            settings_logger.info(f"No settings file found at {SETTINGS_FILE}, creating with default values")
            save_settings(settings)
        
        return settings
    except Exception as e:
        settings_logger.error(f"Error loading settings: {e}")
        settings_logger.info("Using default settings due to error")
        return DEFAULT_CONFIGS.get(app_type, DEFAULT_CONFIGS["sonarr"])

def _deep_update(d, u):
    """Recursively update a dictionary without overwriting entire nested dicts"""
    for k, v in u.items():
        if isinstance(v, dict) and k in d and isinstance(d[k], dict):
            _deep_update(d[k], v)
        else:
            d[k] = v

def save_settings(settings: Dict[str, Any]) -> bool:
    """Save settings to the settings file."""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        settings_logger.info("Settings saved successfully")
        return True
    except Exception as e:
        settings_logger.error(f"Error saving settings: {e}")
        return False

def update_setting(category: str, key: str, value: Any) -> bool:
    """Update a specific setting value."""
    try:
        settings = load_settings()
        
        # Ensure category exists
        if category not in settings:
            settings[category] = {}
            
        # Update the value
        settings[category][key] = value
        
        # Save the updated settings
        return save_settings(settings)
    except Exception as e:
        settings_logger.error(f"Error updating setting {category}.{key}: {e}")
        return False

def get_setting(category: str, key: str, default: Any = None) -> Any:
    """Get a specific setting value."""
    try:
        settings = load_settings()
        return settings.get(category, {}).get(key, default)
    except Exception as e:
        settings_logger.error(f"Error getting setting {category}.{key}: {e}")
        return default

def get_all_settings() -> Dict[str, Any]:
    """Get all settings."""
    return load_settings()

def get_app_type() -> str:
    """Get the current app type"""
    settings = load_settings()
    return settings.get("app_type", "sonarr")

def get_api_key() -> str:
    """Get the API key from the connections section"""
    settings = load_settings()
    app_type = settings.get("app_type", "sonarr")
    return settings.get("connections", {}).get(app_type, {}).get("api_key", "")

def get_api_url() -> str:
    """Get the API URL from the connections section"""
    settings = load_settings()
    app_type = settings.get("app_type", "sonarr")
    return settings.get("connections", {}).get(app_type, {}).get("api_url", "")

# Initialize settings file if it doesn't exist
if not SETTINGS_FILE.exists():
    save_settings(load_settings())