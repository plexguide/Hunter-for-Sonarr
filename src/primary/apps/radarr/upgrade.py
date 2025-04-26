#!/usr/bin/env python3
"""
Quality Upgrade Processing for Radarr
Handles searching for movies that need quality upgrades in Radarr
"""

import time
import random
from typing import List, Dict, Any, Set, Callable
from src.primary.utils.logger import get_logger
from src.primary.state import load_processed_ids, save_processed_ids, get_state_file_path, truncate_processed_list
from src.primary.apps.radarr import api as radarr_api
from src.primary.stats_manager import increment_stat

# Get logger for the app
radarr_logger = get_logger("radarr")

# State file for processed upgrades
PROCESSED_UPGRADES_FILE = get_state_file_path("radarr", "processed_upgrades")

def process_cutoff_upgrades(
    app_settings: Dict[str, Any],
    stop_check: Callable[[], bool] # Function to check if stop is requested
) -> bool:
    """
    Process quality cutoff upgrades for Radarr based on settings.
    
    Args:
        app_settings: Dictionary containing all settings for Radarr
        stop_check: A function that returns True if the process should stop
        
    Returns:
        True if any movies were processed for upgrades, False otherwise.
    """
    radarr_logger.info("Starting quality cutoff upgrades processing cycle for Radarr.")
    processed_any = False
    
    # Extract necessary settings
    api_url = app_settings.get("api_url")
    api_key = app_settings.get("api_key")
    api_timeout = app_settings.get("api_timeout", 90)  # Default timeout
    monitored_only = app_settings.get("monitored_only", True)
    skip_movie_refresh = app_settings.get("skip_movie_refresh", False)
    random_upgrades = app_settings.get("random_upgrades", False)
    hunt_upgrade_movies = app_settings.get("hunt_upgrade_movies", 0)
    command_wait_delay = app_settings.get("command_wait_delay", 5)
    command_wait_attempts = app_settings.get("command_wait_attempts", 12)
    state_reset_interval_hours = app_settings.get("state_reset_interval_hours", 168)  # Add this line to get the stateful reset interval