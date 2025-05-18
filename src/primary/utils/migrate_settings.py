#!/usr/bin/env python3
"""
Settings migration utility for Huntarr
Migrates settings from nested structure to flat structure
"""

import os
import json
import pathlib
import logging

# Create logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("settings_migration")

# Use the centralized path configuration
from src.primary.utils.config_paths import CONFIG_PATH

# Settings file path using cross-platform configuration
SETTINGS_DIR = CONFIG_PATH
SETTINGS_FILE = SETTINGS_DIR / "huntarr.json"

def migrate_settings():
    """Migrate settings from nested to flat structure"""
    logger.info("Starting settings migration...")
    
    if not SETTINGS_FILE.exists():
        logger.info(f"Settings file {SETTINGS_FILE} does not exist, nothing to migrate.")
        return
    
    try:
        # Read current settings
        with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
            settings = json.load(file)
            
        # Flag to track if changes were made
        changes_made = False
        
        # Check and migrate each app's settings
        for app in ["sonarr", "radarr", "lidarr", "readarr"]:
            if app in settings and "huntarr" in settings[app]:
                logger.info(f"Found nested huntarr section in {app}, migrating...")
                
                # Move all settings from app.huntarr to app level
                for key, value in settings[app]["huntarr"].items():
                    if key not in settings[app]:
                        settings[app][key] = value
                        logger.info(f"Moved {app}.huntarr.{key} to {app}.{key}")
                
                # Remove the huntarr section
                del settings[app]["huntarr"]
                logger.info(f"Removed {app}.huntarr section")
                changes_made = True
            
            # Check for advanced section
            if app in settings and "advanced" in settings[app]:
                logger.info(f"Found advanced section in {app}, migrating...")
                
                # Move all settings from app.advanced to app level
                for key, value in settings[app]["advanced"].items():
                    if key not in settings[app]:
                        settings[app][key] = value
                        logger.info(f"Moved {app}.advanced.{key} to {app}.{key}")
                
                # Remove the advanced section
                del settings[app]["advanced"]
                logger.info(f"Removed {app}.advanced section")
                changes_made = True
        
        # Save changes if needed
        if changes_made:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
                json.dump(settings, file, indent=2)
            logger.info("Settings migration completed successfully.")
        else:
            logger.info("No changes needed, settings are already in the correct format.")
    
    except Exception as e:
        logger.error(f"Error migrating settings: {e}")

if __name__ == "__main__":
    migrate_settings()
