#!/usr/bin/env python3
"""
Stateful Manager for Huntarr
Handles storing and retrieving processed media IDs to prevent reprocessing
"""

import os
import json
import time
import pathlib
import datetime
import logging
from typing import Dict, Any, List, Optional, Set

# Create logger for stateful_manager
stateful_logger = logging.getLogger("stateful_manager")

# Constants
STATEFUL_DIR = pathlib.Path(os.getenv("STATEFUL_DIR", "/config/stateful"))
LOCK_FILE = STATEFUL_DIR / "lock.json"
DEFAULT_HOURS = 168  # Default 7 days (168 hours)

# Ensure the stateful directory exists
try:
    STATEFUL_DIR.mkdir(parents=True, exist_ok=True)
    stateful_logger.info(f"Stateful directory created/confirmed at {STATEFUL_DIR}")
except Exception as e:
    stateful_logger.error(f"Error creating stateful directory: {e}")

# Create app directories
APP_TYPES = ["sonarr", "radarr", "lidarr", "readarr", "whisparr"]
for app_type in APP_TYPES:
    (STATEFUL_DIR / app_type).mkdir(exist_ok=True)

# Add import for get_advanced_setting
from src.primary.settings_manager import get_advanced_setting

def initialize_lock_file() -> None:
    """Initialize the lock file with the current timestamp if it doesn't exist."""
    # Ensure directory exists - we don't need to log this again
    try:
        STATEFUL_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        stateful_logger.error(f"Error creating stateful directory: {e}")
        
    if not LOCK_FILE.exists():
        try:
            current_time = int(time.time())
            # Get the expiration hours setting
            expiration_hours = get_advanced_setting("statefulExpirationHours", DEFAULT_HOURS)
            
            expires_at = current_time + (expiration_hours * 3600)
            
            with open(LOCK_FILE, 'w') as f:
                json.dump({
                    "created_at": current_time,
                    "expires_at": expires_at
                }, f, indent=2)
            stateful_logger.info(f"Initialized lock file at {LOCK_FILE} with expiration in {expiration_hours} hours")
        except Exception as e:
            stateful_logger.error(f"Error initializing lock file: {e}")
            
def get_lock_info() -> Dict[str, Any]:
    """Get the current lock information."""
    initialize_lock_file()
    try:
        with open(LOCK_FILE, 'r') as f:
            lock_info = json.load(f)
        
        # Validate the structure and ensure required fields exist
        if not isinstance(lock_info, dict):
            raise ValueError("Lock info is not a dictionary")
            
        if "created_at" not in lock_info:
            lock_info["created_at"] = int(time.time())
            
        if "expires_at" not in lock_info or lock_info["expires_at"] is None:
            # Recalculate expiration if missing
            expiration_hours = get_advanced_setting("statefulExpirationHours", DEFAULT_HOURS)
            lock_info["expires_at"] = lock_info["created_at"] + (expiration_hours * 3600)
            
            # Save the updated info
            with open(LOCK_FILE, 'w') as f:
                json.dump(lock_info, f, indent=2)
            
        return lock_info
    except Exception as e:
        stateful_logger.error(f"Error reading lock file: {e}")
        # Return default values if there's an error
        current_time = int(time.time())
        expiration_hours = get_advanced_setting("statefulExpirationHours", DEFAULT_HOURS)
        expires_at = current_time + (expiration_hours * 3600)
        
        return {
            "created_at": current_time,
            "expires_at": expires_at
        }

def update_lock_expiration(hours: int = None) -> None:
    """Update the lock expiration based on the hours setting."""
    if hours is None:
        expiration_hours = get_advanced_setting("statefulExpirationHours", DEFAULT_HOURS)
    
    lock_info = get_lock_info()
    created_at = lock_info.get("created_at", int(time.time()))
    expires_at = created_at + (expiration_hours * 3600)
    
    lock_info["expires_at"] = expires_at
    
    try:
        with open(LOCK_FILE, 'w') as f:
            json.dump(lock_info, f, indent=2)
        stateful_logger.info(f"Updated lock expiration to {datetime.datetime.fromtimestamp(expires_at)}")
    except Exception as e:
        stateful_logger.error(f"Error updating lock expiration: {e}")

def reset_stateful_management() -> bool:
    """
    Reset the stateful management system.

    This involves:
    1. Creating a new lock file with the current timestamp and a calculated expiration time
       based on the 'stateful_management_hours' setting.
    2. Deleting all stored processed ID files (*.json) within each app-specific
       subdirectory under the STATEFUL_DIR.

    Returns:
        bool: True if the reset was successful, False otherwise.
    """
    try:
        # Get the expiration hours setting BEFORE writing the lock file
        expiration_hours = get_advanced_setting("statefulExpirationHours", DEFAULT_HOURS)
        
        # Create new lock file with calculated expiration
        current_time = int(time.time())
        expires_at = current_time + (expiration_hours * 3600)
        
        with open(LOCK_FILE, 'w') as f:
            json.dump({
                "created_at": current_time,
                "expires_at": expires_at # Write the calculated expiration time directly
            }, f, indent=2)
        
        # Delete all stored IDs
        for app_type in APP_TYPES:
            app_dir = STATEFUL_DIR / app_type
            if app_dir.exists():
                for json_file in app_dir.glob("*.json"):
                    try:
                        json_file.unlink()
                        stateful_logger.debug(f"Deleted {json_file}")
                    except Exception as e:
                        stateful_logger.error(f"Error deleting {json_file}: {e}")
        
        # No need to call update_lock_expiration() again as we wrote it directly
        stateful_logger.info(f"Successfully reset stateful management. New expiration: {datetime.datetime.fromtimestamp(expires_at)}")
        return True
    except Exception as e:
        stateful_logger.error(f"Error resetting stateful management: {e}")
        return False

def check_expiration() -> bool:
    """
    Check if the stateful management has expired.
    
    Returns:
        bool: True if expired, False otherwise
    """
    lock_info = get_lock_info()
    expires_at = lock_info.get("expires_at")
    
    # If expires_at is None, update it based on settings
    if expires_at is None:
        update_lock_expiration()
        lock_info = get_lock_info()
        expires_at = lock_info.get("expires_at")
    
    current_time = int(time.time())
    
    if current_time >= expires_at:
        stateful_logger.info("Stateful management has expired, resetting...")
        reset_stateful_management()
        return True
    
    return False

def get_processed_ids(app_type: str, instance_name: str) -> Set[str]:
    """
    Get the set of processed media IDs for a specific app instance.
    
    Args:
        app_type: The type of app (sonarr, radarr, etc.)
        instance_name: The name of the instance
        
    Returns:
        Set[str]: Set of processed media IDs
    """
    if app_type not in APP_TYPES:
        stateful_logger.warning(f"Unknown app type: {app_type}")
        return set()
    
    # Create safe filename from instance name
    safe_instance_name = "".join([c if c.isalnum() else "_" for c in instance_name])
    
    file_path = STATEFUL_DIR / app_type / f"{safe_instance_name}.json"
    stateful_logger.debug(f"[get_processed_ids] Checking file: {file_path} for {app_type}/{instance_name}") # DEBUG LOG
    
    if not file_path.exists():
        stateful_logger.debug(f"[get_processed_ids] File not found: {file_path}") # DEBUG LOG
        return set()
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            processed_ids_set = set(data.get("processed_ids", [])) # Convert list to set
            stateful_logger.debug(f"[get_processed_ids] Read {len(processed_ids_set)} IDs from {file_path}: {processed_ids_set}") # DEBUG LOG
            return processed_ids_set
    except Exception as e:
        stateful_logger.error(f"Error reading processed IDs for {instance_name} from {file_path}: {e}") # Updated log
        return set()

def add_processed_id(app_type: str, instance_name: str, media_id: str) -> bool:
    """
    Add a media ID to the processed list for a specific app instance.
    
    Args:
        app_type: The type of app (sonarr, radarr, etc.)
        instance_name: The name of the instance
        media_id: The ID of the processed media
        
    Returns:
        bool: True if successful, False otherwise
    """
    if app_type not in APP_TYPES:
        stateful_logger.warning(f"Unknown app type: {app_type}")
        return False
    
    # Create safe filename from instance name
    safe_instance_name = "".join([c if c.isalnum() else "_" for c in instance_name])
    
    file_path = STATEFUL_DIR / app_type / f"{safe_instance_name}.json"
    
    # Get existing processed IDs using the get function (which includes logging)
    current_processed_ids_set = get_processed_ids(app_type, instance_name)
    
    # Convert set back to list for appending and saving
    processed_ids_list = list(current_processed_ids_set)
    
    # Add the new ID if it's not already there
    if media_id not in current_processed_ids_set:
        processed_ids_list.append(media_id)
        stateful_logger.debug(f"[add_processed_id] Adding ID {media_id} to list for {app_type}/{instance_name}") # DEBUG LOG
    else:
        stateful_logger.debug(f"[add_processed_id] ID {media_id} already in list for {app_type}/{instance_name}") # DEBUG LOG
        # No need to write if the ID is already present
        return True
        
    # Write the updated list back to the file
    stateful_logger.debug(f"[add_processed_id] Writing {len(processed_ids_list)} IDs to {file_path}: {processed_ids_list}") # DEBUG LOG
    try:
        with open(file_path, 'w') as f:
            json.dump({
                "processed_ids": processed_ids_list,
                "last_updated": int(time.time())
            }, f, indent=2)
        # Removed redundant log here, previous debug log is sufficient
        return True
    except Exception as e:
        stateful_logger.error(f"Error adding media ID {media_id} to {file_path}: {e}")
        return False

def is_processed(app_type: str, instance_name: str, media_id: str) -> bool:
    """
    Check if a media ID has already been processed.
    
    Args:
        app_type: The type of app (sonarr, radarr, etc.)
        instance_name: The name of the instance
        media_id: The ID of the media to check
        
    Returns:
        bool: True if already processed, False otherwise
    """
    # Create safe filename for logging
    safe_instance = "".join([c if c.isalnum() else "_" for c in instance_name])
    file_path = STATEFUL_DIR / app_type / f"{safe_instance}.json"
    
    # Get processed IDs for this app/instance
    processed_ids = get_processed_ids(app_type, instance_name)
    
    # Log what we're checking and the result
    # Converting media_id to string since some callers might pass an integer
    media_id_str = str(media_id)
    is_in_set = media_id_str in processed_ids
    
    stateful_logger.info(f"is_processed check: {app_type}/{instance_name}, ID:{media_id_str}, Found:{is_in_set}, File:{file_path}, Total IDs:{len(processed_ids)}")
    
    return is_in_set

def get_stateful_management_info() -> Dict[str, Any]:
    """Get information about the stateful management system."""
    lock_info = get_lock_info()
    created_at_ts = lock_info.get("created_at")
    expires_at_ts = lock_info.get("expires_at")
    
    # Get the interval setting
    expiration_hours = get_advanced_setting("statefulExpirationHours", DEFAULT_HOURS)

    return {
        "created_at_ts": created_at_ts,
        "expires_at_ts": expires_at_ts,
        "interval_hours": expiration_hours
    }

def initialize_stateful_system():
    """Perform a complete initialization of the stateful management system."""
    stateful_logger.info("Initializing stateful management system")
    
    # Ensure all required directories exist
    try:
        STATEFUL_DIR.mkdir(parents=True, exist_ok=True)
        for app_type in APP_TYPES:
            (STATEFUL_DIR / app_type).mkdir(exist_ok=True)
        stateful_logger.info(f"Stateful directory structure created at {STATEFUL_DIR}")
    except Exception as e:
        stateful_logger.error(f"Failed to create stateful directories: {e}")
    
    # Initialize the lock file with proper expiration
    try:
        initialize_lock_file()
        # Update expiration time
        expiration_hours = get_advanced_setting("statefulExpirationHours", DEFAULT_HOURS)
        update_lock_expiration(expiration_hours)
        stateful_logger.info(f"Stateful lock file initialized with {expiration_hours} hour expiration")
    except Exception as e:
        stateful_logger.error(f"Failed to initialize lock file: {e}")
    
    # Check for existing processed IDs
    try:
        total_ids = 0
        for app_type in APP_TYPES:
            app_dir = STATEFUL_DIR / app_type
            if app_dir.exists():
                files = list(app_dir.glob("*.json"))
                total_ids += len(files)
        
        if total_ids > 0:
            stateful_logger.info(f"Found {total_ids} existing processed ID files")
        else:
            stateful_logger.info("No existing processed ID files found")
    except Exception as e:
        stateful_logger.error(f"Failed to check for existing processed IDs: {e}")
    
    stateful_logger.info("Stateful management system initialization complete")

# Initialize the stateful system on module import
initialize_stateful_system()
