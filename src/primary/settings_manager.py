#!/usr/bin/env python3
"""
Settings manager for Huntarr
Handles loading, saving, and providing settings from individual JSON files per app
Supports default configurations for different Arr applications
"""

import os
import json
import pathlib
import logging
import shutil
from typing import Dict, Any, Optional, List

# Create a simple logger for settings_manager
logging.basicConfig(level=logging.INFO)
settings_logger = logging.getLogger("settings_manager")

# Settings directory setup - Root config directory
SETTINGS_DIR = pathlib.Path("/config")
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

# Default configs location remains the same
DEFAULT_CONFIGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'default_configs'))

# List of known application types based on default config files
KNOWN_APP_TYPES = [f.stem for f in pathlib.Path(DEFAULT_CONFIGS_DIR).glob("*.json")]

def get_settings_file_path(app_name: str) -> pathlib.Path:
    """Get the path to the settings file for a specific app."""
    if app_name not in KNOWN_APP_TYPES:
        # Log a warning but allow for potential future app types
        settings_logger.warning(f"Requested settings file for unknown app type: {app_name}")
    return SETTINGS_DIR / f"{app_name}.json"

def get_default_config_path(app_name: str) -> pathlib.Path:
    """Get the path to the default config file for a specific app."""
    return pathlib.Path(DEFAULT_CONFIGS_DIR) / f"{app_name}.json"

# Helper function to load default settings for a specific app
def load_default_app_settings(app_name: str) -> Dict[str, Any]:
    """Load default settings for a specific app from its JSON file."""
    default_file = get_default_config_path(app_name)
    if default_file.exists():
        try:
            with open(default_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            settings_logger.error(f"Error loading default settings for {app_name} from {default_file}: {e}")
            return {}
    else:
        settings_logger.warning(f"Default settings file not found for {app_name}: {default_file}")
        return {}

def _ensure_config_exists(app_name: str) -> None:
    """Ensure the config file exists for an app, copying from default if not."""
    settings_file = get_settings_file_path(app_name)
    if not settings_file.exists():
        default_file = get_default_config_path(app_name)
        if default_file.exists():
            try:
                shutil.copyfile(default_file, settings_file)
                settings_logger.info(f"Created default settings file for {app_name} at {settings_file}")
            except Exception as e:
                settings_logger.error(f"Error copying default settings for {app_name}: {e}")
        else:
            # Create an empty file if no default exists
            settings_logger.warning(f"No default config found for {app_name}. Creating empty settings file.")
            try:
                with open(settings_file, 'w') as f:
                    json.dump({}, f)
            except Exception as e:
                settings_logger.error(f"Error creating empty settings file for {app_name}: {e}")


def load_settings(app_name: str) -> Dict[str, Any]:
    """Load settings for a specific app."""
    if app_name not in KNOWN_APP_TYPES:
        settings_logger.error(f"Attempted to load settings for unknown app type: {app_name}")
        return {}
        
    _ensure_config_exists(app_name)
    settings_file = get_settings_file_path(app_name)
    try:
        with open(settings_file, 'r') as f:
            # Load existing settings
            current_settings = json.load(f)
            
            # Load defaults to check for missing keys
            default_settings = load_default_app_settings(app_name)
            
            # Add missing keys from defaults without overwriting existing values
            updated = False
            for key, value in default_settings.items():
                if key not in current_settings:
                    current_settings[key] = value
                    updated = True
            
            # If keys were added, save the updated file
            if updated:
                settings_logger.info(f"Added missing default keys to {app_name}.json")
                save_settings(app_name, current_settings) # Use save_settings to handle writing
                
            return current_settings
            
    except json.JSONDecodeError:
        settings_logger.error(f"Error decoding JSON from {settings_file}. Restoring from default.")
        # Attempt to restore from default
        default_settings = load_default_app_settings(app_name)
        save_settings(app_name, default_settings) # Save the restored defaults
        return default_settings
    except Exception as e:
        settings_logger.error(f"Error loading settings for {app_name} from {settings_file}: {e}")
        return {} # Return empty dict on other errors


def save_settings(app_name: str, settings_data: Dict[str, Any]) -> bool:
    """Save settings for a specific app."""
    if app_name not in KNOWN_APP_TYPES:
         settings_logger.error(f"Attempted to save settings for unknown app type: {app_name}")
         return False
         
    settings_file = get_settings_file_path(app_name)
    try:
        # Ensure the directory exists (though it should from the top-level check)
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load current settings to merge, preserving any keys not included in settings_data
        # This might be needed if the frontend only sends partial updates, though current
        # frontend seems to send the full section. Let's assume full updates for now.
        # current_settings = load_settings(app_name) # Avoid recursion
        # merged_settings = {**current_settings, **settings_data}

        # Write the provided settings data directly
        with open(settings_file, 'w') as f:
            json.dump(settings_data, f, indent=2)
        settings_logger.info(f"Settings saved successfully for {app_name} to {settings_file}")
        return True
    except Exception as e:
        settings_logger.error(f"Error saving settings for {app_name} to {settings_file}: {e}")
        return False

def get_setting(app_name: str, key: str, default: Optional[Any] = None) -> Any:
    """Get a specific setting value for an app."""
    settings = load_settings(app_name)
    return settings.get(key, default)

def get_api_url(app_name: str) -> Optional[str]:
    """Get the API URL for a specific app."""
    return get_setting(app_name, "api_url", "")

def get_api_key(app_name: str) -> Optional[str]:
    """Get the API Key for a specific app."""
    return get_setting(app_name, "api_key", "")

def get_all_settings() -> Dict[str, Dict[str, Any]]:
    """Load settings for all known apps."""
    all_settings = {}
    for app_name in KNOWN_APP_TYPES:
        # Only include apps if their config file exists or can be created from defaults
        # Effectively, load_settings ensures the file exists and loads it.
        settings = load_settings(app_name)
        if settings: # Only add if settings were successfully loaded
             all_settings[app_name] = settings
    return all_settings

def get_configured_apps() -> List[str]:
    """Return a list of app names that have basic configuration (API URL and Key)."""
    configured = []
    for app_name in KNOWN_APP_TYPES:
        settings = load_settings(app_name)
        # Check if essential keys exist and have non-empty values
        if settings.get("api_url") and settings.get("api_key"):
            configured.append(app_name)
    return configured

# Removed get_app_type() as it's no longer relevant in this manager
# Removed get_all_default_settings() as load_settings handles defaults per app

# Example usage (for testing purposes, remove later)
if __name__ == "__main__":
    settings_logger.info(f"Known app types: {KNOWN_APP_TYPES}")
    
    # Ensure defaults are copied if needed
    for app in KNOWN_APP_TYPES:
        _ensure_config_exists(app)

    # Test loading Sonarr settings
    sonarr_settings = load_settings("sonarr")
    settings_logger.info(f"Loaded Sonarr settings: {json.dumps(sonarr_settings, indent=2)}")

    # Test getting a specific setting
    sonarr_sleep = get_setting("sonarr", "sleep_duration", 999)
    settings_logger.info(f"Sonarr sleep duration: {sonarr_sleep}")

    # Test saving updated settings (example)
    if sonarr_settings:
        sonarr_settings["sleep_duration"] = 850
        save_settings("sonarr", sonarr_settings)
        reloaded_sonarr_settings = load_settings("sonarr")
        settings_logger.info(f"Reloaded Sonarr settings after save: {json.dumps(reloaded_sonarr_settings, indent=2)}")


    # Test getting all settings
    all_app_settings = get_all_settings()
    settings_logger.info(f"All loaded settings: {json.dumps(all_app_settings, indent=2)}")

    # Test getting configured apps
    configured_list = get_configured_apps()
    settings_logger.info(f"Configured apps: {configured_list}")