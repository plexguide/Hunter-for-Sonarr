#!/usr/bin/env python3
"""
Settings manager for Huntarr-Sonarr - Simplified to remove JSON dependency
Now only handles theme setting in memory
"""

import logging

# Create a simple logger for settings_manager
logging.basicConfig(level=logging.INFO)
settings_logger = logging.getLogger("settings_manager")

# In-memory settings storage (only for theme)
MEMORY_SETTINGS = {
    "ui": {
        "dark_mode": True
    }
}

def get_setting(section, key, default=None):
    """Get a setting value from memory"""
    try:
        return MEMORY_SETTINGS.get(section, {}).get(key, default)
    except Exception as e:
        settings_logger.error(f"Error getting setting {section}.{key}: {str(e)}")
        return default

def update_setting(section, key, value):
    """Update a setting value in memory"""
    try:
        if section not in MEMORY_SETTINGS:
            MEMORY_SETTINGS[section] = {}
        MEMORY_SETTINGS[section][key] = value
        return True
    except Exception as e:
        settings_logger.error(f"Error updating setting {section}.{key}: {str(e)}")
        return False

def get_all_settings():
    """Get all settings as a dictionary"""
    return MEMORY_SETTINGS