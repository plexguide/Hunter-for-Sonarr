#!/usr/bin/env python3
"""
Missing Albums Processing for Lidarr
Handles searching for missing albums in Lidarr
"""

import random
import time
import datetime
import os
import json
from typing import List, Callable, Dict, Optional
from primary.utils.logger import get_logger, debug_log
from primary.config import MONITORED_ONLY
from primary import settings_manager
from primary.state import load_processed_ids, save_processed_id, truncate_processed_list, get_state_file_path

# Get app-specific logger
logger = get_logger("lidarr")

def process_missing_albums(restart_cycle_flag: Callable[[], bool] = lambda: False) -> bool:
    """
    Process albums that are missing from the library.

    Args:
        restart_cycle_flag: Function that returns whether to restart the cycle

    Returns:
        True if any processing was done, False otherwise
    """
    # Reload settings to ensure the latest values are used
    from primary.config import refresh_settings
    refresh_settings("lidarr")

    # Get the current value directly at the start of processing
    HUNT_MISSING_ALBUMS = settings_manager.get_setting("huntarr", "hunt_missing_albums", 1)
    RANDOM_MISSING = settings_manager.get_setting("advanced", "random_missing", True)
    
    # Get app-specific state file
    PROCESSED_MISSING_FILE = get_state_file_path("lidarr", "processed_missing")

    logger.info("=== Checking for Missing Albums ===")

    # Skip if HUNT_MISSING_ALBUMS is set to 0
    if HUNT_MISSING_ALBUMS <= 0:
        logger.info("HUNT_MISSING_ALBUMS is set to 0, skipping missing albums")
        return False

    # Check for restart signal
    if restart_cycle_flag():
        logger.info("🔄 Received restart signal before starting missing albums. Aborting...")
        return False
        
    # Placeholder for API implementation - would check for missing albums here
    logger.info("Lidarr missing albums functionality not yet implemented")
    
    return False  # No processing done in placeholder implementation