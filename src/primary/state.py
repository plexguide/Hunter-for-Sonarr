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
    if not app_type:
        logger.error("get_state_file_path called without an app_type.")
        return "/config/state/unknown/error.json" 
        
    if app_type == "sonarr":
        base_path = "/config/state/sonarr"
    elif app_type == "radarr":
        base_path = "/config/state/radarr"
    elif app_type == "lidarr":
        base_path = "/config/state/lidarr"
    elif app_type == "readarr":
        base_path = "/config/state/readarr"
    elif app_type == "whisparr":
        base_path = "/config/state/whisparr"
    else:
        logger.warning(f"get_state_file_path called with unexpected app_type: {app_type}")
        base_path = f"/config/state/{app_type}"
    
    os.makedirs(base_path, exist_ok=True)
    
    return f"{base_path}/{state_type}.json"

def get_last_reset_time(app_type: str = None) -> datetime.datetime:
    """
    Get the last time the state was reset for a specific app type.
    
    Args:
        app_type: The type of app to get last reset time for.
        
    Returns:
        The datetime of the last reset, or a very old date if no reset has occurred or app_type is invalid.
    """
    if not app_type:
        logger.error("get_last_reset_time called without app_type.")
        return datetime.datetime.fromtimestamp(0)
        
    current_app_type = app_type
    reset_file = get_state_file_path(current_app_type, "last_reset")
    
    try:
        if os.path.exists(reset_file):
            with open(reset_file, "r") as f:
                reset_time_str = f.read().strip()
                return datetime.datetime.fromisoformat(reset_time_str)
    except Exception as e:
        logger.error(f"Error reading last reset time for {current_app_type}: {e}")
    
    return datetime.datetime.fromtimestamp(0)

def set_last_reset_time(reset_time: datetime.datetime, app_type: str = None) -> None:
    """
    Set the last time the state was reset for a specific app type.
    
    Args:
        reset_time: The datetime to set
        app_type: The type of app to set last reset time for.
    """
    if not app_type:
        logger.error("set_last_reset_time called without app_type.")
        return
        
    current_app_type = app_type
    reset_file = get_state_file_path(current_app_type, "last_reset")
    
    try:
        with open(reset_file, "w") as f:
            f.write(reset_time.isoformat())
    except Exception as e:
        logger.error(f"Error writing last reset time for {current_app_type}: {e}")

def check_state_reset(app_type: str = None) -> bool:
    """
    Check if the state needs to be reset based on the reset interval.
    If it's time to reset, clears the processed IDs and updates the last reset time.
    
    Args:
        app_type: The type of app to check state reset for.
        
    Returns:
        True if the state was reset, False otherwise.
    """
    if not app_type:
        logger.error("check_state_reset called without app_type.")
        return False
        
    current_app_type = app_type
    
    reset_interval = settings_manager.get_setting(current_app_type, "state_reset_interval_hours", 168)
    
    last_reset = get_last_reset_time(current_app_type)
    now = datetime.datetime.now()
    
    delta = now - last_reset
    hours_passed = delta.total_seconds() / 3600
    
    if hours_passed >= reset_interval:
        logger.info(f"State files for {current_app_type} have not been reset in {hours_passed:.1f} hours (interval: {reset_interval}h). Resetting now.")
        
        clear_processed_ids(current_app_type)
        
        set_last_reset_time(now, current_app_type)
        
        return True
    
    return False

def clear_processed_ids(app_type: str = None) -> None:
    """
    Clear all processed IDs for a specific app type.
    
    Args:
        app_type: The type of app to clear processed IDs for.
    """
    if not app_type:
        logger.error("clear_processed_ids called without app_type.")
        return
        
    current_app_type = app_type
    
    missing_file = get_state_file_path(current_app_type, "processed_missing")
    try:
        if os.path.exists(missing_file):
            with open(missing_file, "w") as f:
                f.write("[]")
            logger.info(f"Cleared processed missing IDs for {current_app_type}")
    except Exception as e:
        logger.error(f"Error clearing processed missing IDs for {current_app_type}: {e}")
    
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
        app_type: The type of app to calculate reset time for.
        
    Returns:
        A string representation of when the next reset will occur.
    """
    if not app_type:
        logger.error("calculate_reset_time called without app_type.")
        return "Next reset: Unknown (app type not provided)"
        
    current_app_type = app_type
    
    reset_interval = settings_manager.get_setting(current_app_type, "state_reset_interval_hours", 168)
    
    last_reset = get_last_reset_time(current_app_type)
    next_reset = last_reset + datetime.timedelta(hours=reset_interval)
    now = datetime.datetime.now()
    
    if next_reset < now:
        return "Next reset: at the start of the next cycle"
    
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

def reset_state_file(app_type: str, state_type: str) -> bool:
    """
    Reset a specific state file for an app type.
    
    Args:
        app_type: The type of app (sonarr, radarr, etc.)
        state_type: The type of state file (processed_missing, processed_upgrades)
        
    Returns:
        True if successful, False otherwise
    """
    if not app_type:
        logger.error("reset_state_file called without app_type.")
        return False
        
    filepath = get_state_file_path(app_type, state_type)
    
    try:
        save_processed_ids(filepath, [])
        logger.info(f"Reset {state_type} state file for {app_type}")
        return True
    except Exception as e:
        logger.error(f"Error resetting {state_type} state file for {app_type}: {e}")
        return False

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
        processed_ids = processed_ids[-max_items:]
        save_processed_ids(filepath, processed_ids)
        logger.debug(f"Truncated {filepath} to {max_items} items")

def init_state_files() -> None:
    """Initialize state files for all app types"""
    app_types = settings_manager.KNOWN_APP_TYPES 
    
    for app_type in app_types:
        missing_file = get_state_file_path(app_type, "processed_missing")
        upgrades_file = get_state_file_path(app_type, "processed_upgrades")
        reset_file = get_state_file_path(app_type, "last_reset")
        
        for filepath in [missing_file, upgrades_file]:
            if not os.path.exists(filepath):
                save_processed_ids(filepath, [])
        
        if not os.path.exists(reset_file):
             set_last_reset_time(datetime.datetime.fromtimestamp(0), app_type)

init_state_files()