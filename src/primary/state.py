#!/usr/bin/env python3
"""
State management module for Huntarr
Handles all persistence of program state
"""

import os
import datetime
import time
import json
from typing import List, Dict, Any, Optional
from src.primary.utils.logger import logger
from src.primary.config import STATE_RESET_INTERVAL_HOURS, APP_TYPE
from src.primary import settings_manager

# Create state directories based on app type
def get_state_file_path(app_type: str, state_type: str) -> str:
    """
    Get the path to a state file based on app type and state type.
    
    Args:
        app_type: The type of app (sonarr, radarr, etc.)
        state_type: The type of state file (e.g., processed_missing, processed_upgrades)
    
    Returns:
        The absolute path to the state file
    """
    if app_type == "sonarr":
        base_path = "/tmp/huntarr-state/sonarr"
    elif app_type == "radarr":
        base_path = "/tmp/huntarr-state/radarr"
    elif app_type == "lidarr":
        base_path = "/tmp/huntarr-state/lidarr"
    elif app_type == "readarr":
        base_path = "/tmp/huntarr-state/readarr"
    else:
        base_path = "/tmp/huntarr-state/unknown"
    
    # Ensure the directory exists
    os.makedirs(base_path, exist_ok=True)
    
    return f"{base_path}/{state_type}.json"

# Define state file paths based on the get_state_file_path function
PROCESSED_MISSING_FILE = get_state_file_path(APP_TYPE, "processed_missing")
PROCESSED_UPGRADES_FILE = get_state_file_path(APP_TYPE, "processed_upgrades")
LAST_RESET_FILE = get_state_file_path(APP_TYPE, "last_reset")

def get_last_reset_time(app_type: str = None) -> datetime.datetime:
    """
    Get the last time the state was reset for a specific app type.
    
    Args:
        app_type: The type of app to get last reset time for. If None, uses APP_TYPE.
        
    Returns:
        The datetime of the last reset, or a very old date if no reset has occurred.
    """
    current_app_type = app_type or APP_TYPE
    reset_file = get_state_file_path(current_app_type, "last_reset")
    
    try:
        if os.path.exists(reset_file):
            with open(reset_file, "r") as f:
                reset_time_str = f.read().strip()
                return datetime.datetime.fromisoformat(reset_time_str)
    except Exception as e:
        logger.error(f"Error reading last reset time for {current_app_type}: {e}")
    
    # Default to a very old date if no reset has occurred
    return datetime.datetime.fromtimestamp(0)

def set_last_reset_time(reset_time: datetime.datetime, app_type: str = None) -> None:
    """
    Set the last time the state was reset for a specific app type.
    
    Args:
        reset_time: The datetime to set
        app_type: The type of app to set last reset time for. If None, uses APP_TYPE.
    """
    current_app_type = app_type or APP_TYPE
    reset_file = get_state_file_path(current_app_type, "last_reset")
    
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(reset_file), exist_ok=True)
        with open(reset_file, "w") as f:
            f.write(reset_time.isoformat())
    except Exception as e:
        logger.error(f"Error writing last reset time for {current_app_type}: {e}")

def check_state_reset(app_type: str = None) -> bool:
    """
    Check if the state needs to be reset based on the reset interval.
    If it's time to reset, clears the processed IDs and updates the last reset time.
    
    Args:
        app_type: The type of app to check state reset for. If None, uses APP_TYPE.
        
    Returns:
        True if the state was reset, False otherwise.
    """
    current_app_type = app_type or APP_TYPE
    
    # Get reset interval from settings
    reset_interval = settings_manager.get_setting("huntarr", "state_reset_interval_hours", 168)
    
    last_reset = get_last_reset_time(current_app_type)
    now = datetime.datetime.now()
    
    # Calculate the time delta since the last reset
    delta = now - last_reset
    hours_passed = delta.total_seconds() / 3600
    
    # Reset if it's been longer than the reset interval
    if hours_passed >= reset_interval:
        logger.info(f"State files for {current_app_type} have not been reset in {hours_passed:.1f} hours. Resetting now.")
        
        # Clear processed IDs
        clear_processed_ids(current_app_type)
        
        # Update the last reset time
        set_last_reset_time(now, current_app_type)
        
        return True
    
    return False

def clear_processed_ids(app_type: str = None) -> None:
    """
    Clear all processed IDs for a specific app type.
    
    Args:
        app_type: The type of app to clear processed IDs for. If None, uses APP_TYPE.
    """
    current_app_type = app_type or APP_TYPE
    
    # Clear missing IDs
    missing_file = get_state_file_path(current_app_type, "processed_missing")
    try:
        if os.path.exists(missing_file):
            with open(missing_file, "w") as f:
                f.write("[]")
            logger.info(f"Cleared processed missing IDs for {current_app_type}")
    except Exception as e:
        logger.error(f"Error clearing processed missing IDs for {current_app_type}: {e}")
    
    # Clear upgrade IDs
    upgrades_file = get_state_file_path(current_app_type, "processed_upgrades")
    try:
        if os.path.exists(upgrades_file):
            with open(upgrades_file, "w") as f:
                f.write("[]")
            logger.info(f"Cleared processed upgrade IDs for {current_app_type}")
    except Exception as e:
        logger.error(f"Error clearing processed upgrade IDs for {current_app_type}: {e}")

def calculate_reset_time(app_type: str = None) -> str:
    """
    Calculate when the next state reset will occur.
    
    Args:
        app_type: The type of app to calculate reset time for. If None, uses APP_TYPE.
        
    Returns:
        A string representation of when the next reset will occur.
    """
    current_app_type = app_type or APP_TYPE
    
    # Get reset interval from settings
    reset_interval = settings_manager.get_setting("huntarr", "state_reset_interval_hours", 168)
    
    last_reset = get_last_reset_time(current_app_type)
    next_reset = last_reset + datetime.timedelta(hours=reset_interval)
    now = datetime.datetime.now()
    
    # If the next reset is in the past, it will reset in the next cycle
    if next_reset < now:
        return "Next reset: at the start of the next cycle"
    
    # Calculate time until next reset
    delta = next_reset - now
    hours = delta.total_seconds() / 3600
    
    if hours < 1:
        minutes = delta.total_seconds() / 60
        return f"Next reset: in {int(minutes)} minutes"
    elif hours < 24:
        return f"Next reset: in {int(hours)} hours"
    else:
        days = hours / 24
        return f"Next reset: in {int(days)} days"

def load_processed_ids(filepath: str) -> List[int]:
    """
    Load processed IDs from a file.
    
    Args:
        filepath: The path to the file
        
    Returns:
        A list of processed IDs
    """
    try:
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return json.load(f)
        return []
    except Exception as e:
        logger.error(f"Error loading processed IDs from {filepath}: {e}")
        return []

def save_processed_ids(filepath: str, ids: List[int]) -> None:
    """
    Save processed IDs to a file.
    
    Args:
        filepath: The path to the file
        ids: The list of IDs to save
    """
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(ids, f)
    except Exception as e:
        logger.error(f"Error saving processed IDs to {filepath}: {e}")

def save_processed_id(filepath: str, item_id: int) -> None:
    """
    Add a single ID to a processed IDs file.
    
    Args:
        filepath: The path to the file
        item_id: The ID to add
    """
    processed_ids = load_processed_ids(filepath)
    
    if item_id not in processed_ids:
        processed_ids.append(item_id)
        save_processed_ids(filepath, processed_ids)

def truncate_processed_list(filepath: str, max_items: int = 1000) -> None:
    """
    Truncate a processed IDs list to a maximum number of items.
    This helps prevent the file from growing too large over time.
    
    Args:
        filepath: The path to the file
        max_items: The maximum number of items to keep
    """
    processed_ids = load_processed_ids(filepath)
    
    if len(processed_ids) > max_items:
        # Keep only the most recent items (at the end of the list)
        processed_ids = processed_ids[-max_items:]
        save_processed_ids(filepath, processed_ids)
        logger.debug(f"Truncated {filepath} to {max_items} items")

# Initialize state files for all app types
def init_state_files() -> None:
    """Initialize state files for all app types"""
    app_types = ["sonarr", "radarr", "lidarr", "readarr"]
    
    for app_type in app_types:
        missing_file = get_state_file_path(app_type, "processed_missing")
        upgrades_file = get_state_file_path(app_type, "processed_upgrades")
        
        # Initialize the files if they don't exist
        for filepath in [missing_file, upgrades_file]:
            if not os.path.exists(filepath):
                save_processed_ids(filepath, [])

# Run initialization
init_state_files()