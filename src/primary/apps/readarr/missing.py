#!/usr/bin/env python3
"""
Missing Books Processing for Readarr
Handles searching for missing books in Readarr
"""

import time
import random
from typing import List, Dict, Any, Set, Callable
from src.primary.utils.logger import get_logger
from src.primary.state import load_processed_ids, save_processed_ids, get_state_file_path, truncate_processed_list
from src.primary.apps.readarr import api as readarr_api
from src.primary.stats_manager import increment_stat

# Get logger for the app
readarr_logger = get_logger("readarr")

# State file for processed missing books
PROCESSED_MISSING_FILE = get_state_file_path("readarr", "processed_missing")

def process_missing_books(
    app_settings: Dict[str, Any],
    stop_check: Callable[[], bool] # Function to check if stop is requested
) -> bool:
    """
    Process missing books in Readarr based on provided settings.
    
    Args:
        app_settings: Dictionary containing all settings for Readarr
        stop_check: A function that returns True if the process should stop
    
    Returns:
        True if any books were processed, False otherwise.
    """
    readarr_logger.info("Starting missing books processing cycle for Readarr.")
    processed_any = False
    
    # Extract necessary settings
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 90)  # Default timeout
    monitored_only = app_settings.get("monitored_only", True)
    skip_future_releases = app_settings.get("skip_future_releases", True)
    skip_author_refresh = app_settings.get("skip_author_refresh", False)
    random_missing = app_settings.get("random_missing", False)
    hunt_missing_books = app_settings.get("hunt_missing_books", 0)
    command_wait_delay = app_settings.get("command_wait_delay", 5)
    command_wait_attempts = app_settings.get("command_wait_attempts", 12)
    state_reset_interval_hours = app_settings.get("state_reset_interval_hours", 168)  # Add this line to get the stateful reset interval