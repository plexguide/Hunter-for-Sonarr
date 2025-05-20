#!/usr/bin/env python3
"""
Huntarr Configuration Migration Script

This module is responsible for migrating legacy JSON configuration files 
from the root config directory to the settings subdirectory
"""

import os
import shutil
import logging
import pathlib

# Get the logger
logger = logging.getLogger('huntarr')

# Import config paths
from src.primary.utils.config_paths import CONFIG_PATH, SETTINGS_DIR

def migrate_json_configs():
    """
    Migrates JSON configuration files from old location to new settings directory.
    
    Looks for specific JSON configuration files in the root config directory and moves them
    to the settings subdirectory if they exist.
    """
    # Define the source and destination directories using platform-compatible paths
    source_dir = CONFIG_PATH
    dest_dir = SETTINGS_DIR
    
    # List of JSON files to look for and migrate
    json_files = [
        "eros.json", 
        "lidarr.json", 
        "readarr.json", 
        "swaparr.json", 
        "general.json", 
        "radarr.json", 
        "sonarr.json", 
        "whisparr.json"
    ]
    
    # Flag to track if any files were migrated
    files_migrated = False
    
    # Check if the source directory exists
    if not os.path.isdir(source_dir):
        logger.info(f"Source directory {source_dir} not found - skipping JSON configuration migration")
        return False
    
    # Ensure the destination directory exists
    if not os.path.isdir(dest_dir):
        logger.info(f"Creating settings directory at {dest_dir}")
        try:
            os.makedirs(dest_dir, exist_ok=True)
            # Set directory permissions to 755
            os.chmod(dest_dir, 0o755)
        except Exception as e:
            logger.error(f"Failed to create settings directory: {e}")
            return False
    
    logger.info("Checking for configuration files to migrate")
    
    # Process each JSON file
    for json_file in json_files:
        source_file = os.path.join(source_dir, json_file)
        dest_file = os.path.join(dest_dir, json_file)
        
        # Check if the file exists in the old location
        if os.path.isfile(source_file):
            logger.info(f"Found {json_file} in old location, migrating...")
            files_migrated = True
            
            try:
                # Copy the file to the new location
                shutil.copy2(source_file, dest_file)
                logger.info(f"Successfully migrated {json_file}")
                
                # Set file permissions to 644
                os.chmod(dest_file, 0o644)
                
                # Remove the original file
                os.remove(source_file)
                logger.info(f"Removed original {json_file}")
            except Exception as e:
                logger.error(f"Error migrating {json_file}: {e}")
    
    # Report results
    if files_migrated:
        logger.info("Configuration migration completed successfully")
    else:
        logger.info("No legacy configuration files found")
    
    return files_migrated

if __name__ == "__main__":
    # Setup basic logging if run directly
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    # Run migration
    migrate_json_configs()
