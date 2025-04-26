#!/usr/bin/env python3
"""
Quality Upgrade Processing for Whisparr
Handles searching for scenes that need quality upgrades in Whisparr
"""

import time
import random
from typing import List, Dict, Any, Set, Callable
from src.primary.utils.logger import get_logger
from src.primary.state import load_processed_ids, save_processed_ids, get_state_file_path, truncate_processed_list
from src.primary.apps.whisparr import api as whisparr_api
from src.primary.stats_manager import increment_stat

# Get logger for the app
whisparr_logger = get_logger("whisparr")

# State file for processed cutoff upgrades
PROCESSED_UPGRADES_FILE = get_state_file_path("whisparr", "processed_upgrades")

def process_cutoff_upgrades(
    app_settings: Dict[str, Any],
    stop_check: Callable[[], bool] # Function to check if stop is requested
) -> bool:
    """
    Process quality cutoff upgrades for Whisparr based on settings.
    
    Args:
        app_settings: Dictionary containing all settings for Whisparr
        stop_check: A function that returns True if the process should stop
        
    Returns:
        True if any scenes were processed for upgrades, False otherwise.
    """
    whisparr_logger.info("Starting quality cutoff upgrades processing cycle for Whisparr.")
    processed_any = False
    
    # Extract necessary settings
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 90)  # Default timeout
    monitored_only = app_settings.get("monitored_only", True)
    skip_scene_refresh = app_settings.get("skip_scene_refresh", False)
    random_upgrades = app_settings.get("random_upgrades", False)
    hunt_upgrade_scenes = app_settings.get("hunt_upgrade_scenes", 0)
    command_wait_delay = app_settings.get("command_wait_delay", 5)
    command_wait_attempts = app_settings.get("command_wait_attempts", 12)
    state_reset_interval_hours = app_settings.get("state_reset_interval_hours", 168)  # Add this line to get the stateful reset interval