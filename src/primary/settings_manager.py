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
import subprocess
import time
from typing import Dict, Any, Optional, List

# Create a simple logger for settings_manager
logging.basicConfig(level=logging.INFO)
settings_logger = logging.getLogger("settings_manager")

# Settings directory setup - Root config directory
# Use the centralized path configuration
from src.primary.utils.config_paths import SETTINGS_DIR

# Settings directory is already created by config_paths module

# Default configs location remains the same
DEFAULT_CONFIGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'default_configs'))

# Update or add this as a class attribute or constant
KNOWN_APP_TYPES = ["sonarr", "radarr", "lidarr", "readarr", "whisparr", "eros", "swaparr", "general"]

# Add a settings cache with timestamps to avoid excessive disk reads
settings_cache = {}  # Format: {app_name: {'timestamp': timestamp, 'data': settings_dict}}
CACHE_TTL = 5  # Cache time-to-live in seconds

def clear_cache(app_name=None):
    """Clear the settings cache for a specific app or all apps."""
    global settings_cache
    if app_name:
        if app_name in settings_cache:
            settings_logger.debug(f"Clearing cache for {app_name}")
            settings_cache.pop(app_name, None)
    else:
        settings_logger.debug("Clearing entire settings cache")
        settings_cache = {}

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


def load_settings(app_type, use_cache=True):
    """
    Load settings for a specific app type
    
    Args:
        app_type: The app type to load settings for
        use_cache: Whether to use the cached settings if available and recent
        
    Returns:
        Dict containing the app settings
    """
    global settings_cache
    
    # Only log unexpected app types that are not 'general'
    if app_type not in KNOWN_APP_TYPES and app_type != "general":
        settings_logger.warning(f"load_settings called with unexpected app_type: {app_type}")
    
    # Check if we have a valid cache entry
    if use_cache and app_type in settings_cache:
        cache_entry = settings_cache[app_type]
        cache_age = time.time() - cache_entry.get('timestamp', 0)
        
        if cache_age < CACHE_TTL:
            settings_logger.debug(f"Using cached settings for {app_type} (age: {cache_age:.1f}s)")
            return cache_entry['data']
        else:
            settings_logger.debug(f"Cache expired for {app_type} (age: {cache_age:.1f}s)")
    
    # No valid cache entry, load from disk
    _ensure_config_exists(app_type)
    settings_file = get_settings_file_path(app_type)
    try:
        with open(settings_file, 'r') as f:
            # Load existing settings
            current_settings = json.load(f)
            
            # Load defaults to check for missing keys
            default_settings = load_default_app_settings(app_type)
            
            # Add missing keys from defaults without overwriting existing values
            updated = False
            for key, value in default_settings.items():
                if key not in current_settings:
                    current_settings[key] = value
                    updated = True
            
            # Apply Lidarr migration (artist -> album) for Huntarr 7.5.0+
            if app_type == "lidarr":
                if current_settings.get("hunt_missing_mode") == "artist":
                    settings_logger.info("Migrating Lidarr hunt_missing_mode from 'artist' to 'album' (Huntarr 7.5.0+)")
                    current_settings["hunt_missing_mode"] = "album"
                    updated = True
            
            # If keys were added, save the updated file
            if updated:
                settings_logger.info(f"Added missing default keys to {app_type}.json")
                save_settings(app_type, current_settings) # Use save_settings to handle writing
            
            # Update cache
            settings_cache[app_type] = {
                'timestamp': time.time(),
                'data': current_settings
            }
                
            return current_settings
            
    except json.JSONDecodeError:
        settings_logger.error(f"Error decoding JSON from {settings_file}. Restoring from default.")
        # Attempt to restore from default
        default_settings = load_default_app_settings(app_type)
        save_settings(app_type, default_settings) # Save the restored defaults
        
        # Update cache with defaults
        settings_cache[app_type] = {
            'timestamp': time.time(),
            'data': default_settings
        }
        
        return default_settings
    except Exception as e:
        settings_logger.error(f"Error loading settings for {app_type} from {settings_file}: {e}")
        return {} # Return empty dict on other errors


def save_settings(app_name: str, settings_data: Dict[str, Any]) -> bool:
    """Save settings for a specific app."""
    if app_name not in KNOWN_APP_TYPES:
         settings_logger.error(f"Attempted to save settings for unknown app type: {app_name}")
         return False
    
    # Debug: Log the data being saved, especially for general settings
    if app_name == 'general':
        settings_logger.info(f"Saving general settings: {settings_data}")
        settings_logger.info(f"Apprise URLs being saved: {settings_data.get('apprise_urls', 'NOT_FOUND')}")
         
    settings_file = get_settings_file_path(app_name)
    try:
        # Ensure the directory exists (though it should from the top-level check)
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the provided settings data directly
        with open(settings_file, 'w') as f:
            json.dump(settings_data, f, indent=2)
        settings_logger.info(f"Settings saved successfully for {app_name} to {settings_file}")
        
        # Clear cache for this app to ensure fresh reads
        clear_cache(app_name)
        
        # If general settings were saved, also clear timezone cache
        if app_name == 'general':
            try:
                from src.primary.utils.timezone_utils import clear_timezone_cache
                clear_timezone_cache()
                settings_logger.debug("Timezone cache cleared after general settings save")
            except Exception as e:
                settings_logger.warning(f"Failed to clear timezone cache: {e}")
        
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
        
        # First check if there are valid instances configured (multi-instance mode)
        if "instances" in settings and isinstance(settings["instances"], list) and settings["instances"]:
            for instance in settings["instances"]:
                if instance.get("enabled", True) and instance.get("api_url") and instance.get("api_key"):
                    configured.append(app_name)
                    break  # One valid instance is enough to consider the app configured
            continue  # Skip the single-instance check if we already checked instances
                
        # Fallback to legacy single-instance config
        if settings.get("api_url") and settings.get("api_key"):
            configured.append(app_name)
    
    settings_logger.info(f"Configured apps: {configured}")
    return configured

def apply_timezone(timezone: str) -> bool:
    """Apply the specified timezone to the container.
    
    Args:
        timezone: The timezone to set (e.g., 'UTC', 'America/New_York')
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Set TZ environment variable
        os.environ['TZ'] = timezone
        
        # Create symlink for localtime (common approach in containers)
        zoneinfo_path = f"/usr/share/zoneinfo/{timezone}"
        if os.path.exists(zoneinfo_path):
            # Remove existing symlink if it exists
            if os.path.exists("/etc/localtime"):
                os.remove("/etc/localtime")
            
            # Create new symlink
            os.symlink(zoneinfo_path, "/etc/localtime")
            
            # Also update /etc/timezone file if it exists
            with open("/etc/timezone", "w") as f:
                f.write(f"{timezone}\n")
                
            settings_logger.info(f"Timezone set to {timezone}")
            return True
        else:
            settings_logger.error(f"Timezone file not found: {zoneinfo_path}")
            return False
    except Exception as e:
        settings_logger.error(f"Error setting timezone: {str(e)}")
        return False

def initialize_timezone_from_env():
    """Initialize timezone setting from TZ environment variable if not already set."""
    try:
        # Get the TZ environment variable
        tz_env = os.environ.get('TZ')
        if not tz_env:
            settings_logger.info("No TZ environment variable found, using default UTC")
            return
        
        # Load current general settings
        general_settings = load_settings("general")
        current_timezone = general_settings.get("timezone")
        
        # If timezone is not set in settings, initialize it from TZ environment variable
        if not current_timezone or current_timezone == "UTC":
            settings_logger.info(f"Initializing timezone from TZ environment variable: {tz_env}")
            
            # Validate the timezone
            try:
                import pytz
                pytz.timezone(tz_env)  # This will raise an exception if invalid
                
                # Update the settings
                general_settings["timezone"] = tz_env
                save_settings("general", general_settings)
                
                # Apply the timezone to the system
                apply_timezone(tz_env)
                
                settings_logger.info(f"Successfully initialized timezone to {tz_env}")
                
            except pytz.UnknownTimeZoneError:
                settings_logger.warning(f"Invalid timezone in TZ environment variable: {tz_env}, keeping UTC")
            except Exception as e:
                settings_logger.error(f"Error validating timezone {tz_env}: {e}")
        else:
            settings_logger.info(f"Timezone already set in settings: {current_timezone}")
            
    except Exception as e:
        settings_logger.error(f"Error initializing timezone from environment: {e}")

# Add a list of known advanced settings for clarity and documentation
ADVANCED_SETTINGS = [
    "api_timeout", 
    "command_wait_delay", 
    "command_wait_attempts", 
    "minimum_download_queue_size",
    "log_refresh_interval_seconds",
    "stateful_management_hours",
    "hourly_cap",
    "ssl_verify",  # Add SSL verification setting
    "base_url"     # Add base URL setting
]

def get_advanced_setting(setting_name, default_value=None):
    """
    Get an advanced setting from general settings.
    
    Advanced settings are now centralized in general settings and no longer stored
    in individual app settings files. This function provides a consistent way to
    access these settings from anywhere in the codebase.
    
    Args:
        setting_name: The name of the advanced setting to retrieve
        default_value: The default value to return if the setting is not found
        
    Returns:
        The value of the setting or the default value if not found
    """
    if setting_name not in ADVANCED_SETTINGS:
        settings_logger.warning(f"Requested unknown advanced setting: {setting_name}")
    
    # Get from general settings
    general_settings = load_settings('general', use_cache=True)
    return general_settings.get(setting_name, default_value)

def get_ssl_verify_setting():
    """
    Get the SSL verification setting.
    
    Returns:
        bool: True if SSL verification should be enabled (default), False otherwise
    """
    return get_advanced_setting("ssl_verify", True)

def get_custom_tag(app_name: str, tag_type: str, default: str) -> str:
    """
    Get a custom tag for an app and tag type.
    
    Args:
        app_name: The app name (sonarr, radarr, etc.)
        tag_type: The tag type (missing, upgrade, shows_missing)
        default: Default tag if custom tag not found
        
    Returns:
        The custom tag string
    """
    settings = load_settings(app_name)
    custom_tags = settings.get('custom_tags', {})
    tag = custom_tags.get(tag_type, default)
    
    # Validate tag length (max 25 characters as per UI)
    if len(tag) > 25:
        settings_logger.warning(f"Custom tag '{tag}' for {app_name}.{tag_type} exceeds 25 characters, truncating")
        tag = tag[:25]
    
    return tag

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